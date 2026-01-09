import graphene
from graphene_django import DjangoObjectType

from ..models import ListeningHistory, LikedSong, FollowedArtist, SavedAlbum, Review


class ListeningHistoryType(DjangoObjectType):
    """Type for listening history entries"""

    class Meta:
        model = ListeningHistory
        fields = (
            "id",
            "user",
            "song",
            "played_at",
            "duration_played",
            "completed",
            "source",
            "source_id",
        )
        interfaces = (graphene.relay.Node,)


class LikedSongType(DjangoObjectType):
    """Type for liked songs"""

    class Meta:
        model = LikedSong
        fields = ("id", "user", "song", "created_at")
        interfaces = (graphene.relay.Node,)


class FollowedArtistType(DjangoObjectType):
    """Type for followed artists"""

    class Meta:
        model = FollowedArtist
        fields = ("id", "user", "artist", "created_at")
        interfaces = (graphene.relay.Node,)


class SavedAlbumType(DjangoObjectType):
    """Type for saved albums"""

    class Meta:
        model = SavedAlbum
        fields = ("id", "user", "album", "created_at")
        interfaces = (graphene.relay.Node,)


class ReviewType(DjangoObjectType):
    """Type for reviews"""

    can_edit = graphene.Boolean()

    class Meta:
        model = Review
        fields = (
            "id",
            "user",
            "album",
            "song",
            "rating",
            "comment",
            "helpful_count",
            "created_at",
            "updated_at",
        )
        interfaces = (graphene.relay.Node,)

    def resolve_can_edit(self, info):
        """Check if current user can edit this review"""
        user = info.context.user
        if user.is_authenticated:
            return self.user_id == user.id
        return False


class TopArtistType(graphene.ObjectType):
    """Type for top artist statistics"""

    artist = graphene.Field("apps.artists.schema.ArtistType")
    play_count = graphene.Int()
    listening_time = graphene.Int()  # in seconds


class TopSongType(graphene.ObjectType):
    """Type for top song statistics"""

    song = graphene.Field("apps.music.schema.SongType")
    play_count = graphene.Int()
    last_played = graphene.DateTime()


class TopGenreType(graphene.ObjectType):
    """Type for top genre statistics"""

    genre = graphene.Field("apps.music.schema.GenreType")
    play_count = graphene.Int()
    percentage = graphene.Float()


class ListeningStatsType(graphene.ObjectType):
    """Type for comprehensive listening statistics"""

    total_listening_time = graphene.Int()  # in seconds
    total_plays = graphene.Int()
    unique_songs = graphene.Int()
    unique_artists = graphene.Int()
    top_artists = graphene.List(TopArtistType)
    top_songs = graphene.List(TopSongType)
    top_genres = graphene.List(TopGenreType)
