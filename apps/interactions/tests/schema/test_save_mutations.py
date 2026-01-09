from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene.test import Client
from unittest.mock import Mock, patch

from apps.interactions.models import SavedAlbum
from apps.music.models import Album
from apps.artists.models import Artist
from config.schema import schema

User = get_user_model()


class SaveMutationsTestCase(TestCase):
    """Test cases for save/unsave album GraphQL mutations"""

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
        self.album1 = Album.objects.create(
            title="Test Album 1",
            slug="test-album-1",
            artist=self.artist,
            release_date="2024-01-01",
        )
        self.album2 = Album.objects.create(
            title="Test Album 2",
            slug="test-album-2",
            artist=self.artist,
            release_date="2024-02-01",
        )

        # Create a saved album for user1
        SavedAlbum.objects.create(user=self.user1, album=self.album1)

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

    # SAVE ALBUM TESTS

    def test_save_album_success(self):
        """Test saving an album successfully"""
        mutation = """
            mutation SaveAlbum($albumId: ID!) {
                saveAlbum(albumId: $albumId) {
                    success
                    message
                }
            }
        """

        variables = {"albumId": str(self.album2.id)}

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user1),
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["saveAlbum"]["success"])
        self.assertEqual(
            result["data"]["saveAlbum"]["message"], "Album saved successfully"
        )

        # Verify album was saved
        self.assertTrue(
            SavedAlbum.objects.filter(user=self.user1, album=self.album2).exists()
        )

    def test_save_album_already_saved(self):
        """Test saving an album that is already saved"""
        mutation = """
            mutation SaveAlbum($albumId: ID!) {
                saveAlbum(albumId: $albumId) {
                    success
                    message
                }
            }
        """

        variables = {"albumId": str(self.album1.id)}

        # Should handle gracefully or return appropriate message
        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user1),
        )

        # Depending on implementation, it might succeed or return specific message
        self.assertIsNone(result.get("errors"))

    def test_save_album_unauthenticated(self):
        """Test saving an album without authentication"""
        mutation = """
            mutation SaveAlbum($albumId: ID!) {
                saveAlbum(albumId: $albumId) {
                    success
                    message
                }
            }
        """

        variables = {"albumId": str(self.album1.id)}

        result = self.client.execute(
            mutation, variables=variables, context_value=self._get_anonymous_context()
        )

        self.assertIsNotNone(result.get("errors"))

    def test_save_album_invalid_id(self):
        """Test saving an album with invalid ID"""
        mutation = """
            mutation SaveAlbum($albumId: ID!) {
                saveAlbum(albumId: $albumId) {
                    success
                    message
                }
            }
        """

        variables = {"albumId": "99999"}

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user1),
        )

        # Should return error
        self.assertIsNone(result.get("errors"))
        self.assertFalse(result["data"]["saveAlbum"]["success"])

    @patch(
        "apps.interactions.services.interaction_service.InteractionService.save_album"
    )
    def test_save_album_service_error(self, mock_save):
        """Test saving an album when service raises an error"""
        mock_save.side_effect = Exception("Database error")

        mutation = """
            mutation SaveAlbum($albumId: ID!) {
                saveAlbum(albumId: $albumId) {
                    success
                    message
                }
            }
        """

        variables = {"albumId": str(self.album2.id)}

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user1),
        )

        self.assertIsNone(result.get("errors"))
        self.assertFalse(result["data"]["saveAlbum"]["success"])

    # UNSAVE ALBUM TESTS

    def test_unsave_album_success(self):
        """Test unsaving an album successfully"""
        mutation = """
            mutation UnsaveAlbum($albumId: ID!) {
                unsaveAlbum(albumId: $albumId) {
                    success
                    message
                }
            }
        """

        variables = {"albumId": str(self.album1.id)}

        # Verify album is saved before
        self.assertTrue(
            SavedAlbum.objects.filter(user=self.user1, album=self.album1).exists()
        )

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user1),
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["unsaveAlbum"]["success"])

        # Verify album was unsaved
        self.assertFalse(
            SavedAlbum.objects.filter(user=self.user1, album=self.album1).exists()
        )

    def test_unsave_album_not_saved(self):
        """Test unsaving an album that is not saved"""
        mutation = """
            mutation UnsaveAlbum($albumId: ID!) {
                unsaveAlbum(albumId: $albumId) {
                    success
                    message
                }
            }
        """

        variables = {"albumId": str(self.album2.id)}

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user1),
        )

        # Should handle gracefully
        self.assertIsNone(result.get("errors"))

    def test_unsave_album_unauthenticated(self):
        """Test unsaving an album without authentication"""
        mutation = """
            mutation UnsaveAlbum($albumId: ID!) {
                unsaveAlbum(albumId: $albumId) {
                    success
                    message
                }
            }
        """

        variables = {"albumId": str(self.album1.id)}

        result = self.client.execute(
            mutation, variables=variables, context_value=self._get_anonymous_context()
        )

        self.assertIsNotNone(result.get("errors"))

    def test_unsave_album_invalid_id(self):
        """Test unsaving an album with invalid ID"""
        mutation = """
            mutation UnsaveAlbum($albumId: ID!) {
                unsaveAlbum(albumId: $albumId) {
                    success
                    message
                }
            }
        """

        variables = {"albumId": "99999"}

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user1),
        )

        # Should return error
        self.assertIsNone(result.get("errors"))
        self.assertFalse(result["data"]["unsaveAlbum"]["success"])

    @patch(
        "apps.interactions.services.interaction_service.InteractionService.unsave_album"
    )
    def test_unsave_album_service_error(self, mock_unsave):
        """Test unsaving an album when service raises an error"""
        mock_unsave.side_effect = Exception("Database error")

        mutation = """
            mutation UnsaveAlbum($albumId: ID!) {
                unsaveAlbum(albumId: $albumId) {
                    success
                    message
                }
            }
        """

        variables = {"albumId": str(self.album1.id)}

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user1),
        )

        self.assertIsNone(result.get("errors"))
        self.assertFalse(result["data"]["unsaveAlbum"]["success"])
