from django.db.models import Q, Count
from django.utils.text import slugify
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from typing import Dict, List, Optional

from .models import Artist, ArtistMember
from apps.music.models import Genre
from apps.interactions.models import FollowedArtist


class ArtistService:
    """Service layer for Artist business logic"""

    @staticmethod
    def create_artist(data: Dict) -> Artist:
        """
        Create a new artist with validation

        Args:
            data: Dictionary with artist data from CreateArtistInput

        Returns:
            Artist: Created artist instance

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        name = data.get("name", "").strip()
        if not name:
            raise ValidationError("Artist name is required")

        # Check for duplicate name
        if Artist.objects.filter(name__iexact=name).exists():
            raise ValidationError(f"Artist with name '{name}' already exists")

        # Create unique slug
        slug = slugify(name)
        original_slug = slug
        counter = 1
        while Artist.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1

        # Extract social links if provided
        social_links = data.get("social_links", {})

        # Create artist
        artist = Artist.objects.create(
            name=name,
            slug=slug,
            bio=data.get("bio", ""),
            country=data.get("country", ""),
            website=social_links.get("website", "") if social_links else "",
            spotify_url=social_links.get("spotify", "") if social_links else "",
            instagram=social_links.get("instagram", "") if social_links else "",
            twitter=social_links.get("twitter", "") if social_links else "",
        )

        # Handle genres
        genres = data.get("genres", [])
        if genres:
            ArtistService._add_genres_to_artist(artist, genres)

        # TODO: Handle image uploads (profile_image, cover_image)
        # This would involve processing base64 or URLs and saving to storage

        return artist

    @staticmethod
    def update_artist(artist_id: str, data: Dict) -> Artist:
        """
        Update an existing artist

        Args:
            artist_id: ID of the artist to update
            data: Dictionary with updated data from UpdateArtistInput

        Returns:
            Artist: Updated artist instance

        Raises:
            Artist.DoesNotExist: If artist not found
            ValidationError: If validation fails
        """
        try:
            artist = Artist.objects.get(id=artist_id)
        except Artist.DoesNotExist:
            raise ValidationError(f"Artist with ID {artist_id} not found")

        # Update basic fields
        updateable_fields = ["bio", "country", "verified"]
        for field in updateable_fields:
            if field in data:
                setattr(artist, field, data[field])

        # Handle name update (requires slug update)
        if "name" in data:
            new_name = data["name"].strip()
            if not new_name:
                raise ValidationError("Artist name cannot be empty")

            # Check if name is being changed to an existing name
            if new_name != artist.name:
                if (
                    Artist.objects.filter(name__iexact=new_name)
                    .exclude(id=artist_id)
                    .exists()
                ):
                    raise ValidationError(
                        f"Artist with name '{new_name}' already exists"
                    )

                artist.name = new_name
                artist.slug = slugify(new_name)

        # Handle social links
        if "social_links" in data:
            social_links = data["social_links"]
            if social_links:
                artist.website = social_links.get("website", artist.website)
                artist.spotify_url = social_links.get("spotify", artist.spotify_url)
                artist.instagram = social_links.get("instagram", artist.instagram)
                artist.twitter = social_links.get("twitter", artist.twitter)

        # Handle genres
        if "genres" in data:
            artist.genres.clear()
            ArtistService._add_genres_to_artist(artist, data["genres"])

        artist.save()
        return artist

    @staticmethod
    def delete_artist(artist_id: str) -> bool:
        """
        Delete an artist (soft delete in production)

        Args:
            artist_id: ID of the artist to delete

        Returns:
            bool: True if deleted successfully

        Raises:
            Artist.DoesNotExist: If artist not found
        """
        try:
            artist = Artist.objects.get(id=artist_id)

            # In production, you might want to do a soft delete instead
            # artist.is_active = False
            # artist.save()

            artist.delete()
            return True

        except Artist.DoesNotExist:
            raise ValidationError(f"Artist with ID {artist_id} not found")

    @staticmethod
    def follow_artist(user, artist_id: str) -> Dict:
        """
        Follow an artist

        Args:
            user: User instance
            artist_id: ID of the artist to follow

        Returns:
            Dict with success, message, and artist
        """
        try:
            artist = Artist.objects.get(id=artist_id)
        except Artist.DoesNotExist:
            raise ValidationError(f"Artist with ID {artist_id} not found")

        # Check if already following
        follow, created = FollowedArtist.objects.get_or_create(user=user, artist=artist)

        if not created:
            return {
                "success": False,
                "message": "You are already following this artist",
                "artist": artist,
            }

        # Update monthly listeners count
        artist.monthly_listeners = FollowedArtist.objects.filter(artist=artist).count()
        artist.save(update_fields=["monthly_listeners"])

        return {
            "success": True,
            "message": "Successfully followed artist",
            "artist": artist,
        }

    @staticmethod
    def unfollow_artist(user, artist_id: str) -> Dict:
        """
        Unfollow an artist

        Args:
            user: User instance
            artist_id: ID of the artist to unfollow

        Returns:
            Dict with success and message
        """
        try:
            artist = Artist.objects.get(id=artist_id)
        except Artist.DoesNotExist:
            raise ValidationError(f"Artist with ID {artist_id} not found")

        # Try to delete the follow relationship
        deleted, _ = FollowedArtist.objects.filter(user=user, artist=artist).delete()

        if deleted == 0:
            return {"success": False, "message": "You are not following this artist"}

        # Update monthly listeners count
        artist.monthly_listeners = FollowedArtist.objects.filter(artist=artist).count()
        artist.save(update_fields=["monthly_listeners"])

        return {"success": True, "message": "Successfully unfollowed artist"}

    @staticmethod
    def get_trending_artists(time_range: str = "WEEK", limit: int = 50) -> List[Artist]:
        """
        Get trending artists based on recent activity

        Args:
            time_range: One of DAY, WEEK, MONTH, YEAR
            limit: Maximum number of artists to return

        Returns:
            List of Artist instances
        """
        # Define time ranges
        time_filters = {
            "DAY": timezone.now() - timedelta(days=1),
            "WEEK": timezone.now() - timedelta(weeks=1),
            "MONTH": timezone.now() - timedelta(days=30),
            "YEAR": timezone.now() - timedelta(days=365),
        }

        time_filter = time_filters.get(time_range, time_filters["WEEK"])

        # In a real implementation, you would calculate trending based on:
        # - Recent plays from ListeningHistory
        # - Recent follows
        # - Growth rate
        # For now, return artists with most monthly listeners and recent activity

        return list(
            Artist.objects.annotate(
                recent_followers=Count(
                    "followers", filter=Q(followers__created_at__gte=time_filter)
                )
            ).order_by("-recent_followers", "-monthly_listeners")[:limit]
        )

    @staticmethod
    def get_similar_artists(artist_id: str, limit: int = 20) -> List[Artist]:
        """
        Get artists similar to the given artist based on genres

        Args:
            artist_id: ID of the reference artist
            limit: Maximum number of similar artists to return

        Returns:
            List of Artist instances
        """
        try:
            artist = Artist.objects.get(id=artist_id)
        except Artist.DoesNotExist:
            raise ValidationError(f"Artist with ID {artist_id} not found")

        # Get genres of the reference artist
        artist_genres = artist.genres.values_list("id", flat=True)

        if not artist_genres:
            # If no genres, return popular artists
            return Artist.objects.exclude(id=artist_id).order_by("-monthly_listeners")[
                :limit
            ]

        # Find artists with matching genres
        similar = (
            Artist.objects.filter(genres__id__in=artist_genres)
            .exclude(id=artist_id)
            .annotate(
                matching_genres=Count("genres", filter=Q(genres__id__in=artist_genres))
            )
            .order_by("-matching_genres", "-monthly_listeners")
            .distinct()[:limit]
        )

        return similar

    @staticmethod
    def add_member(data: Dict) -> ArtistMember:
        """
        Add a member to an artist/band

        Args:
            data: Dictionary with member data from AddArtistMemberInput

        Returns:
            ArtistMember: Created member instance
        """
        artist_id = data.get("artist_id")
        name = data.get("name", "").strip()
        role = data.get("role", "").strip()

        if not name:
            raise ValidationError("Member name is required")
        if not role:
            raise ValidationError("Member role is required")

        try:
            artist = Artist.objects.get(id=artist_id)
        except Artist.DoesNotExist:
            raise ValidationError(f"Artist with ID {artist_id} not found")

        # Check for duplicate member
        if ArtistMember.objects.filter(artist=artist, name__iexact=name).exists():
            raise ValidationError(f"Member '{name}' already exists for this artist")

        member = ArtistMember.objects.create(
            artist=artist, name=name, role=role, join_date=data.get("join_date")
        )

        # TODO: Handle image upload

        return member

    @staticmethod
    def remove_member(member_id: str) -> bool:
        """
        Remove a member from an artist/band

        Args:
            member_id: ID of the member to remove

        Returns:
            bool: True if removed successfully
        """
        try:
            member = ArtistMember.objects.get(id=member_id)
            member.delete()
            return True
        except ArtistMember.DoesNotExist:
            raise ValidationError(f"Member with ID {member_id} not found")

    @staticmethod
    def _add_genres_to_artist(artist: Artist, genre_names: List[str]):
        """
        Helper method to add genres to an artist

        Args:
            artist: Artist instance
            genre_names: List of genre names
        """
        for genre_name in genre_names:
            genre_name = genre_name.strip()
            if genre_name:
                genre, _ = Genre.objects.get_or_create(
                    name=genre_name, defaults={"slug": slugify(genre_name)}
                )
                artist.genres.add(genre)

    @staticmethod
    def get_artist_statistics(artist_id: str) -> Dict:
        """
        Get comprehensive statistics for an artist

        Args:
            artist_id: ID of the artist

        Returns:
            Dictionary with various statistics
        """
        try:
            artist = Artist.objects.get(id=artist_id)
        except Artist.DoesNotExist:
            raise ValidationError(f"Artist with ID {artist_id} not found")

        from apps.music.models import Song, Album
        from apps.interactions.models import ListeningHistory

        # Calculate statistics
        total_albums = Album.objects.filter(artist=artist).count()
        total_songs = Song.objects.filter(artist=artist).count()
        total_plays = (
            Song.objects.filter(artist=artist).aggregate(total=Count("plays"))["total"]
            or 0
        )

        followers_count = FollowedArtist.objects.filter(artist=artist).count()

        # Get top songs
        top_songs = Song.objects.filter(artist=artist).order_by("-play_count")[:10]

        return {
            "total_albums": total_albums,
            "total_songs": total_songs,
            "total_plays": total_plays,
            "followers_count": followers_count,
            "monthly_listeners": artist.monthly_listeners,
            "top_songs": top_songs,
            "verified": artist.verified,
        }
