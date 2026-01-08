from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene.test import Client

from apps.playlists.models import Playlist, PlaylistFollower, PlaylistSong
from apps.music.models import Song, Album
from apps.artists.models import Artist
from config.schema import schema

User = get_user_model()


class PlaylistMutationsTestCase(TestCase):
    """Test cases for Playlist GraphQL mutations"""

    def setUp(self):
        """Set up test data"""
        self.client = Client(schema)

        # Create users
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )

        # Create test songs
        self.artist = Artist.objects.create(name="Test Artist", slug="test-artist")
        self.album = Album.objects.create(
            title="Test Album",
            slug="test-album",
            artist=self.artist,
            release_date="2024-01-01",
        )
        self.song1 = Song.objects.create(
            title="Song 1",
            slug="song-1",
            artist=self.artist,
            album=self.album,
            duration=210,
        )
        self.song2 = Song.objects.create(
            title="Song 2",
            slug="song-2",
            artist=self.artist,
            album=self.album,
            duration=180,
        )
        self.song3 = Song.objects.create(
            title="Song 3",
            slug="song-3",
            artist=self.artist,
            album=self.album,
            duration=200,
        )

        # Create a test playlist
        self.playlist = Playlist.objects.create(
            name="Test Playlist",
            slug="test-playlist",
            user=self.user1,
            is_public=True,
        )

    def _get_user_context(self, user):
        """Helper to create user context"""

        class MockContext:
            def __init__(self, user):
                self.user = user

        return MockContext(user)

    def _get_anonymous_context(self):
        """Helper to create anonymous context"""

        class MockContext:
            def __init__(self):
                self.user = type("AnonymousUser", (), {"is_authenticated": False})()

        return MockContext()

    # CREATE PLAYLIST TESTS

    def test_create_playlist_success(self):
        """Test creating a new playlist"""
        mutation = """
            mutation CreatePlaylist($input: CreatePlaylistInput!) {
                createPlaylist(input: $input) {
                    success
                    message
                    playlist {
                        id
                        name
                        slug
                        description
                        isPublic
                        isCollaborative
                        user {
                            username
                        }
                    }
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            mutation,
            variables={
                "input": {
                    "name": "My New Playlist",
                    "description": "A great playlist",
                    "isPublic": True,
                    "isCollaborative": False,
                }
            },
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["createPlaylist"]
        self.assertTrue(data["success"])
        self.assertIsNotNone(data["playlist"])
        self.assertEqual(data["playlist"]["name"], "My New Playlist")
        self.assertEqual(data["playlist"]["slug"], "my-new-playlist")
        self.assertEqual(data["playlist"]["user"]["username"], "user1")

    def test_create_playlist_unauthenticated(self):
        """Test creating playlist without authentication fails"""
        mutation = """
            mutation CreatePlaylist($input: CreatePlaylistInput!) {
                createPlaylist(input: $input) {
                    success
                    message
                }
            }
        """

        context = self._get_anonymous_context()
        result = self.client.execute(
            mutation,
            variables={"input": {"name": "Test"}},
            context_value=context,
        )

        self.assertIsNotNone(result.get("errors"))
        self.assertIn("logged in", str(result["errors"]).lower())

    def test_create_playlist_empty_name(self):
        """Test creating playlist with empty name fails"""
        mutation = """
            mutation CreatePlaylist($input: CreatePlaylistInput!) {
                createPlaylist(input: $input) {
                    success
                    message
                    playlist {
                        id
                    }
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            mutation,
            variables={"input": {"name": ""}},
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["createPlaylist"]
        self.assertFalse(data["success"])
        self.assertIn("required", data["message"].lower())
        self.assertIsNone(data["playlist"])

    def test_create_playlist_duplicate_slug(self):
        """Test creating playlist with duplicate name creates unique slug"""
        mutation = """
            mutation CreatePlaylist($input: CreatePlaylistInput!) {
                createPlaylist(input: $input) {
                    success
                    playlist {
                        slug
                    }
                }
            }
        """

        context = self._get_user_context(self.user1)

        # Create first playlist
        result1 = self.client.execute(
            mutation,
            variables={"input": {"name": "Test Playlist"}},
            context_value=context,
        )

        # Create second with same name
        result2 = self.client.execute(
            mutation,
            variables={"input": {"name": "Test Playlist"}},
            context_value=context,
        )

        self.assertIsNone(result1.get("errors"))
        self.assertIsNone(result2.get("errors"))

        slug1 = result1["data"]["createPlaylist"]["playlist"]["slug"]
        slug2 = result2["data"]["createPlaylist"]["playlist"]["slug"]

        self.assertNotEqual(slug1, slug2)

    # UPDATE PLAYLIST TESTS

    def test_update_playlist_success(self):
        """Test updating a playlist"""
        mutation = """
            mutation UpdatePlaylist($id: ID!, $input: UpdatePlaylistInput!) {
                updatePlaylist(id: $id, input: $input) {
                    success
                    message
                    playlist {
                        id
                        name
                        description
                        isPublic
                    }
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            mutation,
            variables={
                "id": str(self.playlist.id),
                "input": {
                    "name": "Updated Playlist",
                    "description": "New description",
                    "isPublic": False,
                },
            },
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["updatePlaylist"]
        self.assertTrue(data["success"])
        self.assertEqual(data["playlist"]["name"], "Updated Playlist")
        self.assertEqual(data["playlist"]["description"], "New description")
        self.assertFalse(data["playlist"]["isPublic"])

    def test_update_playlist_not_owner(self):
        """Test updating playlist by non-owner fails"""
        mutation = """
            mutation UpdatePlaylist($id: ID!, $input: UpdatePlaylistInput!) {
                updatePlaylist(id: $id, input: $input) {
                    success
                    message
                }
            }
        """

        context = self._get_user_context(self.user2)
        result = self.client.execute(
            mutation,
            variables={
                "id": str(self.playlist.id),
                "input": {"name": "Hacked"},
            },
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["updatePlaylist"]
        self.assertFalse(data["success"])
        self.assertIn("permission", data["message"].lower())

    def test_update_playlist_not_found(self):
        """Test updating non-existent playlist"""
        mutation = """
            mutation UpdatePlaylist($id: ID!, $input: UpdatePlaylistInput!) {
                updatePlaylist(id: $id, input: $input) {
                    success
                    message
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            mutation,
            variables={"id": "99999", "input": {"name": "Test"}},
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["updatePlaylist"]
        self.assertFalse(data["success"])
        self.assertIn("not found", data["message"].lower())

    # DELETE PLAYLIST TESTS

    def test_delete_playlist_success(self):
        """Test deleting a playlist"""
        mutation = """
            mutation DeletePlaylist($id: ID!) {
                deletePlaylist(id: $id) {
                    success
                    message
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            mutation,
            variables={"id": str(self.playlist.id)},
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["deletePlaylist"]
        self.assertTrue(data["success"])

        # Verify deletion
        self.assertFalse(Playlist.objects.filter(id=self.playlist.id).exists())

    def test_delete_playlist_not_owner(self):
        """Test deleting playlist by non-owner fails"""
        mutation = """
            mutation DeletePlaylist($id: ID!) {
                deletePlaylist(id: $id) {
                    success
                    message
                }
            }
        """

        context = self._get_user_context(self.user2)
        result = self.client.execute(
            mutation,
            variables={"id": str(self.playlist.id)},
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["deletePlaylist"]
        self.assertFalse(data["success"])
        self.assertIn("permission", data["message"].lower())

    def test_delete_editorial_playlist(self):
        """Test deleting editorial playlist fails"""
        editorial = Playlist.objects.create(
            name="Editorial",
            slug="editorial",
            user=self.user1,
            is_editorial=True,
        )

        mutation = """
            mutation DeletePlaylist($id: ID!) {
                deletePlaylist(id: $id) {
                    success
                    message
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            mutation,
            variables={"id": str(editorial.id)},
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["deletePlaylist"]
        self.assertFalse(data["success"])
        self.assertIn("editorial", data["message"].lower())

    # ADD SONG TO PLAYLIST TESTS

    def test_add_song_to_playlist_success(self):
        """Test adding a song to playlist"""
        mutation = """
            mutation AddSong($input: AddSongToPlaylistInput!) {
                addSongToPlaylist(input: $input) {
                    success
                    message
                    playlistSong {
                        id
                        position
                        song {
                            title
                        }
                    }
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            mutation,
            variables={
                "input": {
                    "playlistId": str(self.playlist.id),
                    "songId": str(self.song1.id),
                    "position": 1,
                }
            },
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["addSongToPlaylist"]
        self.assertTrue(data["success"])
        self.assertIsNotNone(data["playlistSong"])
        self.assertEqual(data["playlistSong"]["song"]["title"], "Song 1")

    def test_add_song_without_position(self):
        """Test adding song without position appends to end"""
        # Add first song
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song1, added_by=self.user1, position=1
        )

        mutation = """
            mutation AddSong($input: AddSongToPlaylistInput!) {
                addSongToPlaylist(input: $input) {
                    success
                    playlistSong {
                        position
                    }
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            mutation,
            variables={
                "input": {
                    "playlistId": str(self.playlist.id),
                    "songId": str(self.song2.id),
                }
            },
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["addSongToPlaylist"]
        self.assertTrue(data["success"])
        self.assertEqual(data["playlistSong"]["position"], 2)

    def test_add_duplicate_song_to_playlist(self):
        """Test adding duplicate song fails"""
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song1, added_by=self.user1, position=1
        )

        mutation = """
            mutation AddSong($input: AddSongToPlaylistInput!) {
                addSongToPlaylist(input: $input) {
                    success
                    message
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            mutation,
            variables={
                "input": {
                    "playlistId": str(self.playlist.id),
                    "songId": str(self.song1.id),
                }
            },
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["addSongToPlaylist"]
        self.assertFalse(data["success"])
        self.assertIn("already", data["message"].lower())

    def test_add_song_to_collaborative_playlist_as_follower(self):
        """Test follower can add song to collaborative playlist"""
        self.playlist.is_collaborative = True
        self.playlist.save()

        # User2 follows the playlist
        PlaylistFollower.objects.create(user=self.user2, playlist=self.playlist)

        mutation = """
            mutation AddSong($input: AddSongToPlaylistInput!) {
                addSongToPlaylist(input: $input) {
                    success
                }
            }
        """

        context = self._get_user_context(self.user2)
        result = self.client.execute(
            mutation,
            variables={
                "input": {
                    "playlistId": str(self.playlist.id),
                    "songId": str(self.song1.id),
                }
            },
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["addSongToPlaylist"]
        self.assertTrue(data["success"])

    # REMOVE SONG FROM PLAYLIST TESTS

    def test_remove_song_from_playlist_success(self):
        """Test removing a song from playlist"""
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song1, added_by=self.user1, position=1
        )

        mutation = """
            mutation RemoveSong($playlistId: ID!, $songId: ID!) {
                removeSongFromPlaylist(playlistId: $playlistId, songId: $songId) {
                    success
                    message
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            mutation,
            variables={
                "playlistId": str(self.playlist.id),
                "songId": str(self.song1.id),
            },
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["removeSongFromPlaylist"]
        self.assertTrue(data["success"])

        # Verify removal
        self.assertFalse(
            PlaylistSong.objects.filter(
                playlist=self.playlist, song=self.song1
            ).exists()
        )

    def test_remove_song_reorders_positions(self):
        """Test removing song reorders remaining songs"""
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song1, added_by=self.user1, position=1
        )
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song2, added_by=self.user1, position=2
        )
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song3, added_by=self.user1, position=3
        )

        mutation = """
            mutation RemoveSong($playlistId: ID!, $songId: ID!) {
                removeSongFromPlaylist(playlistId: $playlistId, songId: $songId) {
                    success
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            mutation,
            variables={
                "playlistId": str(self.playlist.id),
                "songId": str(self.song2.id),
            },
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))

        # Check positions are reordered
        ps1 = PlaylistSong.objects.get(playlist=self.playlist, song=self.song1)
        ps3 = PlaylistSong.objects.get(playlist=self.playlist, song=self.song3)
        self.assertEqual(ps1.position, 1)
        self.assertEqual(ps3.position, 2)

    # REORDER SONGS TESTS

    def test_reorder_songs_success(self):
        """Test reordering songs in playlist"""
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song1, added_by=self.user1, position=1
        )
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song2, added_by=self.user1, position=2
        )
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song3, added_by=self.user1, position=3
        )

        mutation = """
            mutation ReorderSongs($input: ReorderPlaylistSongsInput!) {
                reorderPlaylistSongs(input: $input) {
                    success
                    message
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            mutation,
            variables={
                "input": {
                    "playlistId": str(self.playlist.id),
                    "songId": str(self.song3.id),
                    "newPosition": 1,
                }
            },
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["reorderPlaylistSongs"]
        self.assertTrue(data["success"])

        # Verify new positions
        ps1 = PlaylistSong.objects.get(playlist=self.playlist, song=self.song1)
        ps2 = PlaylistSong.objects.get(playlist=self.playlist, song=self.song2)
        ps3 = PlaylistSong.objects.get(playlist=self.playlist, song=self.song3)
        self.assertEqual(ps3.position, 1)
        self.assertEqual(ps1.position, 2)
        self.assertEqual(ps2.position, 3)

    # FOLLOW/UNFOLLOW TESTS

    def test_follow_playlist_success(self):
        """Test following a playlist"""
        mutation = """
            mutation FollowPlaylist($playlistId: ID!) {
                followPlaylist(playlistId: $playlistId) {
                    success
                    message
                    playlist {
                        id
                    }
                }
            }
        """

        context = self._get_user_context(self.user2)
        result = self.client.execute(
            mutation,
            variables={"playlistId": str(self.playlist.id)},
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["followPlaylist"]
        self.assertTrue(data["success"])

        # Verify follow relationship
        self.assertTrue(
            PlaylistFollower.objects.filter(
                user=self.user2, playlist=self.playlist
            ).exists()
        )

    def test_follow_own_playlist(self):
        """Test following own playlist fails"""
        mutation = """
            mutation FollowPlaylist($playlistId: ID!) {
                followPlaylist(playlistId: $playlistId) {
                    success
                    message
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            mutation,
            variables={"playlistId": str(self.playlist.id)},
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["followPlaylist"]
        self.assertFalse(data["success"])
        self.assertIn("own", data["message"].lower())

    def test_follow_private_playlist(self):
        """Test following private playlist fails"""
        self.playlist.is_public = False
        self.playlist.save()

        mutation = """
            mutation FollowPlaylist($playlistId: ID!) {
                followPlaylist(playlistId: $playlistId) {
                    success
                    message
                }
            }
        """

        context = self._get_user_context(self.user2)
        result = self.client.execute(
            mutation,
            variables={"playlistId": str(self.playlist.id)},
            context_value=context,
        )

        self.assertIsNotNone(result.get("errors"))
        self.assertIn("private", str(result["errors"]).lower())

    def test_unfollow_playlist_success(self):
        """Test unfollowing a playlist"""
        PlaylistFollower.objects.create(user=self.user2, playlist=self.playlist)

        mutation = """
            mutation UnfollowPlaylist($playlistId: ID!) {
                unfollowPlaylist(playlistId: $playlistId) {
                    success
                    message
                }
            }
        """

        context = self._get_user_context(self.user2)
        result = self.client.execute(
            mutation,
            variables={"playlistId": str(self.playlist.id)},
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["unfollowPlaylist"]
        self.assertTrue(data["success"])

        # Verify unfollow
        self.assertFalse(
            PlaylistFollower.objects.filter(
                user=self.user2, playlist=self.playlist
            ).exists()
        )

    def test_unfollow_not_following(self):
        """Test unfollowing playlist not following"""
        mutation = """
            mutation UnfollowPlaylist($playlistId: ID!) {
                unfollowPlaylist(playlistId: $playlistId) {
                    success
                    message
                }
            }
        """

        context = self._get_user_context(self.user2)
        result = self.client.execute(
            mutation,
            variables={"playlistId": str(self.playlist.id)},
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["unfollowPlaylist"]
        self.assertFalse(data["success"])
        self.assertIn("not following", data["message"].lower())

    # DUPLICATE PLAYLIST TESTS

    def test_duplicate_playlist_success(self):
        """Test duplicating a playlist"""
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song1, added_by=self.user1, position=1
        )
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song2, added_by=self.user1, position=2
        )

        mutation = """
            mutation DuplicatePlaylist($playlistId: ID!, $newName: String) {
                duplicatePlaylist(playlistId: $playlistId, newName: $newName) {
                    success
                    message
                    playlist {
                        id
                        name
                    }
                }
            }
        """

        context = self._get_user_context(self.user2)
        result = self.client.execute(
            mutation,
            variables={"playlistId": str(self.playlist.id), "newName": "My Copy"},
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["duplicatePlaylist"]
        self.assertTrue(data["success"])
        self.assertEqual(data["playlist"]["name"], "My Copy")

        # Verify songs were copied by checking total count for user2
        user2_playlists = Playlist.objects.filter(user=self.user2)
        total_songs = PlaylistSong.objects.filter(playlist__in=user2_playlists).count()
        self.assertEqual(total_songs, 2)

    def test_duplicate_playlist_default_name(self):
        """Test duplicating playlist with default name"""
        mutation = """
            mutation DuplicatePlaylist($playlistId: ID!) {
                duplicatePlaylist(playlistId: $playlistId) {
                    success
                    playlist {
                        name
                    }
                }
            }
        """

        context = self._get_user_context(self.user2)
        result = self.client.execute(
            mutation,
            variables={"playlistId": str(self.playlist.id)},
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["duplicatePlaylist"]
        self.assertTrue(data["success"])
        self.assertIn("Copy", data["playlist"]["name"])

    # COLLABORATOR TESTS

    def test_add_collaborator_success(self):
        """Test adding a collaborator to playlist"""
        self.playlist.is_collaborative = True
        self.playlist.save()

        mutation = """
            mutation AddCollaborator($playlistId: ID!, $userId: ID!) {
                addCollaborator(playlistId: $playlistId, userId: $userId) {
                    success
                    message
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            mutation,
            variables={
                "playlistId": str(self.playlist.id),
                "userId": str(self.user2.id),
            },
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["addCollaborator"]
        self.assertTrue(data["success"])

        # Verify collaborator is following
        self.assertTrue(
            PlaylistFollower.objects.filter(
                user=self.user2, playlist=self.playlist
            ).exists()
        )

    def test_add_collaborator_not_owner(self):
        """Test non-owner cannot add collaborator"""
        self.playlist.is_collaborative = True
        self.playlist.save()

        mutation = """
            mutation AddCollaborator($playlistId: ID!, $userId: ID!) {
                addCollaborator(playlistId: $playlistId, userId: $userId) {
                    success
                    message
                }
            }
        """

        context = self._get_user_context(self.user2)
        result = self.client.execute(
            mutation,
            variables={
                "playlistId": str(self.playlist.id),
                "userId": str(self.user2.id),
            },
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["addCollaborator"]
        self.assertFalse(data["success"])
        self.assertIn("owner", data["message"].lower())

    def test_add_collaborator_non_collaborative(self):
        """Test adding collaborator to non-collaborative playlist fails"""
        mutation = """
            mutation AddCollaborator($playlistId: ID!, $userId: ID!) {
                addCollaborator(playlistId: $playlistId, userId: $userId) {
                    success
                    message
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            mutation,
            variables={
                "playlistId": str(self.playlist.id),
                "userId": str(self.user2.id),
            },
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["addCollaborator"]
        self.assertFalse(data["success"])
        self.assertIn("collaborative", data["message"].lower())

    def test_remove_collaborator_success(self):
        """Test removing a collaborator from playlist"""
        self.playlist.is_collaborative = True
        self.playlist.save()
        PlaylistFollower.objects.create(user=self.user2, playlist=self.playlist)

        mutation = """
            mutation RemoveCollaborator($playlistId: ID!, $userId: ID!) {
                removeCollaborator(playlistId: $playlistId, userId: $userId) {
                    success
                    message
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            mutation,
            variables={
                "playlistId": str(self.playlist.id),
                "userId": str(self.user2.id),
            },
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        data = result["data"]["removeCollaborator"]
        self.assertTrue(data["success"])

        # Verify removal
        self.assertFalse(
            PlaylistFollower.objects.filter(
                user=self.user2, playlist=self.playlist
            ).exists()
        )
