# apps/interactions/services.py
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from datetime import timedelta
from typing import Dict, List

from ..models import ListeningHistory, LikedSong, FollowedArtist, SavedAlbum, Review
from apps.music.models import Song, Album
from apps.artists.models import Artist


class InteractionService:
    """Service layer for user interactions"""

    @staticmethod
    def track_play(
        user,
        song_id: str,
        duration_played: int,
        completed: bool = False,
        source: str = None,
        source_id: str = None,
    ):
        """
        Track a song play in listening history

        Args:
            user: User instance
            song_id: ID of the song played
            duration_played: How many seconds were played
            completed: Whether the song was completed (>30 seconds usually)
            source: Where the play came from (playlist, album, radio, etc.)
            source_id: ID of the source
        """
        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            raise ValidationError(f"Song with ID {song_id} not found")

        # Validate duration
        if duration_played < 0 or duration_played > song.duration + 10:
            raise ValidationError("Invalid duration played")

        # Create listening history entry
        ListeningHistory.objects.create(
            user=user,
            song=song,
            duration_played=duration_played,
            completed=completed,
            source=source or "",
            source_id=source_id or "",
        )

        # Update song play count if completed
        if completed:
            song.play_count = F("play_count") + 1
            song.save(update_fields=["play_count"])

    @staticmethod
    def save_album(user, album_id: str) -> Dict:
        """
        Save an album to user's library

        Args:
            user: User instance
            album_id: ID of the album to save

        Returns:
            Dict with success, message, and album
        """
        try:
            album = Album.objects.get(id=album_id)
        except Album.DoesNotExist:
            raise ValidationError(f"Album with ID {album_id} not found")

        # Check if already saved
        saved, created = SavedAlbum.objects.get_or_create(user=user, album=album)

        if not created:
            return {
                "success": False,
                "message": "Album is already in your library",
                "album": album,
            }

        return {"success": True, "message": "Album saved successfully", "album": album}

    @staticmethod
    def unsave_album(user, album_id: str) -> Dict:
        """
        Remove an album from user's library

        Args:
            user: User instance
            album_id: ID of the album to unsave

        Returns:
            Dict with success and message
        """
        try:
            album = Album.objects.get(id=album_id)
        except Album.DoesNotExist:
            raise ValidationError(f"Album with ID {album_id} not found")

        # Try to delete the saved album
        deleted, _ = SavedAlbum.objects.filter(user=user, album=album).delete()

        if deleted == 0:
            return {"success": False, "message": "Album is not in your library"}

        return {"success": True, "message": "Album removed from library"}

    @staticmethod
    @staticmethod
    def add_review(user, data: Dict) -> Review:
        """
        Add a review for an album or song

        Args:
            user: User instance
            data: Dictionary with review data

        Returns:
            Review: Created review instance
        """
        album_id = data.get("album_id")
        song_id = data.get("song_id")
        rating = data.get("rating")
        comment = data.get("comment", "").strip()

        # Must review either album or song, not both
        if not album_id and not song_id:
            raise ValidationError("Must specify either album_id or song_id")

        if album_id and song_id:
            raise ValidationError("Cannot review both album and song")

        # Validate rating
        if not rating or rating < 1 or rating > 5:
            raise ValidationError("Rating must be between 1 and 5")

        # Get the entity being reviewed
        album = None
        song = None

        if album_id:
            try:
                album = Album.objects.get(id=album_id)
            except Album.DoesNotExist:
                raise ValidationError(f"Album with ID {album_id} not found")

            # Check if user already reviewed this album
            if Review.objects.filter(user=user, album=album).exists():
                raise ValidationError("You have already reviewed this album")

        if song_id:
            try:
                song = Song.objects.get(id=song_id)
            except Song.DoesNotExist:
                raise ValidationError(f"Song with ID {song_id} not found")

            # Check if user already reviewed this song
            if Review.objects.filter(user=user, song=song).exists():
                raise ValidationError("You have already reviewed this song")

        # Create review
        review = Review.objects.create(
            user=user, album=album, song=song, rating=rating, comment=comment
        )

        return review

    @staticmethod
    def update_review(user, review_id: str, data: Dict) -> Review:
        """
        Update an existing review

        Args:
            user: User instance
            review_id: ID of the review to update
            data: Dictionary with updated data

        Returns:
            Review: Updated review instance
        """
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            raise ValidationError(f"Review with ID {review_id} not found")

        # Check permissions
        if review.user_id != user.id:
            raise PermissionDenied("You don't have permission to update this review")

        # Update rating
        if "rating" in data:
            rating = data["rating"]
            if rating < 1 or rating > 5:
                raise ValidationError("Rating must be between 1 and 5")
            review.rating = rating

        # Update comment
        if "comment" in data:
            review.comment = data["comment"].strip()

        review.save()
        return review

    @staticmethod
    def delete_review(user, review_id: str) -> bool:
        """
        Delete a review

        Args:
            user: User instance
            review_id: ID of the review to delete

        Returns:
            bool: True if deleted successfully
        """
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            raise ValidationError(f"Review with ID {review_id} not found")

        # Check permissions
        if review.user_id != user.id:
            raise PermissionDenied("You don't have permission to delete this review")

        review.delete()
        return True

    @staticmethod
    def mark_review_helpful(user, review_id: str) -> bool:
        """
        Mark a review as helpful

        Args:
            user: User instance
            review_id: ID of the review

        Returns:
            bool: True if marked successfully
        """
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            raise ValidationError(f"Review with ID {review_id} not found")

        # Can't mark your own review as helpful
        if review.user_id == user.id:
            raise ValidationError("You cannot mark your own review as helpful")

        # Increment helpful count
        review.helpful_count = F("helpful_count") + 1
        review.save(update_fields=["helpful_count"])

        # In production, you'd want to track who marked it helpful
        # to prevent multiple marks from same user

        return True

    @staticmethod
    def clear_listening_history(user) -> bool:
        """
        Clear user's listening history

        Args:
            user: User instance

        Returns:
            bool: True if cleared successfully
        """
        deleted_count, _ = ListeningHistory.objects.filter(user=user).delete()
        return deleted_count > 0


class AnalyticsService:
    """Service layer for analytics and statistics"""

    @staticmethod
    def get_listening_stats(user, time_range: str = "MONTH") -> Dict:
        """
        Get comprehensive listening statistics

        Args:
            user: User instance
            time_range: One of WEEK, MONTH, YEAR, ALL_TIME

        Returns:
            Dictionary with comprehensive stats
        """
        # Get time filter
        time_filter = AnalyticsService._get_time_filter(time_range)

        # Build query
        qs = ListeningHistory.objects.filter(user=user)
        if time_filter:
            qs = qs.filter(played_at__gte=time_filter)

        # Calculate basic stats
        stats = qs.aggregate(
            total_listening_time=Sum("duration_played"), total_plays=Count("id")
        )

        # Get unique counts
        unique_songs = qs.values("song").distinct().count()
        unique_artists = qs.values("song__artist").distinct().count()

        # Get top items
        top_artists = AnalyticsService.get_top_artists(user, time_range, limit=5)
        top_songs = AnalyticsService.get_top_songs(user, time_range, limit=10)
        top_genres = AnalyticsService.get_top_genres(user, time_range)

        return {
            "total_listening_time": stats["total_listening_time"] or 0,
            "total_plays": stats["total_plays"] or 0,
            "unique_songs": unique_songs,
            "unique_artists": unique_artists,
            "top_artists": top_artists,
            "top_songs": top_songs,
            "top_genres": top_genres,
        }

    @staticmethod
    def get_top_artists(user, time_range: str = "MONTH", limit: int = 10) -> List[Dict]:
        """
        Get user's top artists

        Args:
            user: User instance
            time_range: Time range filter
            limit: Maximum number of results

        Returns:
            List of dictionaries with artist and stats
        """
        time_filter = AnalyticsService._get_time_filter(time_range)

        qs = ListeningHistory.objects.filter(user=user)
        if time_filter:
            qs = qs.filter(played_at__gte=time_filter)

        # Group by artist and aggregate
        top_artists = (
            qs.values("song__artist")
            .annotate(play_count=Count("id"), listening_time=Sum("duration_played"))
            .order_by("-play_count")[:limit]
        )

        # Build result with artist objects
        result = []
        for item in top_artists:
            try:
                artist = Artist.objects.get(id=item["song__artist"])
                result.append(
                    {
                        "artist": artist,
                        "play_count": item["play_count"],
                        "listening_time": item["listening_time"] or 0,
                    }
                )
            except Artist.DoesNotExist:
                continue

        return result

    @staticmethod
    def get_top_songs(user, time_range: str = "MONTH", limit: int = 50) -> List[Dict]:
        """
        Get user's top songs

        Args:
            user: User instance
            time_range: Time range filter
            limit: Maximum number of results

        Returns:
            List of dictionaries with song and stats
        """
        time_filter = AnalyticsService._get_time_filter(time_range)

        qs = ListeningHistory.objects.filter(user=user)
        if time_filter:
            qs = qs.filter(played_at__gte=time_filter)

        # Group by song and aggregate
        top_songs = (
            qs.values("song")
            .annotate(play_count=Count("id"), last_played=F("played_at"))
            .order_by("-play_count")[:limit]
        )

        # Build result with song objects
        result = []
        for item in top_songs:
            try:
                song = Song.objects.select_related("artist", "album").get(
                    id=item["song"]
                )

                # Get the actual last played time for this song
                last_play = qs.filter(song=song).order_by("-played_at").first()

                result.append(
                    {
                        "song": song,
                        "play_count": item["play_count"],
                        "last_played": last_play.played_at if last_play else None,
                    }
                )
            except Song.DoesNotExist:
                continue

        return result

    @staticmethod
    def get_top_genres(user, time_range: str = "MONTH") -> List[Dict]:
        """
        Get user's top genres

        Args:
            user: User instance
            time_range: Time range filter

        Returns:
            List of dictionaries with genre and stats
        """
        time_filter = AnalyticsService._get_time_filter(time_range)

        qs = ListeningHistory.objects.filter(user=user)
        if time_filter:
            qs = qs.filter(played_at__gte=time_filter)

        # Get total plays for percentage calculation
        total_plays = qs.count()

        if total_plays == 0:
            return []

        # Group by genre and aggregate
        top_genres = (
            qs.filter(song__genre__isnull=False)
            .values("song__genre")
            .annotate(play_count=Count("id"))
            .order_by("-play_count")[:10]
        )

        # Build result with genre objects
        result = []
        from apps.music.models import Genre

        for item in top_genres:
            try:
                genre = Genre.objects.get(id=item["song__genre"])
                play_count = item["play_count"]
                percentage = (play_count / total_plays) * 100

                result.append(
                    {
                        "genre": genre,
                        "play_count": play_count,
                        "percentage": round(percentage, 2),
                    }
                )
            except Genre.DoesNotExist:
                continue

        return result

    @staticmethod
    def _get_time_filter(time_range: str):
        """
        Get datetime filter for time range

        Args:
            time_range: One of WEEK, MONTH, YEAR, ALL_TIME

        Returns:
            Datetime object or None for ALL_TIME
        """
        time_filters = {
            "WEEK": timezone.now() - timedelta(weeks=1),
            "MONTH": timezone.now() - timedelta(days=30),
            "YEAR": timezone.now() - timedelta(days=365),
            "ALL_TIME": None,
        }

        return time_filters.get(time_range, time_filters["MONTH"])

    @staticmethod
    def get_user_recommendations_data(user) -> Dict:
        """
        Get data for building recommendations

        Args:
            user: User instance

        Returns:
            Dictionary with user's music taste data
        """
        # Get recent listening history (last 100 plays)
        recent_plays = ListeningHistory.objects.filter(user=user).order_by(
            "-played_at"
        )[:100]

        # Extract favorite genres
        favorite_genres = set()
        for play in recent_plays:
            if play.song.genre:
                favorite_genres.add(play.song.genre_id)

        # Get followed artists
        followed_artists = FollowedArtist.objects.filter(user=user).values_list(
            "artist_id", flat=True
        )

        # Get liked songs for audio features analysis
        liked_songs = LikedSong.objects.filter(user=user).select_related("song")[:50]

        # Calculate average audio features
        total_energy = 0
        total_danceability = 0
        total_valence = 0
        count = 0

        for like in liked_songs:
            if like.song.energy is not None:
                total_energy += like.song.energy
                count += 1
            if like.song.danceability is not None:
                total_danceability += like.song.danceability
            if like.song.valence is not None:
                total_valence += like.song.valence

        avg_energy = total_energy / count if count > 0 else 0.5
        avg_danceability = total_danceability / count if count > 0 else 0.5
        avg_valence = total_valence / count if count > 0 else 0.5

        return {
            "favorite_genres": list(favorite_genres),
            "followed_artists": list(followed_artists),
            "audio_preferences": {
                "energy": avg_energy,
                "danceability": avg_danceability,
                "valence": avg_valence,
            },
        }
