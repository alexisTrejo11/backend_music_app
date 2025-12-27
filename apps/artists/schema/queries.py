import graphene
from graphene_django import DjangoObjectType, DjangoListField
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from django.db.models import Q
from ..models import Artist
from .types import ArtistType


class ArtistQuery(graphene.ObjectType):
    """Artist-related GraphQL queries"""

    # Single artist queries
    artist = graphene.Field(ArtistType, id=graphene.ID(), slug=graphene.String())

    # List queries
    all_artists = DjangoFilterConnectionField(ArtistType)
    search_artists = graphene.relay.ConnectionField(
        graphene.relay.Connection,
        query=graphene.String(required=True),
        limit=graphene.Int(default_value=20),
        offset=graphene.Int(default_value=0),
    )

    # Special queries
    trending_artists = graphene.List(
        ArtistType,
        time_range=graphene.String(default_value="WEEK"),  # DAY, WEEK, MONTH, YEAR
        limit=graphene.Int(default_value=50),
    )

    similar_artists = graphene.List(
        ArtistType,
        artist_id=graphene.ID(required=True),
        limit=graphene.Int(default_value=20),
    )

    def resolve_artist(self, info, id=None, slug=None):
        """Get single artist by ID or slug"""
        if id:
            return Artist.objects.get(id=id)
        elif slug:
            return Artist.objects.get(slug=slug)
        raise GraphQLError("Either 'id' or 'slug' must be provided")

    def resolve_all_artists(self, info, **kwargs):
        """Get all artists with filtering"""
        return Artist.objects.all()

    def resolve_search_artists(self, info, query, limit=20, offset=0, **kwargs):
        """Search artists by name"""
        qs = Artist.objects.filter(Q(name__icontains=query) | Q(bio__icontains=query))

        total_count = qs.count()
        artists = qs[offset : offset + limit]

        # Create connection
        from graphene.relay.connection import Connection

        return Connection.create_connection(
            graphene.relay.Connection.create_connection_type(ArtistType),
            qs,
            total_count=total_count,
        )

    def resolve_trending_artists(self, info, time_range="WEEK", limit=50):
        """Get trending artists based on time range"""
        from django.utils import timezone
        from datetime import timedelta

        # Define time ranges
        time_filters = {
            "DAY": timezone.now() - timedelta(days=1),
            "WEEK": timezone.now() - timedelta(weeks=1),
            "MONTH": timezone.now() - timedelta(days=30),
            "YEAR": timezone.now() - timedelta(days=365),
        }

        if time_range not in time_filters:
            time_range = "WEEK"

        # In a real app, you would calculate trending based on plays, follows, etc.
        # For now, return artists with most monthly listeners
        return Artist.objects.order_by("-monthly_listeners")[:limit]

    def resolve_similar_artists(self, info, artist_id, limit=20):
        """Get artists similar to given artist"""
        try:
            artist = Artist.objects.get(id=artist_id)

            # Get genres of the artist
            artist_genres = artist.genres.values_list("id", flat=True)

            # Find artists with same genres (excluding the original)
            similar = (
                Artist.objects.filter(genres__id__in=artist_genres)
                .exclude(id=artist_id)
                .distinct()
                .order_by("-monthly_listeners")[:limit]
            )

            return similar
        except Artist.DoesNotExist:
            raise GraphQLError(f"Artist with ID {artist_id} not found")
