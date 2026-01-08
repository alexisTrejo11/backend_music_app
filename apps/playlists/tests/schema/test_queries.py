from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene.test import Client

from apps.playlists.models import Playlist, PlaylistFollower, PlaylistSong
from apps.music.models import Song, Album, Genre
from apps.artists.models import Artist
from config.schema import schema

User = get_user_model()


class PlaylistQueriesTestCase(TestCase):
    """Test cases for Playlist GraphQL queries"""

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

        # Create test data for songs
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

        # Create playlists for user1
        self.public_playlist = Playlist.objects.create(
            name="Public Playlist",
            slug="public-playlist",
            description="A public playlist",
            user=self.user1,
            is_public=True,
        )

        self.private_playlist = Playlist.objects.create(
            name="Private Playlist",
            slug="private-playlist",
            description="A private playlist",
            user=self.user1,
            is_public=False,
        )

        self.collaborative_playlist = Playlist.objects.create(
            name="Collaborative Playlist",
            slug="collaborative-playlist",
            description="A collaborative playlist",
            user=self.user1,
            is_public=True,
            is_collaborative=True,
        )

        self.editorial_playlist = Playlist.objects.create(
            name="Editorial Playlist",
            slug="editorial-playlist",
            description="An editorial playlist",
            user=self.user1,
            is_public=True,
            is_editorial=True,
        )

        # Create playlist for user2
        self.user2_playlist = Playlist.objects.create(
            name="User2 Playlist",
            slug="user2-playlist",
            description="User2's playlist",
            user=self.user2,
            is_public=True,
        )

        # Add songs to playlists
        PlaylistSong.objects.create(
            playlist=self.public_playlist,
            song=self.song1,
            added_by=self.user1,
            position=1,
        )
        PlaylistSong.objects.create(
            playlist=self.public_playlist,
            song=self.song2,
            added_by=self.user1,
            position=2,
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

    def test_query_playlist_by_id(self):
        """Test querying a single playlist by ID"""
        query = """
            query GetPlaylist($id: ID!) {
                playlist(id: $id) {
                    id
                    name
                    slug
                    description
                    isPublic
                    user {
                        username
                    }
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            query, variables={"id": str(self.public_playlist.id)}, context_value=context
        )

        self.assertIsNone(result.get("errors"))
        playlist_data = result["data"]["playlist"]
        self.assertEqual(playlist_data["name"], "Public Playlist")
        self.assertEqual(playlist_data["slug"], "public-playlist")
        self.assertTrue(playlist_data["isPublic"])
        self.assertEqual(playlist_data["user"]["username"], "user1")

    def test_query_playlist_by_slug(self):
        """Test querying a single playlist by slug"""
        query = """
            query GetPlaylist($slug: String!) {
                playlist(slug: $slug) {
                    id
                    name
                    slug
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            query, variables={"slug": "public-playlist"}, context_value=context
        )

        self.assertIsNone(result.get("errors"))
        playlist_data = result["data"]["playlist"]
        self.assertEqual(playlist_data["name"], "Public Playlist")

    def test_query_playlist_not_found(self):
        """Test querying non-existent playlist returns error"""
        query = """
            query GetPlaylist($id: ID!) {
                playlist(id: $id) {
                    id
                    name
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            query, variables={"id": "99999"}, context_value=context
        )

        self.assertIsNotNone(result.get("errors"))
        self.assertIn("not found", str(result["errors"]))

    def test_query_private_playlist_as_owner(self):
        """Test owner can view their private playlist"""
        query = """
            query GetPlaylist($id: ID!) {
                playlist(id: $id) {
                    id
                    name
                    isPublic
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            query,
            variables={"id": str(self.private_playlist.id)},
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        playlist_data = result["data"]["playlist"]
        self.assertEqual(playlist_data["name"], "Private Playlist")
        self.assertFalse(playlist_data["isPublic"])

    def test_query_private_playlist_as_other_user(self):
        """Test other users cannot view private playlists"""
        query = """
            query GetPlaylist($id: ID!) {
                playlist(id: $id) {
                    id
                    name
                }
            }
        """

        context = self._get_user_context(self.user2)
        result = self.client.execute(
            query,
            variables={"id": str(self.private_playlist.id)},
            context_value=context,
        )

        self.assertIsNotNone(result.get("errors"))
        self.assertIn("private", str(result["errors"]).lower())

    def test_query_private_playlist_unauthenticated(self):
        """Test unauthenticated users cannot view private playlists"""
        query = """
            query GetPlaylist($id: ID!) {
                playlist(id: $id) {
                    id
                    name
                }
            }
        """

        context = self._get_anonymous_context()
        result = self.client.execute(
            query,
            variables={"id": str(self.private_playlist.id)},
            context_value=context,
        )

        self.assertIsNotNone(result.get("errors"))
        self.assertIn("private", str(result["errors"]).lower())

    def test_query_my_playlists(self):
        """Test querying current user's playlists"""
        query = """
            query {
                myPlaylists {
                    id
                    name
                    isPublic
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(query, context_value=context)

        self.assertIsNone(result.get("errors"))
        playlists = result["data"]["myPlaylists"]
        self.assertEqual(len(playlists), 4)  # user1 has 4 playlists
        playlist_names = [p["name"] for p in playlists]
        self.assertIn("Public Playlist", playlist_names)
        self.assertIn("Private Playlist", playlist_names)

    def test_query_my_playlists_unauthenticated(self):
        """Test querying my playlists without authentication fails"""
        query = """
            query {
                myPlaylists {
                    id
                    name
                }
            }
        """

        context = self._get_anonymous_context()
        result = self.client.execute(query, context_value=context)

        self.assertIsNotNone(result.get("errors"))
        self.assertIn("logged in", str(result["errors"]).lower())

    def test_query_user_playlists_by_user_id(self):
        """Test querying playlists by user ID"""
        query = """
            query GetUserPlaylists($userId: ID!) {
                userPlaylists(userId: $userId) {
                    id
                    name
                    isPublic
                }
            }
        """

        context = self._get_user_context(self.user2)
        result = self.client.execute(
            query, variables={"userId": str(self.user1.id)}, context_value=context
        )

        self.assertIsNone(result.get("errors"))
        playlists = result["data"]["userPlaylists"]
        # Should only see public playlists (3: public, collaborative, editorial)
        self.assertEqual(len(playlists), 3)
        for playlist in playlists:
            self.assertTrue(playlist["isPublic"])

    def test_query_user_playlists_by_username(self):
        """Test querying playlists by username"""
        query = """
            query GetUserPlaylists($username: String!) {
                userPlaylists(username: $username) {
                    id
                    name
                }
            }
        """

        context = self._get_user_context(self.user2)
        result = self.client.execute(
            query, variables={"username": "user1"}, context_value=context
        )

        self.assertIsNone(result.get("errors"))
        playlists = result["data"]["userPlaylists"]
        self.assertGreater(len(playlists), 0)

    def test_query_user_playlists_include_private_as_owner(self):
        """Test owner can see their private playlists with includePrivate"""
        query = """
            query GetUserPlaylists($userId: ID!, $includePrivate: Boolean!) {
                userPlaylists(userId: $userId, includePrivate: $includePrivate) {
                    id
                    name
                    isPublic
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            query,
            variables={"userId": str(self.user1.id), "includePrivate": True},
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        playlists = result["data"]["userPlaylists"]
        self.assertEqual(len(playlists), 4)  # All 4 playlists including private

    def test_query_user_playlists_include_private_as_other(self):
        """Test other users cannot see private playlists even with includePrivate"""
        query = """
            query GetUserPlaylists($userId: ID!, $includePrivate: Boolean!) {
                userPlaylists(userId: $userId, includePrivate: $includePrivate) {
                    id
                    name
                    isPublic
                }
            }
        """

        context = self._get_user_context(self.user2)
        result = self.client.execute(
            query,
            variables={"userId": str(self.user1.id), "includePrivate": True},
            context_value=context,
        )

        self.assertIsNone(result.get("errors"))
        playlists = result["data"]["userPlaylists"]
        # Should still only see public playlists
        self.assertEqual(len(playlists), 3)

    def test_query_user_playlists_not_found(self):
        """Test querying playlists for non-existent user"""
        query = """
            query GetUserPlaylists($userId: ID!) {
                userPlaylists(userId: $userId) {
                    id
                    name
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            query, variables={"userId": "99999"}, context_value=context
        )

        self.assertIsNotNone(result.get("errors"))
        self.assertIn("not found", str(result["errors"]))

    def test_query_followed_playlists(self):
        """Test querying playlists followed by current user"""
        # User1 follows user2's playlist
        PlaylistFollower.objects.create(user=self.user1, playlist=self.user2_playlist)

        query = """
            query {
                followedPlaylists {
                    id
                    name
                    user {
                        username
                    }
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(query, context_value=context)

        self.assertIsNone(result.get("errors"))
        playlists = result["data"]["followedPlaylists"]
        self.assertEqual(len(playlists), 1)
        self.assertEqual(playlists[0]["name"], "User2 Playlist")
        self.assertEqual(playlists[0]["user"]["username"], "user2")

    def test_query_followed_playlists_unauthenticated(self):
        """Test querying followed playlists without authentication fails"""
        query = """
            query {
                followedPlaylists {
                    id
                    name
                }
            }
        """

        context = self._get_anonymous_context()
        result = self.client.execute(query, context_value=context)

        self.assertIsNotNone(result.get("errors"))
        self.assertIn("logged in", str(result["errors"]).lower())

    def test_query_featured_playlists(self):
        """Test querying featured/editorial playlists"""
        query = """
            query {
                featuredPlaylists(limit: 10) {
                    id
                    name
                    isEditorial
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(query, context_value=context)

        self.assertIsNone(result.get("errors"))
        playlists = result["data"]["featuredPlaylists"]
        self.assertGreater(len(playlists), 0)
        # All should be editorial
        for playlist in playlists:
            self.assertTrue(playlist["isEditorial"])

    def test_query_search_playlists(self):
        """Test searching playlists by name"""
        query = """
            query SearchPlaylists($query: String!) {
                searchPlaylists(query: $query) {
                    id
                    name
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            query, variables={"query": "Public"}, context_value=context
        )

        self.assertIsNone(result.get("errors"))
        playlists = result["data"]["searchPlaylists"]
        self.assertGreater(len(playlists), 0)
        # Public Playlist should be in results
        playlist_names = [p["name"] for p in playlists]
        self.assertIn("Public Playlist", playlist_names)

    def test_query_search_playlists_by_description(self):
        """Test searching playlists by description"""
        query = """
            query SearchPlaylists($query: String!) {
                searchPlaylists(query: $query) {
                    id
                    name
                    description
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            query, variables={"query": "collaborative"}, context_value=context
        )

        self.assertIsNone(result.get("errors"))
        playlists = result["data"]["searchPlaylists"]
        self.assertEqual(len(playlists), 1)
        self.assertEqual(playlists[0]["name"], "Collaborative Playlist")

    def test_query_search_playlists_with_limit(self):
        """Test searching playlists with limit"""
        query = """
            query SearchPlaylists($query: String!, $limit: Int!) {
                searchPlaylists(query: $query, limit: $limit) {
                    id
                    name
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            query, variables={"query": "Playlist", "limit": 2}, context_value=context
        )

        self.assertIsNone(result.get("errors"))
        playlists = result["data"]["searchPlaylists"]
        self.assertLessEqual(len(playlists), 2)

    def test_query_trending_playlists(self):
        """Test querying trending playlists"""
        # Add followers to make playlist trending
        PlaylistFollower.objects.create(user=self.user2, playlist=self.public_playlist)

        query = """
            query {
                trendingPlaylists(limit: 10) {
                    id
                    name
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(query, context_value=context)

        self.assertIsNone(result.get("errors"))
        playlists = result["data"]["trendingPlaylists"]
        self.assertGreater(len(playlists), 0)

    def test_query_playlist_with_songs(self):
        """Test querying playlist with its songs"""
        query = """
            query GetPlaylist($id: ID!) {
                playlist(id: $id) {
                    id
                    name
                    songsCount
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            query, variables={"id": str(self.public_playlist.id)}, context_value=context
        )

        self.assertIsNone(result.get("errors"))
        playlist_data = result["data"]["playlist"]
        self.assertEqual(playlist_data["songsCount"], 2)

    def test_query_playlist_computed_fields(self):
        """Test playlist computed fields"""
        query = """
            query GetPlaylist($id: ID!) {
                playlist(id: $id) {
                    id
                    name
                    isFollowing
                    isOwner
                    canEdit
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(
            query, variables={"id": str(self.public_playlist.id)}, context_value=context
        )

        self.assertIsNone(result.get("errors"))
        playlist_data = result["data"]["playlist"]
        self.assertFalse(playlist_data["isFollowing"])  # Owner doesn't follow own
        self.assertTrue(playlist_data["isOwner"])
        self.assertTrue(playlist_data["canEdit"])

    def test_query_without_required_parameter(self):
        """Test querying playlist without required parameter fails"""
        query = """
            query {
                playlist {
                    id
                    name
                }
            }
        """

        context = self._get_user_context(self.user1)
        result = self.client.execute(query, context_value=context)

        self.assertIsNotNone(result.get("errors"))
