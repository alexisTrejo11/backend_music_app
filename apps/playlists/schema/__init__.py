import graphene
from .queries import PlaylistQuery
from .mutations import (
    CreatePlaylist,
    UpdatePlaylist,
    DeletePlaylist,
    AddSongToPlaylist,
    RemoveSongFromPlaylist,
    ReorderPlaylistSongs,
    FollowPlaylist,
    UnfollowPlaylist,
    DuplicatePlaylist,
    AddCollaborator,
    RemoveCollaborator,
)


class Query(PlaylistQuery, graphene.ObjectType):
    """Playlist-related GraphQL queries"""

    pass


class Mutation(graphene.ObjectType):
    """Playlist-related GraphQL mutations"""

    create_playlist = CreatePlaylist.Field()
    update_playlist = UpdatePlaylist.Field()
    delete_playlist = DeletePlaylist.Field()
    add_song_to_playlist = AddSongToPlaylist.Field()
    remove_song_from_playlist = RemoveSongFromPlaylist.Field()
    reorder_playlist_songs = ReorderPlaylistSongs.Field()
    follow_playlist = FollowPlaylist.Field()
    unfollow_playlist = UnfollowPlaylist.Field()
    duplicate_playlist = DuplicatePlaylist.Field()
    add_collaborator = AddCollaborator.Field()
    remove_collaborator = RemoveCollaborator.Field()
