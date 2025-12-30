import graphene
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from apps.interactions.models import FollowedArtist
from ..models import Artist
from ..services import ArtistService
from .types import ArtistType


class ArtistQueryMixin:
    """Mixin with artist-related query resolvers"""

    artist = graphene.Field(
        ArtistType,
        id=graphene.ID(),
        slug=graphene.String(),
    )

    all_artists = DjangoFilterConnectionField(
        ArtistType,
        description="Get all artists with optional filtering",
    )

    search_artists = graphene.List(
        ArtistType,
        query=graphene.String(required=True),
        limit=graphene.Int(default_value=20),
        offset=graphene.Int(default_value=0),
        description="Search artists by name or bio",
    )

    trending_artists = graphene.List(
        ArtistType,
        time_range=graphene.String(default_value="WEEK"),
        limit=graphene.Int(default_value=10),
        description="Get trending artists. time_range: DAY, WEEK, MONTH, YEAR",
    )

    similar_artists = graphene.List(
        ArtistType,
        artist_id=graphene.ID(required=True),
        limit=graphene.Int(default_value=10),
        description="Get artists similar to the given artist based on genres",
    )

    followed_artists = graphene.List(
        ArtistType,
        description="Get all artists followed by the current user",
    )

    def resolve_artist(self, info, id=None, slug=None):
        """Get single artist by ID or slug"""
        if id:
            try:
                return Artist.objects.get(id=id)
            except Artist.DoesNotExist:
                raise GraphQLError(f"Artist with ID {id} not found")
        elif slug:
            try:
                return Artist.objects.get(slug=slug)
            except Artist.DoesNotExist:
                raise GraphQLError(f"Artist with slug '{slug}' not found")
        raise GraphQLError("Either 'id' or 'slug' must be provided")

    def resolve_all_artists(self, info, **kwargs):
        """Get all artists with filtering"""
        return Artist.objects.all()

    def resolve_trending_artists(self, info, time_range="WEEK", limit=50):
        """Get trending artists based on time range"""
        return ArtistService.get_trending_artists(time_range, limit)

    def resolve_similar_artists(self, info, artist_id, limit=10):
        """Get artists similar to given artist"""
        return ArtistService.get_similar_artists(artist_id, limit)

    def resolve_search_artists(self, info, query, limit=20, offset=0, **kwargs):
        """Search artists by name or bio"""
        qs = Artist.objects.filter(
            Q(name__icontains=query) | Q(bio__icontains=query)
        ).distinct()

        return qs[offset : offset + limit]

    def resolve_followed_artists(self, info):
        """Get all artists followed by current user"""
        user = info.context.user
        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in to view followed artists")

        followed = FollowedArtist.objects.filter(user=user).select_related("artist")
        return [fa.artist for fa in followed]
