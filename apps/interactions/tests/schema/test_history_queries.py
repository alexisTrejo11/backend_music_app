from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene.test import Client
from datetime import timedelta
from django.utils import timezone

from apps.interactions.models import ListeningHistory
from apps.music.models import Song, Album
from apps.artists.models import Artist
from config.schema import schema

User = get_user_model()


class HistoryQueriesTestCase(TestCase):
    """Test cases for listening history GraphQL queries"""

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

        # Create test data
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

        # Create listening history for user1
        now = timezone.now()
        for i in range(60):
            ListeningHistory.objects.create(
                user=self.user1,
                song=self.song1 if i % 2 == 0 else self.song2,
                duration_played=180,
                completed=True,
                played_at=now - timedelta(minutes=i),
            )

        # Create listening history for user2
        ListeningHistory.objects.create(
            user=self.user2, song=self.song1, duration_played=100, completed=False
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

    # LISTENING HISTORY QUERY TESTS

    def test_listening_history_default_params(self):
        """Test fetching listening history with default parameters"""
        query = """
            query {
                listeningHistory {
                    id
                    song {
                        id
                        title
                    }
                    playedAt
                    durationPlayed
                    completed
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user1)
        )

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["listeningHistory"])
        # Default limit is 50
        self.assertEqual(len(result["data"]["listeningHistory"]), 50)

    def test_listening_history_with_limit(self):
        """Test fetching listening history with custom limit"""
        query = """
            query {
                listeningHistory(limit: 10) {
                    id
                    song {
                        title
                    }
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user1)
        )

        self.assertIsNone(result.get("errors"))
        self.assertEqual(len(result["data"]["listeningHistory"]), 10)

    def test_listening_history_with_offset(self):
        """Test fetching listening history with offset"""
        query = """
            query {
                listeningHistory(limit: 10, offset: 5) {
                    id
                    song {
                        title
                    }
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user1)
        )

        self.assertIsNone(result.get("errors"))
        self.assertEqual(len(result["data"]["listeningHistory"]), 10)

    def test_listening_history_pagination(self):
        """Test listening history pagination"""
        # First page
        query_page1 = """
            query {
                listeningHistory(limit: 20, offset: 0) {
                    id
                }
            }
        """

        result_page1 = self.client.execute(
            query_page1, context_value=self._get_user_context(self.user1)
        )

        # Second page
        query_page2 = """
            query {
                listeningHistory(limit: 20, offset: 20) {
                    id
                }
            }
        """

        result_page2 = self.client.execute(
            query_page2, context_value=self._get_user_context(self.user1)
        )

        self.assertIsNone(result_page1.get("errors"))
        self.assertIsNone(result_page2.get("errors"))
        self.assertEqual(len(result_page1["data"]["listeningHistory"]), 20)
        self.assertEqual(len(result_page2["data"]["listeningHistory"]), 20)

        # Ensure different results
        ids_page1 = [item["id"] for item in result_page1["data"]["listeningHistory"]]
        ids_page2 = [item["id"] for item in result_page2["data"]["listeningHistory"]]
        self.assertNotEqual(ids_page1, ids_page2)

    def test_listening_history_ordered_by_date(self):
        """Test listening history is ordered by played_at descending"""
        query = """
            query {
                listeningHistory(limit: 5) {
                    id
                    playedAt
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user1)
        )

        self.assertIsNone(result.get("errors"))
        played_dates = [item["playedAt"] for item in result["data"]["listeningHistory"]]

        # Verify descending order
        for i in range(len(played_dates) - 1):
            self.assertGreaterEqual(played_dates[i], played_dates[i + 1])

    def test_listening_history_includes_related_data(self):
        """Test listening history includes song, artist, and album data"""
        query = """
            query {
                listeningHistory(limit: 1) {
                    id
                    song {
                        id
                        title
                        artist {
                            id
                            name
                        }
                        album {
                            id
                            title
                        }
                    }
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user1)
        )

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["listeningHistory"][0]["song"])
        self.assertIsNotNone(result["data"]["listeningHistory"][0]["song"]["artist"])
        self.assertIsNotNone(result["data"]["listeningHistory"][0]["song"]["album"])

    def test_listening_history_user_isolation(self):
        """Test users only see their own listening history"""
        query = """
            query {
                listeningHistory {
                    id
                }
            }
        """

        result_user1 = self.client.execute(
            query, context_value=self._get_user_context(self.user1)
        )
        result_user2 = self.client.execute(
            query, context_value=self._get_user_context(self.user2)
        )

        self.assertIsNone(result_user1.get("errors"))
        self.assertIsNone(result_user2.get("errors"))

        # User1 should have 50 (limit) out of 60
        self.assertEqual(len(result_user1["data"]["listeningHistory"]), 50)
        # User2 should have only 1
        self.assertEqual(len(result_user2["data"]["listeningHistory"]), 1)

    def test_listening_history_unauthenticated(self):
        """Test fetching listening history without authentication"""
        query = """
            query {
                listeningHistory {
                    id
                }
            }
        """

        result = self.client.execute(query, context_value=self._get_anonymous_context())

        self.assertIsNotNone(result.get("errors"))

    def test_listening_history_empty(self):
        """Test fetching listening history for user with no history"""
        user3 = User.objects.create_user(
            username="user3", email="user3@example.com", password="testpass123"
        )

        query = """
            query {
                listeningHistory {
                    id
                }
            }
        """

        result = self.client.execute(query, context_value=self._get_user_context(user3))

        self.assertIsNone(result.get("errors"))
        self.assertEqual(len(result["data"]["listeningHistory"]), 0)

    # RECENT PLAYS QUERY TESTS

    def test_recent_plays_default_params(self):
        """Test fetching recent plays with default parameters"""
        query = """
            query {
                recentPlays {
                    id
                    song {
                        title
                    }
                    playedAt
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user1)
        )

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["recentPlays"])
        # Default limit is 20
        self.assertEqual(len(result["data"]["recentPlays"]), 20)

    def test_recent_plays_with_limit(self):
        """Test fetching recent plays with custom limit"""
        query = """
            query {
                recentPlays(limit: 5) {
                    id
                    song {
                        title
                    }
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user1)
        )

        self.assertIsNone(result.get("errors"))
        self.assertEqual(len(result["data"]["recentPlays"]), 5)

    def test_recent_plays_ordered_by_date(self):
        """Test recent plays is ordered by played_at descending"""
        query = """
            query {
                recentPlays(limit: 10) {
                    playedAt
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user1)
        )

        self.assertIsNone(result.get("errors"))
        played_dates = [item["playedAt"] for item in result["data"]["recentPlays"]]

        # Verify descending order
        for i in range(len(played_dates) - 1):
            self.assertGreaterEqual(played_dates[i], played_dates[i + 1])

    def test_recent_plays_includes_related_data(self):
        """Test recent plays includes song, artist, and album data"""
        query = """
            query {
                recentPlays(limit: 1) {
                    id
                    song {
                        id
                        title
                        artist {
                            name
                        }
                        album {
                            title
                        }
                    }
                }
            }
        """

        result = self.client.execute(
            query, context_value=self._get_user_context(self.user1)
        )

        self.assertIsNone(result.get("errors"))
        self.assertIsNotNone(result["data"]["recentPlays"][0]["song"])
        self.assertIsNotNone(result["data"]["recentPlays"][0]["song"]["artist"])
        self.assertIsNotNone(result["data"]["recentPlays"][0]["song"]["album"])

    def test_recent_plays_user_isolation(self):
        """Test users only see their own recent plays"""
        query = """
            query {
                recentPlays {
                    id
                }
            }
        """

        result_user1 = self.client.execute(
            query, context_value=self._get_user_context(self.user1)
        )
        result_user2 = self.client.execute(
            query, context_value=self._get_user_context(self.user2)
        )

        self.assertIsNone(result_user1.get("errors"))
        self.assertIsNone(result_user2.get("errors"))

        # User1 should have 20 (limit)
        self.assertEqual(len(result_user1["data"]["recentPlays"]), 20)
        # User2 should have only 1
        self.assertEqual(len(result_user2["data"]["recentPlays"]), 1)

    def test_recent_plays_unauthenticated(self):
        """Test fetching recent plays without authentication"""
        query = """
            query {
                recentPlays {
                    id
                }
            }
        """

        result = self.client.execute(query, context_value=self._get_anonymous_context())

        self.assertIsNotNone(result.get("errors"))

    def test_recent_plays_empty(self):
        """Test fetching recent plays for user with no history"""
        user3 = User.objects.create_user(
            username="user3", email="user3@example.com", password="testpass123"
        )

        query = """
            query {
                recentPlays {
                    id
                }
            }
        """

        result = self.client.execute(query, context_value=self._get_user_context(user3))

        self.assertIsNone(result.get("errors"))
        self.assertEqual(len(result["data"]["recentPlays"]), 0)
