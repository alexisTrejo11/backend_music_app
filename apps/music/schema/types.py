import graphene
from graphene_django import DjangoObjectType
from ..models import Genre, Album, Song
from apps.interactions.models import LikedSong


class GenreType(DjangoObjectType):
    subgenres = graphene.List(lambda: GenreType)

    class Meta:
        model = Genre
        fields = ("id", "name", "slug", "description", "parent")
        interfaces = (graphene.relay.Node,)

    def resolve_subgenres(self, info):
        """Get child genres"""
        return Genre.objects.filter(parent=self)


class AlbumType(DjangoObjectType):
    song_count = graphene.Int()
    is_saved = graphene.Boolean()

    class Meta:
        model = Album
        fields = (
            "id",
            "title",
            "slug",
            "artist",
            "album_type",
            "release_date",
            "cover_image",
            "description",
            "label",
            "total_duration",
            "total_tracks",
            "play_count",
            "is_explicit",
            "copyright",
            "upc",
            "created_at",
            "updated_at",
        )
        interfaces = (graphene.relay.Node,)

    def resolve_song_count(self, info):
        """Get the number of songs in the album"""
        return self.songs.count()

    def resolve_is_saved(self, info):
        """Check if current user has saved this album"""
        user = info.context.user
        if user.is_authenticated:
            from apps.interactions.models import SavedAlbum

            return SavedAlbum.objects.filter(user=user, album=self).exists()
        return False


class AudioFeaturesType(graphene.ObjectType):
    """Audio features for recommendations"""

    tempo = graphene.Float()
    key = graphene.String()
    energy = graphene.Float()
    danceability = graphene.Float()
    valence = graphene.Float()


class SongType(DjangoObjectType):
    is_liked = graphene.Boolean()
    audio_features = graphene.Field(AudioFeaturesType)
    featured_artists_list = graphene.List(lambda: graphene.String())

    class Meta:
        model = Song
        fields = (
            "id",
            "title",
            "slug",
            "artist",
            "album",
            "featured_artists",
            "audio_file",
            "audio_url",
            "duration",
            "track_number",
            "disc_number",
            "isrc",
            "lyrics",
            "is_explicit",
            "genre",
            "mood",
            "language",
            "play_count",
            "like_count",
            "created_at",
            "updated_at",
        )
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "title": ["exact", "icontains"],
            "genre": ["exact"],
            "is_explicit": ["exact"],
            "mood": ["exact"],
        }

    def resolve_is_liked(self, info):
        """Check if current user has liked this song"""
        user = info.context.user
        if user.is_authenticated:
            return LikedSong.objects.filter(user=user, song=self).exists()
        return False

    def resolve_audio_features(self, info):
        """Get audio features as structured object"""
        return AudioFeaturesType(
            tempo=self.tempo,
            key=self.key,
            energy=self.energy,
            danceability=self.danceability,
            valence=self.valence,
        )

    def resolve_featured_artists_list(self, info):
        """Get list of featured artist names"""
        return [artist.name for artist in self.featured_artists.all()]
