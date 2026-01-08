from django.db.models import Q, F
from django.utils.text import slugify
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from typing import Dict, List, Optional

from .models import Playlist, PlaylistSong, PlaylistFollower
from apps.music.models import Song
from django.contrib.auth import get_user_model

User = get_user_model()


class PlaylistService:
    """Service layer for Playlist business logic"""

    @staticmethod
    def create_playlist(user, data: Dict) -> Playlist:
        """
        Create a new playlist

        Args:
            user: User instance creating the playlist
            data: Dictionary with playlist data from CreatePlaylistInput

        Returns:
            Playlist: Created playlist instance
        """
        name = data.get("name", "").strip()

        # Validate name
        if not name:
            raise ValidationError("Playlist name is required")

        if len(name) > 255:
            raise ValidationError("Playlist name must be 255 characters or less")

        # Create unique slug
        slug = slugify(name)
        original_slug = slug
        counter = 1
        while Playlist.objects.filter(user=user, slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1

        # Create playlist
        playlist = Playlist.objects.create(
            name=name,
            slug=slug,
            user=user,
            description=data.get("description", ""),
            is_public=data.get("is_public", True),
            is_collaborative=data.get("is_collaborative", False),
        )

        # TODO: Handle cover_image upload

        return playlist

    @staticmethod
    def update_playlist(user, playlist_id: str, data: Dict) -> Playlist:
        """
        Update an existing playlist

        Args:
            user: User instance updating the playlist
            playlist_id: ID of the playlist to update
            data: Dictionary with updated data from UpdatePlaylistInput

        Returns:
            Playlist: Updated playlist instance
        """
        try:
            playlist = Playlist.objects.get(id=playlist_id)
        except Playlist.DoesNotExist:
            raise ValidationError(f"Playlist with ID {playlist_id} not found")

        # Check permissions
        if playlist.user_id != user.id:
            raise PermissionDenied("You don't have permission to update this playlist")

        # Update name and slug if provided
        if "name" in data:
            new_name = data["name"].strip()
            if not new_name:
                raise ValidationError("Playlist name cannot be empty")

            if len(new_name) > 255:
                raise ValidationError("Playlist name must be 255 characters or less")

            playlist.name = new_name
            playlist.slug = slugify(new_name)

        # Update other fields
        updateable_fields = ["description", "is_public", "is_collaborative"]
        for field in updateable_fields:
            if field in data:
                setattr(playlist, field, data[field])

        # TODO: Handle cover_image update

        playlist.save()
        return playlist

    @staticmethod
    def delete_playlist(user, playlist_id: str) -> bool:
        """
        Delete a playlist

        Args:
            user: User instance deleting the playlist
            playlist_id: ID of the playlist to delete

        Returns:
            bool: True if deleted successfully
        """
        try:
            playlist = Playlist.objects.get(id=playlist_id)
        except Playlist.DoesNotExist:
            raise ValidationError(f"Playlist with ID {playlist_id} not found")

        # Check permissions
        if playlist.user_id != user.id:
            raise PermissionDenied("You don't have permission to delete this playlist")

        # Don't allow deletion of editorial playlists
        if playlist.is_editorial:
            raise PermissionDenied("Editorial playlists cannot be deleted")

        playlist.delete()
        return True

    @staticmethod
    def add_song_to_playlist(
        user, playlist_id: str, song_id: str, position: Optional[int] = None
    ):
        """
        Add a song to a playlist

        Args:
            user: User instance adding the song
            playlist_id: ID of the playlist
            song_id: ID of the song to add
            position: Optional position for the song (1-indexed)

        Returns:
            PlaylistSong: Created playlist song instance
        """
        # Get playlist
        try:
            playlist = Playlist.objects.get(id=playlist_id)
        except Playlist.DoesNotExist:
            raise ValidationError(f"Playlist with ID {playlist_id} not found")

        # Check permissions
        if not PlaylistService._can_edit_playlist(user, playlist):
            raise PermissionDenied("You don't have permission to edit this playlist")

        # Get song
        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            raise ValidationError(f"Song with ID {song_id} not found")

        # Check if song is already in playlist
        if PlaylistSong.objects.filter(playlist=playlist, song=song).exists():
            raise ValidationError("Song is already in this playlist")

        with transaction.atomic():
            # If no position provided, append to end
            if position is None:
                max_position = PlaylistSong.objects.filter(playlist=playlist).count()
                position = max_position + 1
            else:
                # Shift existing songs down to make room
                PlaylistSong.objects.filter(
                    playlist=playlist, position__gte=position
                ).update(position=F("position") + 1)

            # Create playlist song entry
            playlist_song = PlaylistSong.objects.create(
                playlist=playlist, song=song, added_by=user, position=position
            )

            # Update playlist stats
            PlaylistService._update_playlist_stats(playlist)

        return playlist_song

    @staticmethod
    def remove_song_from_playlist(user, playlist_id: str, song_id: str) -> bool:
        """
        Remove a song from a playlist

        Args:
            user: User instance removing the song
            playlist_id: ID of the playlist
            song_id: ID of the song to remove

        Returns:
            bool: True if removed successfully
        """
        # Get playlist
        try:
            playlist = Playlist.objects.get(id=playlist_id)
        except Playlist.DoesNotExist:
            raise ValidationError(f"Playlist with ID {playlist_id} not found")

        # Check permissions
        if not PlaylistService._can_edit_playlist(user, playlist):
            raise PermissionDenied("You don't have permission to edit this playlist")

        # Get playlist song entry
        try:
            playlist_song = PlaylistSong.objects.get(playlist=playlist, song_id=song_id)
        except PlaylistSong.DoesNotExist:
            raise ValidationError("Song is not in this playlist")

        with transaction.atomic():
            removed_position = playlist_song.position
            playlist_song.delete()

            # Shift remaining songs up
            PlaylistSong.objects.filter(
                playlist=playlist, position__gt=removed_position
            ).update(position=F("position") - 1)

            # Update playlist stats
            PlaylistService._update_playlist_stats(playlist)

        return True

    @staticmethod
    def reorder_songs(user, playlist_id: str, song_id: str, new_position: int) -> bool:
        """
        Reorder songs in a playlist

        Args:
            user: User instance reordering songs
            playlist_id: ID of the playlist
            song_id: ID of the song to move
            new_position: New position for the song (1-indexed)

        Returns:
            bool: True if reordered successfully
        """
        # Get playlist
        try:
            playlist = Playlist.objects.get(id=playlist_id)
        except Playlist.DoesNotExist:
            raise ValidationError(f"Playlist with ID {playlist_id} not found")

        # Check permissions
        if not PlaylistService._can_edit_playlist(user, playlist):
            raise PermissionDenied("You don't have permission to edit this playlist")

        # Get playlist song entry
        try:
            playlist_song = PlaylistSong.objects.get(playlist=playlist, song_id=song_id)
        except PlaylistSong.DoesNotExist:
            raise ValidationError("Song is not in this playlist")

        old_position = playlist_song.position

        # Validate new position
        max_position = PlaylistSong.objects.filter(playlist=playlist).count()
        if new_position < 1 or new_position > max_position:
            raise ValidationError(f"Position must be between 1 and {max_position}")

        if old_position == new_position:
            return True  # No change needed

        with transaction.atomic():
            if new_position < old_position:
                # Moving up - shift songs down
                PlaylistSong.objects.filter(
                    playlist=playlist,
                    position__gte=new_position,
                    position__lt=old_position,
                ).update(position=F("position") + 1)
            else:
                # Moving down - shift songs up
                PlaylistSong.objects.filter(
                    playlist=playlist,
                    position__gt=old_position,
                    position__lte=new_position,
                ).update(position=F("position") - 1)

            # Update the moved song
            playlist_song.position = new_position
            playlist_song.save()

        return True

    @staticmethod
    def follow_playlist(user, playlist_id: str) -> Dict:
        """
        Follow a playlist

        Args:
            user: User instance following the playlist
            playlist_id: ID of the playlist to follow

        Returns:
            Dict with success, message, and playlist
        """
        try:
            playlist = Playlist.objects.get(id=playlist_id)
        except Playlist.DoesNotExist:
            raise ValidationError(f"Playlist with ID {playlist_id} not found")

        # Can't follow private playlists
        if not playlist.is_public:
            raise PermissionDenied("Cannot follow private playlists")

        # Can't follow your own playlist
        if playlist.user_id == user.id:
            return {
                "success": False,
                "message": "You can't follow your own playlist",
                "playlist": playlist,
            }

        # Check if already following
        follow, created = PlaylistFollower.objects.get_or_create(
            user=user, playlist=playlist
        )

        if not created:
            return {
                "success": False,
                "message": "You are already following this playlist",
                "playlist": playlist,
            }

        # Update follower count
        playlist.follower_count = PlaylistFollower.objects.filter(
            playlist=playlist
        ).count()
        playlist.save(update_fields=["follower_count"])

        return {
            "success": True,
            "message": "Successfully followed playlist",
            "playlist": playlist,
        }

    @staticmethod
    def unfollow_playlist(user, playlist_id: str) -> Dict:
        """
        Unfollow a playlist

        Args:
            user: User instance unfollowing the playlist
            playlist_id: ID of the playlist to unfollow

        Returns:
            Dict with success and message
        """
        try:
            playlist = Playlist.objects.get(id=playlist_id)
        except Playlist.DoesNotExist:
            raise ValidationError(f"Playlist with ID {playlist_id} not found")

        # Try to delete the follow relationship
        deleted, _ = PlaylistFollower.objects.filter(
            user=user, playlist=playlist
        ).delete()

        if deleted == 0:
            return {"success": False, "message": "You are not following this playlist"}

        # Update follower count
        playlist.follower_count = PlaylistFollower.objects.filter(
            playlist=playlist
        ).count()
        playlist.save(update_fields=["follower_count"])

        return {"success": True, "message": "Successfully unfollowed playlist"}

    @staticmethod
    def duplicate_playlist(
        user, playlist_id: str, new_name: Optional[str] = None
    ) -> Playlist:
        """
        Duplicate a playlist to current user's library

        Args:
            user: User instance duplicating the playlist
            playlist_id: ID of the playlist to duplicate
            new_name: Optional new name for the duplicated playlist

        Returns:
            Playlist: Newly created playlist
        """
        # Get original playlist
        try:
            original = Playlist.objects.get(id=playlist_id)
        except Playlist.DoesNotExist:
            raise ValidationError(f"Playlist with ID {playlist_id} not found")

        # Check if playlist is accessible
        if not original.is_public and original.user_id != user.id:
            raise PermissionDenied("Cannot duplicate private playlists")

        # Determine new playlist name
        if new_name:
            name = new_name.strip()
        else:
            name = f"{original.name} (Copy)"

        # Create new playlist
        with transaction.atomic():
            new_playlist = PlaylistService.create_playlist(
                user,
                {
                    "name": name,
                    "description": original.description,
                    "is_public": True,
                    "is_collaborative": False,
                },
            )

            # Copy all songs
            original_songs = PlaylistSong.objects.filter(playlist=original).order_by(
                "position"
            )

            for ps in original_songs:
                PlaylistSong.objects.create(
                    playlist=new_playlist,
                    song=ps.song,
                    added_by=user,
                    position=ps.position,
                )

            # Update stats
            PlaylistService._update_playlist_stats(new_playlist)

        return new_playlist

    @staticmethod
    def add_collaborator(user, playlist_id: str, collaborator_id: str) -> bool:
        """
        Add a collaborator to a playlist

        Args:
            user: User instance (playlist owner)
            playlist_id: ID of the playlist
            collaborator_id: ID of the user to add as collaborator

        Returns:
            bool: True if added successfully
        """
        # Get playlist
        try:
            playlist = Playlist.objects.get(id=playlist_id)
        except Playlist.DoesNotExist:
            raise ValidationError(f"Playlist with ID {playlist_id} not found")

        # Only owner can add collaborators
        if playlist.user_id != user.id:
            raise PermissionDenied("Only the playlist owner can add collaborators")

        # Playlist must be collaborative
        if not playlist.is_collaborative:
            raise ValidationError("Playlist must be set as collaborative")

        # Get collaborator user
        try:
            collaborator = User.objects.get(id=collaborator_id)
        except User.DoesNotExist:
            raise ValidationError(f"User with ID {collaborator_id} not found")

        # Can't add owner as collaborator
        if collaborator.id == user.id:
            raise ValidationError("Owner is already a collaborator")

        # Add as follower (collaborators must follow)
        PlaylistFollower.objects.get_or_create(user=collaborator, playlist=playlist)

        return True

    @staticmethod
    def remove_collaborator(user, playlist_id: str, collaborator_id: str) -> bool:
        """
        Remove a collaborator from a playlist

        Args:
            user: User instance (playlist owner)
            playlist_id: ID of the playlist
            collaborator_id: ID of the user to remove

        Returns:
            bool: True if removed successfully
        """
        # Get playlist
        try:
            playlist = Playlist.objects.get(id=playlist_id)
        except Playlist.DoesNotExist:
            raise ValidationError(f"Playlist with ID {playlist_id} not found")

        # Only owner can remove collaborators
        if playlist.user_id != user.id:
            raise PermissionDenied("Only the playlist owner can remove collaborators")

        # Remove follower relationship
        deleted, _ = PlaylistFollower.objects.filter(
            user_id=collaborator_id, playlist=playlist
        ).delete()

        if deleted == 0:
            raise ValidationError("User is not a collaborator")

        return True

    @staticmethod
    def search_playlists(
        query: str, limit: int = 20, offset: int = 0
    ) -> List[Playlist]:
        """
        Search public playlists

        Args:
            query: Search query
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of Playlist instances
        """
        return (
            Playlist.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query),
                is_public=True,
            )
            .select_related("user")
            .order_by("-follower_count")[offset : offset + limit]
        )

    @staticmethod
    def _can_edit_playlist(user, playlist: Playlist) -> bool:
        """
        Check if user can edit a playlist

        Args:
            user: User instance
            playlist: Playlist instance

        Returns:
            bool: True if user can edit
        """
        # Owner can always edit
        if playlist.user_id == user.id:
            return True

        # Collaborative playlist followers can edit
        if playlist.is_collaborative:
            return PlaylistFollower.objects.filter(
                user=user, playlist=playlist
            ).exists()

        return False

    @staticmethod
    def _update_playlist_stats(playlist: Playlist):
        """
        Update playlist statistics

        Args:
            playlist: Playlist instance
        """
        songs = PlaylistSong.objects.filter(playlist=playlist).select_related("song")

        total_duration = sum(ps.song.duration for ps in songs)

        playlist.total_duration = total_duration
        playlist.save(update_fields=["total_duration"])

    @staticmethod
    def get_playlist_stats(playlist: Playlist) -> Dict:
        """
        Get comprehensive statistics for a playlist

        Args:
            playlist: Playlist instance

        Returns:
            Dictionary with various statistics
        """
        songs_count = PlaylistSong.objects.filter(playlist=playlist).count()

        # Get unique artists
        playlist_songs = PlaylistSong.objects.filter(playlist=playlist).select_related(
            "song__artist"
        )
        unique_artists = set(ps.song.artist_id for ps in playlist_songs)

        return {
            "songs_count": songs_count,
            "total_duration": playlist.total_duration,
            "follower_count": playlist.follower_count,
            "unique_artists_count": len(unique_artists),
            "is_public": playlist.is_public,
            "is_collaborative": playlist.is_collaborative,
            "is_editorial": playlist.is_editorial,
        }
