import graphene
from apps.core.decorators import get_authenticated_user, auth_required
from ..types import LikedSongType
from ...models import LikedSong


class LikesQueries:

    liked_songs = graphene.List(
        LikedSongType,
        limit=graphene.Int(default_value=50),
        offset=graphene.Int(default_value=0),
        description="Get current user's liked songs",
    )

    is_song_liked = graphene.Boolean(
        song_id=graphene.ID(required=True),
        description="Check if a song is liked by the current user",
    )

    @auth_required
    def resolve_liked_songs(self, info, limit=50, offset=0):
        """Get user's liked songs"""
        user = get_authenticated_user(info)

        return (
            LikedSong.objects.filter(user=user)
            .select_related("song__artist", "song__album")
            .order_by("-created_at")[offset : offset + limit]
        )

    def resolve_is_song_liked(self, info, song_id):
        """Check if a song is liked by the user"""
        user = info.context.user
        if not user.is_authenticated:
            return False

        return LikedSong.objects.filter(user=user, song_id=song_id).exists()
