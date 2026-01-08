import graphene
from graphql import GraphQLError

from ...models import Genre
from ..types import GenreType


class GenreQuery(graphene.ObjectType):
    """Genre-related GraphQL queries"""

    genre = graphene.Field(
        GenreType,
        id=graphene.ID(),
        slug=graphene.String(),
        description="Get a single genre by ID or slug",
    )

    all_genres = graphene.List(GenreType, description="Get all genres")

    def resolve_genre(self, info, id=None, slug=None):
        """Get single genre by ID or slug"""
        if id:
            try:
                return Genre.objects.get(id=id)
            except Genre.DoesNotExist:
                raise GraphQLError(f"Genre with ID {id} not found")
        elif slug:
            try:
                return Genre.objects.get(slug=slug)
            except Genre.DoesNotExist:
                raise GraphQLError(f"Genre with slug '{slug}' not found")
        raise GraphQLError("Either 'id' or 'slug' must be provided")

    def resolve_all_genres(self, info):
        return Genre.objects.all()
