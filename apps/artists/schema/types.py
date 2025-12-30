import graphene
from graphene_django import DjangoObjectType
from apps.music.models import Album, Song, Genre
from apps.interactions.models import FollowedArtist
from ..models import ArtistMember, Artist


class ArtistMemberType(DjangoObjectType):
    class Meta:
        model = ArtistMember
        fields = ("id", "name", "role", "image", "join_date", "leave_date")
        interfaces = (graphene.relay.Node,)


class GenreType(DjangoObjectType):
    class Meta:
        model = Genre
        fields = ("id", "name", "slug", "description")
        interfaces = (graphene.relay.Node,)


class AlbumType(DjangoObjectType):
    class Meta:
        model = Album
        fields = ("id", "title", "release_date", "cover_image", "album_type")
        interfaces = (graphene.relay.Node,)


class SongType(DjangoObjectType):
    class Meta:
        model = Song
        fields = ("id", "title", "duration", "play_count", "audio_file")
        interfaces = (graphene.relay.Node,)


class SocialLinksType(graphene.ObjectType):
    website = graphene.String()
    spotify = graphene.String()
    instagram = graphene.String()
    twitter = graphene.String()


class ArtistType(DjangoObjectType):
    """Type for Artist model with additional computed fields"""

    # Computed fields
    followers_count = graphene.Int()
    is_following = graphene.Boolean()
    albums_count = graphene.Int()
    songs_count = graphene.Int()

    # Relationships
    members = graphene.List(ArtistMemberType)
    albums = graphene.List(AlbumType)
    top_songs = graphene.List(SongType, limit=graphene.Int())
    genres = graphene.List(GenreType)
    social_links = graphene.Field(SocialLinksType)

    class Meta:
        model = Artist
        fields = (
            "id",
            "name",
            "slug",
            "bio",
            "profile_image",
            "cover_image",
            "verified",
            "monthly_listeners",
            "country",
            "created_at",
            "updated_at",
        )
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "name": ["exact", "icontains", "istartswith"],
            "verified": ["exact"],
            "country": ["exact"],
            "monthly_listeners": ["gt", "gte", "lt", "lte"],
        }

    def resolve_followers_count(self, info):
        """Get total followers count"""
        return FollowedArtist.objects.filter(artist=self).count()

    def resolve_is_following(self, info):
        """Check if current user is following this artist"""
        user = info.context.user
        if user.is_authenticated:
            return FollowedArtist.objects.filter(user=user, artist=self).exists()
        return False

    def resolve_albums_count(self, info):
        """Get total albums count"""
        return self.albums.count()

    def resolve_songs_count(self, info):
        """Get total songs count"""
        return self.songs.count()

    def resolve_members(self, info):
        """Get artist members"""
        return self.members.all()

    def resolve_albums(self, info):
        """Get artist albums"""
        return self.albums.order_by("-release_date")

    def resolve_top_songs(self, info, limit=10):
        """Get top songs by play count"""
        return self.songs.order_by("-play_count")[:limit]

    def resolve_genres(self, info):
        """Get artist genres"""
        return self.genres.all()

    def resolve_social_links(self, info):
        """Get social links as structured object"""
        return SocialLinksType(
            website=self.website,
            spotify=self.spotify_url,
            instagram=self.instagram,
            twitter=self.twitter,
        )
