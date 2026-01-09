import graphene
from apps.core.decorators import get_authenticated_user, auth_required
from ..types import FollowedArtistType
from ...models import FollowedArtist


class FollowQueries:
    followed_artists = graphene.List(
        FollowedArtistType, description="Get current user's followed artists"
    )

    is_artist_followed = graphene.Boolean(
        artist_id=graphene.ID(required=True),
        description="Check if user is following a specific artist",
    )

    @auth_required
    def resolve_followed_artists(self, info):
        """Get user's followed artists"""
        user = get_authenticated_user(info)

        return (
            FollowedArtist.objects.filter(user=user)
            .select_related("artist")
            .order_by("-created_at")
        )

    def resolve_is_artist_followed(self, info, artist_id):
        """Check if user is following a specific artist"""
        user = info.context.user
        if not user.is_authenticated:
            return False

        return FollowedArtist.objects.filter(user=user, artist_id=artist_id).exists()
