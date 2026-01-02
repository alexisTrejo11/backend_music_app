import graphene
from graphql import GraphQLError
from django.core.exceptions import PermissionDenied
from ..models import Album, Song
from .types import SongType, AlbumType
from ..services import SongService, AlbumService
from .inputs import (
    CreateSongInput,
    UpdateSongInput,
    CreateAlbumInput,
    UpdateAlbumInput,
)


class CreateSong(graphene.Mutation):
    """Create a new song (artist/admin only)"""

    class Arguments:
        input = CreateSongInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    song = graphene.Field(SongType)

    @classmethod
    def mutate(cls, root, info, input):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        if not (user.is_staff or user.is_superuser):
            raise PermissionDenied("You don't have permission to create songs")

        try:
            song = SongService.create_song(input)
            return CreateSong(
                success=True, message="Song created successfully", song=song
            )
        except Exception as e:
            return CreateSong(success=False, message=str(e), song=None)


class UpdateSong(graphene.Mutation):
    """Update an existing song"""

    class Arguments:
        id = graphene.ID(required=True)
        input = UpdateSongInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    song = graphene.Field(SongType)

    @classmethod
    def mutate(cls, root, info, id, input):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        if not (user.is_staff or user.is_superuser):
            raise PermissionDenied("You don't have permission to update songs")

        try:
            song = SongService.update_song(id, input)
            return UpdateSong(
                success=True, message="Song updated successfully", song=song
            )
        except Exception as e:
            return UpdateSong(success=False, message=str(e), song=None)


class DeleteSong(graphene.Mutation):
    """Delete a song (admin only)"""

    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, id):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        if not user.is_superuser:
            raise PermissionDenied("Only superusers can delete songs")

        try:
            SongService.delete_song(id)
            return DeleteSong(success=True, message="Song deleted successfully")
        except Exception as e:
            return DeleteSong(success=False, message=str(e))


class LikeSong(graphene.Mutation):
    """Like a song"""

    class Arguments:
        song_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    song = graphene.Field(SongType)

    @classmethod
    def mutate(cls, root, info, song_id):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in to like songs")

        try:
            result = SongService.like_song(user, song_id)
            return LikeSong(
                success=result["success"],
                message=result["message"],
                song=result["song"],
            )
        except Exception as e:
            raise GraphQLError(str(e))


class UnlikeSong(graphene.Mutation):
    """Unlike a song"""

    class Arguments:
        song_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, song_id):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in to unlike songs")

        try:
            result = SongService.unlike_song(user, song_id)
            return UnlikeSong(success=result["success"], message=result["message"])
        except Exception as e:
            raise GraphQLError(str(e))


class PlaySong(graphene.Mutation):
    """Track song play for listening history"""

    class Arguments:
        song_id = graphene.ID(required=True)
        source = graphene.String()  # playlist, album, radio, search
        source_id = graphene.String()

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, song_id, source=None, source_id=None):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in")

        try:
            SongService.track_play(user, song_id, source, source_id)
            return PlaySong(success=True, message="Play tracked successfully")
        except Exception as e:
            return PlaySong(success=False, message=str(e))


class CreateAlbum(graphene.Mutation):
    """Create a new album"""

    class Arguments:
        input = CreateAlbumInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    album = graphene.Field(AlbumType)

    @classmethod
    def mutate(cls, root, info, input):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        if not (user.is_staff or user.is_superuser):
            raise PermissionDenied("You don't have permission to create albums")

        try:
            album = AlbumService.create_album(input)
            return CreateAlbum(
                success=True, message="Album created successfully", album=album
            )
        except Exception as e:
            return CreateAlbum(success=False, message=str(e), album=None)


class UpdateAlbum(graphene.Mutation):
    """Update an existing album"""

    class Arguments:
        id = graphene.ID(required=True)
        input = UpdateAlbumInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    album = graphene.Field(AlbumType)

    @classmethod
    def mutate(cls, root, info, id, input):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        if not (user.is_staff or user.is_superuser):
            raise PermissionDenied("You don't have permission to update albums")

        try:
            album = AlbumService.update_album(id, input)
            return UpdateAlbum(
                success=True, message="Album updated successfully", album=album
            )
        except Exception as e:
            return UpdateAlbum(success=False, message=str(e), album=None)


class SongMutation(graphene.ObjectType):
    """Song-related GraphQL mutations"""

    create_song = CreateSong.Field()
    update_song = UpdateSong.Field()
    delete_song = DeleteSong.Field()
    like_song = LikeSong.Field()
    unlike_song = UnlikeSong.Field()
    play_song = PlaySong.Field()
    create_album = CreateAlbum.Field()
    update_album = UpdateAlbum.Field()
