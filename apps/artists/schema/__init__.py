from .types import ArtistType, ArtistMemberType, SocialLinksType
from .queries import ArtistQueryMixin
from .mutations import ArtistMutationMixin
from .inputs import *

__all__ = [
    "ArtistType",
    "ArtistMemberType",
    "SocialLinksType",
    # "ArtistInput",
    # "ArtistUpdateInput",
]


class Query(ArtistQueryMixin, graphene.ObjectType):
    pass


class Mutation(ArtistMutationMixin, graphene.ObjectType):
    pass
