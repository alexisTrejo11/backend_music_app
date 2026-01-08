from typing import Dict
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from apps.artists.models import Artist
from ..models import Album


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
