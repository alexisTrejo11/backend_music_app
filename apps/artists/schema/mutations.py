import graphene
from django.core.exceptions import PermissionDenied
from .inputs import CreateArtistInput
from .types import ArtistType
from ..services import ArtistService


class CreateArtist(graphene.Mutation):
    """Create a new artist (admin/verified users only)"""

    class Arguments:
        input = CreateArtistInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    artist = graphene.Field(ArtistType)

    @classmethod
    def mutate(cls, root, info, input):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        if not (user.is_staff or user.is_superuser):
            raise PermissionDenied("You don't have permission to create artists")

        try:
            artist = ArtistService.create_artist(input)
            return CreateArtist(
                success=True, message="Artist created successfully", artist=artist
            )
        except Exception as e:
            return CreateArtist(success=False, message=str(e), artist=None)
