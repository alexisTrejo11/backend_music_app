from typing import Dict, List
from django.core.exceptions import ValidationError
from slugify import slugify
from apps.artists.models import Artist
from apps.music.models import Album, Genre, Song
from apps.interactions.models import LikedSong, ListeningHistory
from django.db.models import Q, Count, F
from django.utils import timezone
from datetime import timedelta


class SongService:
    """Service layer for Song business logic"""

    @staticmethod
    def create_song(data: Dict):
        """
        Create a new song with validation

        Args:
            data: Dictionary with song data from CreateSongInput

        Returns:
            Song: Created song instance
        """
        title = data.get("title", "").strip()
        artist_id = data.get("artist_id")
        album_id = data.get("album_id")
        duration = data.get("duration")

        if not title:
            raise ValidationError("Song title is required")
        if not duration or duration <= 0:
            raise ValidationError("Valid duration is required")

        try:
            artist = Artist.objects.get(id=artist_id)
        except Artist.DoesNotExist:
            raise ValidationError(f"Artist with ID {artist_id} not found")

        try:
            album = Album.objects.get(id=album_id)
        except Album.DoesNotExist:
            raise ValidationError(f"Album with ID {album_id} not found")

        if album.artist_id != artist_id:
            raise ValidationError("Artist must match album's artist")

        # Create unique slug
        slug = slugify(title)
        original_slug = slug
        counter = 1
        while Song.objects.filter(album=album, slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1

        # Get genre if provided
        genre = None
        genre_id = data.get("genre_id")
        if genre_id:
            try:
                genre = Genre.objects.get(id=genre_id)
            except Genre.DoesNotExist:
                raise ValidationError(f"Genre with ID {genre_id} not found")

        # Create song
        song = Song.objects.create(
            title=title,
            slug=slug,
            artist=artist,
            album=album,
            duration=duration,
            track_number=data.get("track_number", 1),
            disc_number=data.get("disc_number", 1),
            isrc=data.get("isrc", ""),
            lyrics=data.get("lyrics", ""),
            is_explicit=data.get("is_explicit", False),
            genre=genre,
            mood=data.get("mood", ""),
            language=data.get("language", ""),
        )

        # Add featured artists
        featured_artist_ids = data.get("featured_artist_ids", [])
        if featured_artist_ids:
            featured_artists = Artist.objects.filter(id__in=featured_artist_ids)
            song.featured_artists.set(featured_artists)

        # TODO: Handle audio_file upload and processing
        # Update album stats
        # AlbumService.update_album_stats(album)
        # - Extract metadata (duration, bitrate, etc.)
        # - Generate audio features (tempo, key, energy, etc.)
        # - Upload to S3

        return song

    @staticmethod
    def delete_song(song_id: str) -> bool:
        """
        Delete a song

        Args:
            song_id: ID of the song to delete

        Returns:
            bool: True if deleted successfully
        """
        try:
            song = Song.objects.get(id=song_id)
            album = song.album
            song.delete()

            # Update album stats after deletion
            # AlbumService.update_album_stats(album)

            return True
        except Song.DoesNotExist:
            raise ValidationError(f"Song with ID {song_id} not found")

    @staticmethod
    def like_song(user, song_id: str) -> Dict:
        """
        Like a song

        Args:
            user: User instance
            song_id: ID of the song to like

        Returns:
            Dict with success, message, and song
        """
        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            raise ValidationError(f"Song with ID {song_id} not found")

        # Check if already liked
        like, created = LikedSong.objects.get_or_create(user=user, song=song)

        if not created:
            return {
                "success": False,
                "message": "You already liked this song",
                "song": song,
            }

        # Update like count
        song.like_count = LikedSong.objects.filter(song=song).count()
        song.save(update_fields=["like_count"])

        return {"success": True, "message": "Song liked successfully", "song": song}

    @staticmethod
    def unlike_song(user, song_id: str) -> Dict:
        """
        Unlike a song

        Args:
            user: User instance
            song_id: ID of the song to unlike

        Returns:
            Dict with success and message
        """
        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            raise ValidationError(f"Song with ID {song_id} not found")

        # Try to delete the like
        deleted, _ = LikedSong.objects.filter(user=user, song=song).delete()

        if deleted == 0:
            return {"success": False, "message": "You have not liked this song"}

        # Update like count
        song.like_count = LikedSong.objects.filter(song=song).count()
        song.save(update_fields=["like_count"])

        return {"success": True, "message": "Song unliked successfully"}

    @staticmethod
    def track_play(user, song_id: str, source=None, source_id=None):
        """
        Track a song play in listening history

        Args:
            user: User instance
            song_id: ID of the song played
            source: Source of play (playlist, album, radio, search)
            source_id: ID of the source
        """
        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            raise ValidationError(f"Song with ID {song_id} not found")

        # Create listening history entry
        ListeningHistory.objects.create(
            user=user,
            song=song,
            duration_played=song.duration,  # Assume full play for now
            completed=True,
            source=source or "",
            source_id=source_id or "",
        )

        # Update play count (TODO: this asynchronously in production with Celery)
        song.play_count = F("play_count") + 1
        song.save(update_fields=["play_count"])

        # Refresh to get actual value
        song.refresh_from_db()

    @staticmethod
    def search_songs(
        query: str, genre=None, is_explicit=None, limit: int = 20, offset: int = 0
    ):
        """
        Search songs with filters

        Args:
            query: Search query
            genre: Genre filter (slug)
            is_explicit: Filter by explicit content
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of Song instances
        """
        qs = Song.objects.select_related("artist", "album", "genre").filter(
            Q(title__icontains=query)
            | Q(artist__name__icontains=query)
            | Q(album__title__icontains=query)
            | Q(lyrics__icontains=query)
        )

        # Apply filters
        if genre:
            qs = qs.filter(genre__slug=genre)

        if is_explicit is not None:
            qs = qs.filter(is_explicit=is_explicit)

        return qs.distinct()[offset : offset + limit]

    @staticmethod
    def get_trending_songs(time_range: str = "WEEK", limit: int = 50):
        """
        Get trending songs based on recent plays

        Args:
            time_range: One of DAY, WEEK, MONTH, YEAR
            limit: Maximum number of songs

        Returns:
            List of Song instances
        """
        time_filters = {
            "DAY": timezone.now() - timedelta(days=1),
            "WEEK": timezone.now() - timedelta(weeks=1),
            "MONTH": timezone.now() - timedelta(days=30),
            "YEAR": timezone.now() - timedelta(days=365),
        }

        time_filter = time_filters.get(time_range, time_filters["WEEK"])

        # Get songs with most recent plays
        trending = Song.objects.annotate(
            recent_plays=Count("plays", filter=Q(plays__played_at__gte=time_filter))
        ).order_by("-recent_plays", "-play_count")[:limit]

        return trending

    @staticmethod
    def get_recommended_songs(user, limit: int = 30):
        """
        Get personalized song recommendations

        Args:
            user: User instance
            limit: Maximum number of recommendations

        Returns:
            List of Song instances
        """
        # Simple recommendation based on:
        # 1. User's liked songs genres
        # 2. Artists user follows
        # 3. Similar songs to what they've listened to

        # Get user's favorite genres from liked songs
        liked_songs = LikedSong.objects.filter(user=user).select_related("song__genre")
        favorite_genres = set()
        for like in liked_songs[:50]:  # Last 50 likes
            if like.song.genre:
                favorite_genres.add(like.song.genre_id)

        # Get followed artists
        from apps.interactions.models import FollowedArtist

        followed_artists = FollowedArtist.objects.filter(user=user).values_list(
            "artist_id", flat=True
        )

        # Build recommendation query
        recommendations = (
            Song.objects.exclude(id__in=liked_songs.values_list("song_id", flat=True))
            .filter(Q(genre_id__in=favorite_genres) | Q(artist_id__in=followed_artists))
            .distinct()
            .order_by("-play_count", "?")[:limit]
        )

        return recommendations


class AlbumService:
    """Service layer for Album business logic"""

    @staticmethod
    def create_album(data: Dict) -> Album:
        """
        Create a new album with validation

        Args:
            data: Dictionary with album data from CreateAlbumInput

        Returns:
            Album: Created album instance
        """
        title = data.get("title", "").strip()
        artist_id = data.get("artist_id")
        album_type = data.get("album_type")
        release_date = data.get("release_date")

        # Validate required fields
        if not title:
            raise ValidationError("Album title is required")

        valid_types = ["album", "single", "ep", "compilation"]
        if album_type not in valid_types:
            raise ValidationError(
                f"Invalid album type. Must be one of: {', '.join(valid_types)}"
            )

        # Get artist
        try:
            artist = Artist.objects.get(id=artist_id)
        except Artist.DoesNotExist:
            raise ValidationError(f"Artist with ID {artist_id} not found")

        # Create unique slug
        slug = slugify(title)
        original_slug = slug
        counter = 1
        while Album.objects.filter(artist=artist, slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1

        # Create album
        album = Album.objects.create(
            title=title,
            slug=slug,
            artist=artist,
            album_type=album_type,
            release_date=release_date,
            description=data.get("description", ""),
            label=data.get("label", ""),
            is_explicit=data.get("is_explicit", False),
            copyright=data.get("copyright", ""),
            upc=data.get("upc", ""),
        )

        # TODO: Handle cover_image upload

        return album

    @staticmethod
    def update_album(album_id: str, data: Dict) -> Album:
        """
        Update an existing album

        Args:
            album_id: ID of the album to update
            data: Dictionary with updated data from UpdateAlbumInput

        Returns:
            Album: Updated album instance
        """
        try:
            album = Album.objects.get(id=album_id)
        except Album.DoesNotExist:
            raise ValidationError(f"Album with ID {album_id} not found")

        # Update basic fields
        updateable_fields = ["description", "label", "is_explicit"]
        for field in updateable_fields:
            if field in data:
                setattr(album, field, data[field])

        # Handle title update
        if "title" in data:
            new_title = data["title"].strip()
            if not new_title:
                raise ValidationError("Album title cannot be empty")
            album.title = new_title
            album.slug = slugify(new_title)

        # TODO: Handle cover_image update

        album.save()
        return album

    @staticmethod
    def update_album_stats(album: Album):
        """
        Update album statistics (total duration, track count)

        Args:
            album: Album instance
        """
        songs = album.songs.all()

        album.total_tracks = songs.count()
        album.total_duration = sum(song.duration for song in songs)
        album.play_count = sum(song.play_count for song in songs)

        album.save(update_fields=["total_tracks", "total_duration", "play_count"])

    @staticmethod
    def search_albums(query: str, limit: int = 20):
        """
        Search albums by title or artist

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of Album instances
        """
        return Album.objects.select_related("artist").filter(
            Q(title__icontains=query) | Q(artist__name__icontains=query)
        )[:limit]

    @staticmethod
    def get_new_releases(album_type=None, limit: int = 20):
        """
        Get new album releases

        Args:
            album_type: Filter by album type (optional)
            limit: Maximum results

        Returns:
            List of Album instances
        """
        qs = Album.objects.select_related("artist").order_by("-release_date")

        if album_type:
            valid_types = ["album", "single", "ep", "compilation"]
            if album_type in valid_types:
                qs = qs.filter(album_type=album_type)

        return qs[:limit]
