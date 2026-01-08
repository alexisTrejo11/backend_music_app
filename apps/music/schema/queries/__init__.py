from .album_queries import AlbumQuery
from .genre_queries import GenreQuery
from .song_queries import SongQuery


class Query(SongQuery, AlbumQuery, GenreQuery):
    pass
