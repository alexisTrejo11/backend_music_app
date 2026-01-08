import graphene
from graphql import GraphQLError

from apps.music.services import AlbumService
from apps.music.models import Album
from ..types import AlbumType


class AlbumQuery(graphene.ObjectType):
    """Album-related GraphQL queries"""

    album = graphene.Field(
        AlbumType,
        id=graphene.ID(),
        slug=graphene.String(),
        description="Get a single album by ID or slug",
    )

    search_albums = graphene.List(
        AlbumType,
        query=graphene.String(required=True),
        limit=graphene.Int(default_value=20),
        description="Search albums by title",
    )

    new_releases = graphene.List(
        AlbumType,
        album_type=graphene.String(),
        limit=graphene.Int(default_value=20),
        description="Get new album releases",
    )

    def resolve_album(self, info, id=None, slug=None):
        """Get single album by ID or slug"""
        if id:
            try:
                return Album.objects.select_related("artist").get(id=id)
            except Album.DoesNotExist:
                raise GraphQLError(f"Album with ID {id} not found")
        elif slug:
            try:
                return Album.objects.select_related("artist").get(slug=slug)
            except Album.DoesNotExist:
                raise GraphQLError(f"Album with slug '{slug}' not found")
        raise GraphQLError("Either 'id' or 'slug' must be provided")

    def resolve_search_albums(self, info, query, limit=20):
        return AlbumService.search_albums(query, limit)
