from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene.test import Client
from unittest.mock import Mock, patch

from apps.interactions.models import Review
from apps.music.models import Album, Song
from apps.artists.models import Artist
from config.schema import schema

User = get_user_model()


class ReviewMutationsTestCase(TestCase):
    """Test cases for review GraphQL mutations"""

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
        self.song = Song.objects.create(
            title="Test Song",
            slug="test-song",
            artist=self.artist,
            album=self.album,
            duration=210,
        )

        # Create a review by user1
        self.review = Review.objects.create(
            user=self.user1, album=self.album, rating=4, comment="Great album!"
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

    # ADD REVIEW TESTS

    def test_add_album_review_success(self):
        """Test adding an album review successfully"""
        mutation = """
            mutation AddReview($input: AddReviewInput!) {
                addReview(input: $input) {
                    success
                    message
                    review {
                        id
                        rating
                        comment
                    }
                }
            }
        """

        variables = {
            "input": {
                "albumId": str(self.album.id),
                "rating": 5,
                "comment": "Absolutely amazing!",
            }
        }

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user2),
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["addReview"]["success"])
        self.assertEqual(
            result["data"]["addReview"]["message"], "Review added successfully"
        )
        self.assertEqual(result["data"]["addReview"]["review"]["rating"], 5)

    def test_add_song_review_success(self):
        """Test adding a song review successfully"""
        mutation = """
            mutation AddReview($input: AddReviewInput!) {
                addReview(input: $input) {
                    success
                    message
                    review {
                        id
                        rating
                        comment
                    }
                }
            }
        """

        variables = {
            "input": {
                "songId": str(self.song.id),
                "rating": 3,
                "comment": "Pretty good track",
            }
        }

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user1),
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["addReview"]["success"])

    def test_add_review_without_comment(self):
        """Test adding a review without comment"""
        mutation = """
            mutation AddReview($input: AddReviewInput!) {
                addReview(input: $input) {
                    success
                    message
                    review {
                        rating
                        comment
                    }
                }
            }
        """

        variables = {
            "input": {
                "albumId": str(self.album.id),
                "rating": 4,
            }
        }

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user2),
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["addReview"]["success"])

    def test_add_review_unauthenticated(self):
        """Test adding a review without authentication"""
        mutation = """
            mutation AddReview($input: AddReviewInput!) {
                addReview(input: $input) {
                    success
                    message
                }
            }
        """

        variables = {
            "input": {
                "albumId": str(self.album.id),
                "rating": 5,
            }
        }

        result = self.client.execute(
            mutation, variables=variables, context_value=self._get_anonymous_context()
        )

        self.assertIsNotNone(result.get("errors"))

    @patch(
        "apps.interactions.services.interaction_service.InteractionService.add_review"
    )
    def test_add_review_service_error(self, mock_add):
        """Test adding a review when service raises an error"""
        mock_add.side_effect = Exception("Validation error")

        mutation = """
            mutation AddReview($input: AddReviewInput!) {
                addReview(input: $input) {
                    success
                    message
                }
            }
        """

        variables = {
            "input": {
                "albumId": str(self.album.id),
                "rating": 5,
            }
        }

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user1),
        )

        self.assertIsNone(result.get("errors"))
        self.assertFalse(result["data"]["addReview"]["success"])
        self.assertIn("Validation error", result["data"]["addReview"]["message"])

    # UPDATE REVIEW TESTS

    def test_update_review_success(self):
        """Test updating a review successfully"""
        mutation = """
            mutation UpdateReview($reviewId: ID!, $input: UpdateReviewInput!) {
                updateReview(reviewId: $reviewId, input: $input) {
                    success
                    message
                    review {
                        id
                        rating
                        comment
                    }
                }
            }
        """

        variables = {
            "reviewId": str(self.review.id),
            "input": {
                "rating": 5,
                "comment": "Changed my mind - it's perfect!",
            },
        }

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user1),
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["updateReview"]["success"])
        self.assertEqual(result["data"]["updateReview"]["review"]["rating"], 5)

    def test_update_review_rating_only(self):
        """Test updating only the rating"""
        mutation = """
            mutation UpdateReview($reviewId: ID!, $input: UpdateReviewInput!) {
                updateReview(reviewId: $reviewId, input: $input) {
                    success
                    message
                }
            }
        """

        variables = {
            "reviewId": str(self.review.id),
            "input": {
                "rating": 3,
            },
        }

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user1),
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["updateReview"]["success"])

    def test_update_review_unauthorized(self):
        """Test updating a review by different user"""
        mutation = """
            mutation UpdateReview($reviewId: ID!, $input: UpdateReviewInput!) {
                updateReview(reviewId: $reviewId, input: $input) {
                    success
                    message
                }
            }
        """

        variables = {
            "reviewId": str(self.review.id),
            "input": {
                "rating": 1,
            },
        }

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user2),
        )

        # Should return error or failure
        self.assertIsNone(result.get("errors"))
        self.assertFalse(result["data"]["updateReview"]["success"])

    def test_update_review_unauthenticated(self):
        """Test updating a review without authentication"""
        mutation = """
            mutation UpdateReview($reviewId: ID!, $input: UpdateReviewInput!) {
                updateReview(reviewId: $reviewId, input: $input) {
                    success
                    message
                }
            }
        """

        variables = {
            "reviewId": str(self.review.id),
            "input": {
                "rating": 5,
            },
        }

        result = self.client.execute(
            mutation, variables=variables, context_value=self._get_anonymous_context()
        )

        self.assertIsNotNone(result.get("errors"))

    # DELETE REVIEW TESTS

    def test_delete_review_success(self):
        """Test deleting a review successfully"""
        mutation = """
            mutation DeleteReview($reviewId: ID!) {
                deleteReview(reviewId: $reviewId) {
                    success
                    message
                }
            }
        """

        variables = {"reviewId": str(self.review.id)}

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user1),
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["deleteReview"]["success"])
        self.assertEqual(
            result["data"]["deleteReview"]["message"], "Review deleted successfully"
        )

        # Verify review was deleted
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())

    def test_delete_review_unauthorized(self):
        """Test deleting a review by different user"""
        mutation = """
            mutation DeleteReview($reviewId: ID!) {
                deleteReview(reviewId: $reviewId) {
                    success
                    message
                }
            }
        """

        variables = {"reviewId": str(self.review.id)}

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user2),
        )

        # Should return error or failure
        self.assertIsNone(result.get("errors"))
        self.assertFalse(result["data"]["deleteReview"]["success"])

        # Verify review was not deleted
        self.assertTrue(Review.objects.filter(id=self.review.id).exists())

    def test_delete_review_unauthenticated(self):
        """Test deleting a review without authentication"""
        mutation = """
            mutation DeleteReview($reviewId: ID!) {
                deleteReview(reviewId: $reviewId) {
                    success
                    message
                }
            }
        """

        variables = {"reviewId": str(self.review.id)}

        result = self.client.execute(
            mutation, variables=variables, context_value=self._get_anonymous_context()
        )

        self.assertIsNotNone(result.get("errors"))

    def test_delete_review_invalid_id(self):
        """Test deleting a review with invalid ID"""
        mutation = """
            mutation DeleteReview($reviewId: ID!) {
                deleteReview(reviewId: $reviewId) {
                    success
                    message
                }
            }
        """

        variables = {"reviewId": "99999"}

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user1),
        )

        self.assertIsNone(result.get("errors"))
        self.assertFalse(result["data"]["deleteReview"]["success"])

    # MARK REVIEW HELPFUL TESTS

    def test_mark_review_helpful_success(self):
        """Test marking a review as helpful"""
        mutation = """
            mutation MarkReviewHelpful($reviewId: ID!) {
                markReviewHelpful(reviewId: $reviewId) {
                    success
                    message
                }
            }
        """

        variables = {"reviewId": str(self.review.id)}

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user2),
        )

        self.assertIsNone(result.get("errors"))
        self.assertTrue(result["data"]["markReviewHelpful"]["success"])
        self.assertEqual(
            result["data"]["markReviewHelpful"]["message"], "Review marked as helpful"
        )

    def test_mark_review_helpful_unauthenticated(self):
        """Test marking a review as helpful without authentication"""
        mutation = """
            mutation MarkReviewHelpful($reviewId: ID!) {
                markReviewHelpful(reviewId: $reviewId) {
                    success
                    message
                }
            }
        """

        variables = {"reviewId": str(self.review.id)}

        result = self.client.execute(
            mutation, variables=variables, context_value=self._get_anonymous_context()
        )

        self.assertIsNotNone(result.get("errors"))

    def test_mark_review_helpful_invalid_id(self):
        """Test marking a review as helpful with invalid ID"""
        mutation = """
            mutation MarkReviewHelpful($reviewId: ID!) {
                markReviewHelpful(reviewId: $reviewId) {
                    success
                    message
                }
            }
        """

        variables = {"reviewId": "99999"}

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user1),
        )

        self.assertIsNone(result.get("errors"))
        self.assertFalse(result["data"]["markReviewHelpful"]["success"])

    @patch(
        "apps.interactions.services.interaction_service.InteractionService.mark_review_helpful"
    )
    def test_mark_review_helpful_service_error(self, mock_mark):
        """Test marking a review as helpful when service raises an error"""
        mock_mark.side_effect = Exception("Database error")

        mutation = """
            mutation MarkReviewHelpful($reviewId: ID!) {
                markReviewHelpful(reviewId: $reviewId) {
                    success
                    message
                }
            }
        """

        variables = {"reviewId": str(self.review.id)}

        result = self.client.execute(
            mutation,
            variables=variables,
            context_value=self._get_user_context(self.user2),
        )

        self.assertIsNone(result.get("errors"))
        self.assertFalse(result["data"]["markReviewHelpful"]["success"])
        self.assertIn("Database error", result["data"]["markReviewHelpful"]["message"])
