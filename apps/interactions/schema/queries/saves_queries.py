import graphene
from apps.core.decorators import get_authenticated_user, auth_required
from ..types import SavedAlbumType
from ...models import SavedAlbum


class SaveQueries:
    saved_albums = graphene.List(
        SavedAlbumType, description="Get current user's saved albums"
    )

    is_album_saved = graphene.Boolean(
        album_id=graphene.ID(required=True),
        description="Check if user has saved a specific album",
    )

    @auth_required
    def resolve_saved_albums(self, info):
        """Get user's saved albums"""
        user = get_authenticated_user(info)

        return (
            SavedAlbum.objects.filter(user=user)
            .select_related("album__artist")
            .order_by("-created_at")
        )

    def resolve_is_album_saved(self, info, album_id):
        """Check if user has saved a specific album"""
        user = info.context.user
        if not user.is_authenticated:
            return False

        return SavedAlbum.objects.filter(user=user, album_id=album_id).exists()
