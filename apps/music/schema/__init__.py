from .queries.song_queries import SongQuery
from .mutations import SongMutation, AlbumMutation


class Query(SongQuery):
    pass


class Mutation(SongMutation, AlbumMutation):
    pass
