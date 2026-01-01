import graphene
from apps.core.base_schema import TypedBaseMutation
from django.core.exceptions import PermissionDenied
from .inputs import CreateArtistInput, UpdateArtistInput, AddArtistMemberInput
from .types import ArtistType
from ..services import ArtistService


class CreateArtist(TypedBaseMutation):
    """Create a new artist (admin/verified users only)"""

    data = graphene.Field(ArtistType)

    class Arguments:
        input = CreateArtistInput(required=True)

    @classmethod
    def mutate(cls, root, info, input):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        if not (user.is_staff or user.is_superuser):
            raise PermissionDenied("You don't have permission to create artists")

        try:
            artist = ArtistService.create_artist(input)
            return cls.success_response(
                data=artist, message="Artist created successfully"
            )
        except Exception as e:
            return cls.error_response(message=str(e))


class UpdateArtist(TypedBaseMutation):
    """Update an existing artist (admin/verified users only)"""

    data = graphene.Field(ArtistType)

    class Arguments:
        input = UpdateArtistInput(required=True)

    @classmethod
    def mutate(cls, root, info, id, input):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        if not (user.is_staff or user.is_superuser):
            raise PermissionDenied("You don't have permission to update artists")

        try:
            artist = ArtistService.update_artist(id, input)
            return cls.success_response(
                data=artist, message="Artist updated successfully"
            )
        except Exception as e:
            return cls.error_response(message=str(e))


class DeleteArtist(TypedBaseMutation):
    """Delete an existing artist (admin/verified users only)"""

    class Arguments:
        id = graphene.ID(required=True)

    @classmethod
    def mutate(cls, root, info, id):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        if not (user.is_staff or user.is_superuser):
            raise PermissionDenied("You don't have permission to delete artists")

        try:
            ArtistService.delete_artist(id)
            return cls.success_response(message="Artist deleted successfully")
        except Exception as e:
            return cls.error_response(message=str(e))


class AddArtistMember(TypedBaseMutation):
    """Add a member to an artist (admin/verified users only)"""

    data = graphene.Field(ArtistType)

    class Arguments:
        input = AddArtistMemberInput(required=True)

    @classmethod
    def mutate(cls, root, info, input):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        if not (user.is_staff or user.is_superuser):
            raise PermissionDenied("You don't have permission to add artist members")

        try:
            artist = ArtistService.add_member(input)
            return cls.success_response(
                data=artist, message="Artist member added successfully"
            )
        except Exception as e:
            return cls.error_response(message=str(e))


class RemoveArtistMember(TypedBaseMutation):
    """Remove a member from an artist (admin/verified users only)"""

    data = graphene.Field(ArtistType)

    class Arguments:
        artist_id = graphene.ID(required=True)
        member_id = graphene.ID(required=True)

    @classmethod
    def mutate(cls, root, info, member_id):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        if not (user.is_staff or user.is_superuser):
            raise PermissionDenied("You don't have permission to remove artist members")

        try:
            artist = ArtistService.remove_member(member_id)
            return cls.success_response(
                data=artist, message="Artist member removed successfully"
            )
        except Exception as e:
            return cls.error_response(message=str(e))


class ArtistMutationMixin:
    """Artist-related GraphQL mutations"""

    # TODO: implement these later
    # follow_artist = FollowArtist.Field()
    # unfollow_artist = UnfollowArtist.Field()
    create_artist = CreateArtist.Field()
    update_artist = UpdateArtist.Field()
    delete_artist = DeleteArtist.Field()
    add_artist_member = AddArtistMember.Field()
    remove_artist_member = RemoveArtistMember.Field()
