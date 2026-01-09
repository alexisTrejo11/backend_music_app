from .queries.song_queries import SongQuery
from .mutations import SongMutation, AlbumMutation
from .types import SongType, AlbumType, GenreType, AudioFeaturesType


class Query(SongQuery):
    pass


class Mutation(SongMutation, AlbumMutation):
    pass


__all__ = [
    "Query",
    "Mutation",
    "SongType",
    "AlbumType",
    "GenreType",
    "AudioFeaturesType",
]
