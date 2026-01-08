import graphene
from graphql import GraphQLError
from django.core.exceptions import PermissionDenied
from .inputs import (
    CreatePlaylistInput,
    UpdatePlaylistInput,
    AddSongToPlaylistInput,
    ReorderPlaylistSongsInput,
)
from .types import PlaylistType, PlaylistSongType
from ..services import PlaylistService


class CreatePlaylist(graphene.Mutation):
    """Create a new playlist"""

    class Arguments:
        input = CreatePlaylistInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    playlist = graphene.Field(PlaylistType)

    @classmethod
    def mutate(cls, root, info, input):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in to create playlists")

        try:
            playlist = PlaylistService.create_playlist(user, input)
            return CreatePlaylist(
                success=True, message="Playlist created successfully", playlist=playlist
            )
        except Exception as e:
            return CreatePlaylist(success=False, message=str(e), playlist=None)


class UpdatePlaylist(graphene.Mutation):
    """Update an existing playlist"""

    class Arguments:
        id = graphene.ID(required=True)
        input = UpdatePlaylistInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    playlist = graphene.Field(PlaylistType)

    @classmethod
    def mutate(cls, root, info, id, input):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in")

        try:
            playlist = PlaylistService.update_playlist(user, id, input)
            return UpdatePlaylist(
                success=True, message="Playlist updated successfully", playlist=playlist
            )
        except Exception as e:
            return UpdatePlaylist(success=False, message=str(e), playlist=None)


class DeletePlaylist(graphene.Mutation):
    """Delete a playlist"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, id):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in")

        try:
            PlaylistService.delete_playlist(user, id)
            return DeletePlaylist(success=True, message="Playlist deleted successfully")
        except Exception as e:
            return DeletePlaylist(success=False, message=str(e))


class AddSongToPlaylist(graphene.Mutation):
    """Add a song to a playlist"""

    class Arguments:
        input = AddSongToPlaylistInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    playlist_song = graphene.Field(PlaylistSongType)

    @classmethod
    def mutate(cls, root, info, input):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in")

        try:
            playlist_song = PlaylistService.add_song_to_playlist(
                user,
                getattr(input, "playlist_id"),
                getattr(input, "song_id"),
                getattr(input, "position", None),
            )
            return AddSongToPlaylist(
                success=True,
                message="Song added to playlist successfully",
                playlist_song=playlist_song,
            )
        except Exception as e:
            return AddSongToPlaylist(success=False, message=str(e), playlist_song=None)


class RemoveSongFromPlaylist(graphene.Mutation):
    """Remove a song from a playlist"""

    class Arguments:
        playlist_id = graphene.ID(required=True)
        song_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, playlist_id, song_id):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in")

        try:
            PlaylistService.remove_song_from_playlist(user, playlist_id, song_id)
            return RemoveSongFromPlaylist(
                success=True, message="Song removed from playlist successfully"
            )
        except Exception as e:
            return RemoveSongFromPlaylist(success=False, message=str(e))


class ReorderPlaylistSongs(graphene.Mutation):
    """Reorder songs in a playlist"""

    class Arguments:
        input = ReorderPlaylistSongsInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, input):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in")

        try:
            PlaylistService.reorder_songs(
                user,
                getattr(input, "playlist_id"),
                getattr(input, "song_id"),
                getattr(input, "new_position"),
            )
            return ReorderPlaylistSongs(
                success=True, message="Playlist songs reordered successfully"
            )
        except Exception as e:
            return ReorderPlaylistSongs(success=False, message=str(e))


class FollowPlaylist(graphene.Mutation):
    """Follow a playlist"""

    class Arguments:
        playlist_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    playlist = graphene.Field(PlaylistType)

    @classmethod
    def mutate(cls, root, info, playlist_id):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in to follow playlists")

        try:
            result = PlaylistService.follow_playlist(user, playlist_id)
            return FollowPlaylist(
                success=result["success"],
                message=result["message"],
                playlist=result["playlist"],
            )
        except Exception as e:
            raise GraphQLError(str(e))


class UnfollowPlaylist(graphene.Mutation):
    """Unfollow a playlist"""

    class Arguments:
        playlist_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, playlist_id):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in to unfollow playlists")

        try:
            result = PlaylistService.unfollow_playlist(user, playlist_id)
            return UnfollowPlaylist(
                success=result["success"], message=result["message"]
            )
        except Exception as e:
            raise GraphQLError(str(e))


class DuplicatePlaylist(graphene.Mutation):
    """Duplicate a playlist to current user's library"""

    class Arguments:
        playlist_id = graphene.ID(required=True)
        new_name = graphene.String()

    success = graphene.Boolean()
    message = graphene.String()
    playlist = graphene.Field(PlaylistType)

    @classmethod
    def mutate(cls, root, info, playlist_id, new_name=None):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in")

        try:
            playlist = PlaylistService.duplicate_playlist(user, playlist_id, new_name)
            return DuplicatePlaylist(
                success=True,
                message="Playlist duplicated successfully",
                playlist=playlist,
            )
        except Exception as e:
            return DuplicatePlaylist(success=False, message=str(e), playlist=None)


class AddCollaborator(graphene.Mutation):
    """Add a collaborator to a playlist"""

    class Arguments:
        playlist_id = graphene.ID(required=True)
        user_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, playlist_id, user_id):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in")

        try:
            PlaylistService.add_collaborator(user, playlist_id, user_id)
            return AddCollaborator(
                success=True, message="Collaborator added successfully"
            )
        except Exception as e:
            return AddCollaborator(success=False, message=str(e))


class RemoveCollaborator(graphene.Mutation):
    """Remove a collaborator from a playlist"""

    class Arguments:
        playlist_id = graphene.ID(required=True)
        user_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, playlist_id, user_id):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in")

        try:
            PlaylistService.remove_collaborator(user, playlist_id, user_id)
            return RemoveCollaborator(
                success=True, message="Collaborator removed successfully"
            )
        except Exception as e:
            return RemoveCollaborator(success=False, message=str(e))
