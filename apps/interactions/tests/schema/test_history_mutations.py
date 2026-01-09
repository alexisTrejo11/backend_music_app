from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene.test import Client
from unittest.mock import Mock, patch

from apps.interactions.models import ListeningHistory
from apps.music.models import Song, Album
from apps.artists.models import Artist
from config.schema import schema

User = get_user_model()


class HistoryMutationsTestCase(TestCase):
    """Test cases for listening history GraphQL mutations"""

    def setUp(self):
        """Set up test data"""
        self.client = Client(schema)

        # Create user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create test data
        self.artist = Artist.objects.create(name="Test Artist", slug="test-artist")
        self.album = Album.objects.create(
            title="Test Album",
            slug="test-album",
            artist=self.artist,
            release_date="2024-01-01",
        )
        self.song = Song.objects.create(
            title="Test Song",
            slug="test-song",
            artist=self.artist,
            album=self.album,
            duration=210,
        )

        # Create listening history entries
        ListeningHistory.objects.create(
            user=self.user, song=self.song, duration_played=180, completed=True
        )
        ListeningHistory.objects.create(
            user=self.user, song=self.song, duration_played=120, completed=False
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

    # TRACK PLAY TESTS

    def test_track_play_success(self):
        """Test tracking a play successfully"""
        mutation = """
            mutation TrackPlay($input: TrackPlayInput!) {
                trackPlay(input: $input) {
                    success
                    message
                }
            }
        """

        variables = {
            "input": {
                "songId": str(self.song.id),
                "durationPlayed": 200,
                "completed": True,
                "source": "playlist",
                "sourceId": "123",
            }
        }

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user),
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["trackPlay"]["success"])
        self.assertEqual(
            result["data"]["trackPlay"]["message"], "Play tracked successfully"
        )

        # Verify entry was created
        self.assertEqual(ListeningHistory.objects.filter(user=self.user).count(), 3)

    def test_track_play_minimal_data(self):
        """Test tracking a play with minimal required data"""
        mutation = """
            mutation TrackPlay($input: TrackPlayInput!) {
                trackPlay(input: $input) {
                    success
                    message
                }
            }
        """

        variables = {
            "input": {
                "songId": str(self.song.id),
                "durationPlayed": 50,
            }
        }

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user),
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["trackPlay"]["success"])

    def test_track_play_unauthenticated(self):
        """Test tracking a play without authentication"""
        mutation = """
            mutation TrackPlay($input: TrackPlayInput!) {
                trackPlay(input: $input) {
                    success
                    message
                }
            }
        """

        variables = {
            "input": {
                "songId": str(self.song.id),
                "durationPlayed": 100,
            }
        }

        result = self.client.execute(
            mutation, variables=variables, context_value=self._get_anonymous_context()
        )

        self.assertIsNotNone(result.get("errors"))

    @patch(
        "apps.interactions.services.interaction_service.InteractionService.track_play"
    )
    def test_track_play_service_error(self, mock_track_play):
        """Test tracking a play when service raises an error"""
        mock_track_play.side_effect = Exception("Database error")

        mutation = """
            mutation TrackPlay($input: TrackPlayInput!) {
                trackPlay(input: $input) {
                    success
                    message
                }
            }
        """

        variables = {
            "input": {
                "songId": str(self.song.id),
                "durationPlayed": 100,
            }
        }

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user),
        )

        self.assertIsNone(result.get("errors"))
        self.assertFalse(result["data"]["trackPlay"]["success"])
        self.assertIn("Database error", result["data"]["trackPlay"]["message"])

    # CLEAR LISTENING HISTORY TESTS

    def test_clear_listening_history_success(self):
        """Test clearing listening history successfully"""
        mutation = """
            mutation ClearListeningHistory($confirm: Boolean!) {
                clearListeningHistory(confirm: $confirm) {
                    success
                    message
                }
            }
        """

        variables = {"confirm": True}

        # Verify we have entries before
        self.assertEqual(ListeningHistory.objects.filter(user=self.user).count(), 2)

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user),
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["clearListeningHistory"]["success"])
        self.assertEqual(
            result["data"]["clearListeningHistory"]["message"],
            "Listening history cleared successfully",
        )

        # Verify entries were cleared
        self.assertEqual(ListeningHistory.objects.filter(user=self.user).count(), 0)

    def test_clear_listening_history_without_confirmation(self):
        """Test clearing listening history without confirmation"""
        mutation = """
            mutation ClearListeningHistory($confirm: Boolean!) {
                clearListeningHistory(confirm: $confirm) {
                    success
                    message
                }
            }
        """

        variables = {"confirm": False}

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user),
        )

        self.assertIsNone(result.get("errors"))
        self.assertFalse(result["data"]["clearListeningHistory"]["success"])
        self.assertIn(
            "Confirmation required", result["data"]["clearListeningHistory"]["message"]
        )

        # Verify entries were not cleared
        self.assertEqual(ListeningHistory.objects.filter(user=self.user).count(), 2)

    def test_clear_listening_history_unauthenticated(self):
        """Test clearing listening history without authentication"""
        mutation = """
            mutation ClearListeningHistory($confirm: Boolean!) {
                clearListeningHistory(confirm: $confirm) {
                    success
                    message
                }
            }
        """

        variables = {"confirm": True}

        result = self.client.execute(
            mutation, variables=variables, context_value=self._get_anonymous_context()
        )

        self.assertIsNotNone(result.get("errors"))

    @patch(
        "apps.interactions.services.interaction_service.InteractionService.clear_listening_history"
    )
    def test_clear_listening_history_service_error(self, mock_clear):
        """Test clearing listening history when service raises an error"""
        mock_clear.side_effect = Exception("Database error")

        mutation = """
            mutation ClearListeningHistory($confirm: Boolean!) {
                clearListeningHistory(confirm: $confirm) {
                    success
                    message
                }
            }
        """

        variables = {"confirm": True}

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user),
        )

        self.assertIsNone(result.get("errors"))
        self.assertFalse(result["data"]["clearListeningHistory"]["success"])
        self.assertIn(
            "Database error", result["data"]["clearListeningHistory"]["message"]
        )
