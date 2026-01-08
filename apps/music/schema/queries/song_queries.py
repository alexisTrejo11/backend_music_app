from django.core.exceptions import PermissionDenied
import graphene
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError

from apps.interactions.models import LikedSong
from ...models import Song
from ...services import SongService
from ..types import SongType


class SongQuery(graphene.ObjectType):
    """Song-related GraphQL queries"""

    song = graphene.Field(
        SongType,
        id=graphene.ID(),
        slug=graphene.String(),
        description="Get a single song by ID or slug",
    )

    all_songs = DjangoFilterConnectionField(
        SongType, description="Get all songs with filtering"
    )

    search_songs = graphene.List(
        SongType,
        query=graphene.String(required=True),
        genre=graphene.String(),
        is_explicit=graphene.Boolean(),
        limit=graphene.Int(default_value=20),
        offset=graphene.Int(default_value=0),
        description="Search songs with filters",
    )

    trending_songs = graphene.List(
        SongType,
        time_range=graphene.String(default_value="WEEK"),
        limit=graphene.Int(default_value=50),
        description="Get trending songs",
    )

    recommended_songs = graphene.List(
        SongType,
        limit=graphene.Int(default_value=30),
        description="Get personalized song recommendations for current user",
    )

    artist_songs = graphene.List(
        SongType,
        artist_id=graphene.ID(required=True),
        limit=graphene.Int(default_value=20),
        description="Get songs by a specific artist",
    )

    album_songs = graphene.List(
        SongType,
        album_id=graphene.ID(required=True),
        description="Get all songs from an album",
    )

    liked_songs = graphene.List(SongType, description="Get current user's liked songs")

    def resolve_song(self, info, id=None, slug=None):
        """Get single song by ID or slug"""
        if id:
            try:
                return Song.objects.select_related("artist", "album", "genre").get(
                    id=id
                )
            except Song.DoesNotExist:
                raise GraphQLError(f"Song with ID {id} not found")
        elif slug:
            try:
                return Song.objects.select_related("artist", "album", "genre").get(
                    slug=slug
                )
            except Song.DoesNotExist:
                raise GraphQLError(f"Song with slug '{slug}' not found")
        raise GraphQLError("Either 'id' or 'slug' must be provided")

    def resolve_all_songs(self, info, **kwargs):
        return Song.objects.select_related("artist", "album", "genre").all()

    def resolve_search_songs(
        self, info, query, genre=None, is_explicit=None, limit=20, offset=0
    ):
        return SongService.search_songs(query, genre, is_explicit, limit, offset)

    def resolve_trending_songs(self, info, time_range="WEEK", limit=50):
        return SongService.get_trending_songs(time_range, limit)

    def resolve_recommended_songs(self, info, limit=30):
        user = info.context.user
        if not user.is_authenticated:
            # Return popular songs for non-authenticated users
            return Song.objects.order_by("-play_count")[:limit]

        return SongService.get_recommended_songs(user, limit)

    def resolve_artist_songs(self, info, artist_id, limit=20):
        try:
            return Song.objects.filter(artist_id=artist_id).order_by("-play_count")[
                :limit
            ]
        except Exception:
            return []

    def resolve_album_songs(self, info, album_id):
        try:
            return Song.objects.filter(album_id=album_id).order_by(
                "disc_number", "track_number"
            )
        except Exception:
            return []

    def resolve_liked_songs(self, info):
        user = info.context.user
        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in")

        liked = LikedSong.objects.filter(user=user).select_related(
            "song__artist", "song__album"
        )
        return [like.song for like in liked]
