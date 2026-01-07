from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.artists.models import Artist, ArtistMember
from apps.artists.services import ArtistService
from apps.music.models import Genre
from apps.interactions.models import FollowedArtist

User = get_user_model()


class ArtistServiceTestCase(TestCase):
    """Test cases for ArtistService"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            is_staff=True,
        )

        # Create some genres
        self.genre_rock = Genre.objects.create(name="Rock", slug="rock")
        self.genre_pop = Genre.objects.create(name="Pop", slug="pop")

        # Create test artist
        self.artist = Artist.objects.create(
            name="Test Artist",
            slug="test-artist",
            bio="Test bio",
            country="US",
            monthly_listeners=1000,
        )
        self.artist.genres.add(self.genre_rock)

    def test_create_artist_success(self):
        """Test successful artist creation"""
        data = {
            "name": "New Artist",
            "bio": "New artist bio",
            "country": "UK",
            "genres": ["Pop", "Rock"],
            "social_links": {
                "website": "https://example.com",
                "spotify": "https://spotify.com/artist",
            },
        }

        artist = ArtistService.create_artist(data)

        self.assertIsNotNone(artist)
        self.assertEqual(artist.name, "New Artist")
        self.assertEqual(artist.slug, "new-artist")
        self.assertEqual(artist.bio, "New artist bio")
        self.assertEqual(artist.country, "UK")
        self.assertEqual(artist.website, "https://example.com")
        self.assertEqual(artist.genres.count(), 2)

    def test_create_artist_without_name(self):
        """Test artist creation without name fails"""
        data = {"bio": "Test bio"}

        with self.assertRaises(ValidationError) as context:
            ArtistService.create_artist(data)

        self.assertIn("name is required", str(context.exception))

    def test_create_artist_duplicate_name(self):
        """Test creating artist with duplicate name fails"""
        data = {"name": "Test Artist"}  # Already exists

        with self.assertRaises(ValidationError) as context:
            ArtistService.create_artist(data)

        self.assertIn("already exists", str(context.exception))

    def test_create_artist_unique_slug_generation(self):
        """Test unique slug generation for duplicate names"""
        # Create artist with same base slug
        data1 = {"name": "Cool Band"}
        artist1 = ArtistService.create_artist(data1)

        # Delete it to allow name reuse, but slug remains
        artist1.delete()

        data2 = {"name": "Cool Band"}
        artist2 = ArtistService.create_artist(data2)

        self.assertEqual(artist2.slug, "cool-band")

    def test_update_artist_success(self):
        """Test successful artist update"""
        data = {
            "name": "Updated Artist",
            "bio": "Updated bio",
            "country": "CA",
            "verified": True,
            "genres": ["Pop"],
        }

        updated_artist = ArtistService.update_artist(str(self.artist.id), data)

        self.assertEqual(updated_artist.name, "Updated Artist")
        self.assertEqual(updated_artist.bio, "Updated bio")
        self.assertEqual(updated_artist.country, "CA")
        self.assertTrue(updated_artist.verified)
        self.assertEqual(updated_artist.genres.count(), 1)
        self.assertEqual(updated_artist.genres.first().name, "Pop")

    def test_update_artist_not_found(self):
        """Test updating non-existent artist fails"""
        data = {"name": "Updated"}

        with self.assertRaises(ValidationError) as context:
            ArtistService.update_artist("99999", data)

        self.assertIn("not found", str(context.exception))

    def test_update_artist_duplicate_name(self):
        """Test updating artist to existing name fails"""
        other_artist = Artist.objects.create(name="Other Artist", slug="other-artist")

        data = {"name": "Other Artist"}

        with self.assertRaises(ValidationError) as context:
            ArtistService.update_artist(str(self.artist.id), data)

        self.assertIn("already exists", str(context.exception))

    def test_delete_artist_success(self):
        """Test successful artist deletion"""
        artist_id = str(self.artist.id)

        result = ArtistService.delete_artist(artist_id)

        self.assertTrue(result)
        self.assertFalse(Artist.objects.filter(id=artist_id).exists())

    def test_delete_artist_not_found(self):
        """Test deleting non-existent artist fails"""
        with self.assertRaises(ValidationError) as context:
            ArtistService.delete_artist("99999")

        self.assertIn("not found", str(context.exception))

    def test_follow_artist_success(self):
        """Test successfully following an artist"""
        result = ArtistService.follow_artist(self.user, str(self.artist.id))

        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Successfully followed artist")
        self.assertEqual(result["artist"], self.artist)

        # Verify follow relationship exists
        self.assertTrue(
            FollowedArtist.objects.filter(user=self.user, artist=self.artist).exists()
        )

    def test_follow_artist_already_following(self):
        """Test following an already followed artist"""
        # First follow
        ArtistService.follow_artist(self.user, str(self.artist.id))

        # Try to follow again
        result = ArtistService.follow_artist(self.user, str(self.artist.id))

        self.assertFalse(result["success"])
        self.assertIn("already following", result["message"])

    def test_follow_artist_not_found(self):
        """Test following non-existent artist fails"""
        with self.assertRaises(ValidationError) as context:
            ArtistService.follow_artist(self.user, "99999")

        self.assertIn("not found", str(context.exception))

    def test_unfollow_artist_success(self):
        """Test successfully unfollowing an artist"""
        # First follow
        ArtistService.follow_artist(self.user, str(self.artist.id))

        # Then unfollow
        result = ArtistService.unfollow_artist(self.user, str(self.artist.id))

        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Successfully unfollowed artist")

        # Verify follow relationship is deleted
        self.assertFalse(
            FollowedArtist.objects.filter(user=self.user, artist=self.artist).exists()
        )

    def test_unfollow_artist_not_following(self):
        """Test unfollowing an artist not followed"""
        result = ArtistService.unfollow_artist(self.user, str(self.artist.id))

        self.assertFalse(result["success"])
        self.assertIn("not following", result["message"])

    def test_get_trending_artists(self):
        """Test getting trending artists"""
        # Create multiple artists with recent followers
        artist2 = Artist.objects.create(
            name="Popular Artist", slug="popular-artist", monthly_listeners=5000
        )

        # Add recent followers
        FollowedArtist.objects.create(
            user=self.user,
            artist=artist2,
            created_at=timezone.now() - timedelta(days=2),
        )

        trending = ArtistService.get_trending_artists("WEEK", limit=10)

        self.assertIsInstance(trending, list)
        self.assertGreater(len(trending), 0)

    def test_get_similar_artists(self):
        """Test getting similar artists based on genres"""
        # Create similar artists with same genre
        similar_artist = Artist.objects.create(
            name="Similar Artist", slug="similar-artist", monthly_listeners=800
        )
        similar_artist.genres.add(self.genre_rock)

        # Create dissimilar artist
        different_artist = Artist.objects.create(
            name="Different Artist", slug="different-artist"
        )
        different_artist.genres.add(self.genre_pop)

        similar = ArtistService.get_similar_artists(str(self.artist.id), limit=10)

        self.assertIn(similar_artist, similar)
        # Different artist might be included if no better matches

    def test_get_similar_artists_not_found(self):
        """Test getting similar artists for non-existent artist fails"""
        with self.assertRaises(ValidationError) as context:
            ArtistService.get_similar_artists("99999")

        self.assertIn("not found", str(context.exception))

    def test_add_member_success(self):
        """Test successfully adding a member to an artist"""
        data = {
            "artist_id": str(self.artist.id),
            "name": "John Doe",
            "role": "Guitarist",
            "join_date": timezone.now().date(),
        }

        member = ArtistService.add_member(data)

        self.assertIsNotNone(member)
        self.assertEqual(member.name, "John Doe")
        self.assertEqual(member.role, "Guitarist")
        self.assertEqual(member.artist, self.artist)

    def test_add_member_without_name(self):
        """Test adding member without name fails"""
        data = {
            "artist_id": str(self.artist.id),
            "role": "Guitarist",
        }

        with self.assertRaises(ValidationError) as context:
            ArtistService.add_member(data)

        self.assertIn("name is required", str(context.exception))

    def test_add_member_without_role(self):
        """Test adding member without role fails"""
        data = {
            "artist_id": str(self.artist.id),
            "name": "John Doe",
        }

        with self.assertRaises(ValidationError) as context:
            ArtistService.add_member(data)

        self.assertIn("role is required", str(context.exception))

    def test_add_member_duplicate_name(self):
        """Test adding member with duplicate name fails"""
        # Add first member
        ArtistMember.objects.create(
            artist=self.artist, name="John Doe", role="Vocalist"
        )

        # Try to add duplicate
        data = {
            "artist_id": str(self.artist.id),
            "name": "John Doe",
            "role": "Guitarist",
        }

        with self.assertRaises(ValidationError) as context:
            ArtistService.add_member(data)

        self.assertIn("already exists", str(context.exception))

    def test_add_member_artist_not_found(self):
        """Test adding member to non-existent artist fails"""
        data = {
            "artist_id": "99999",
            "name": "John Doe",
            "role": "Guitarist",
        }

        with self.assertRaises(ValidationError) as context:
            ArtistService.add_member(data)

        self.assertIn("not found", str(context.exception))

    def test_remove_member_success(self):
        """Test successfully removing a member"""
        member = ArtistMember.objects.create(
            artist=self.artist, name="John Doe", role="Guitarist"
        )
        member_id = str(member.id)

        result = ArtistService.remove_member(member_id)

        self.assertTrue(result)
        self.assertFalse(ArtistMember.objects.filter(id=member_id).exists())

    def test_remove_member_not_found(self):
        """Test removing non-existent member fails"""
        with self.assertRaises(ValidationError) as context:
            ArtistService.remove_member("99999")

        self.assertIn("not found", str(context.exception))

    def test_get_artist_statistics(self):
        """Test getting comprehensive artist statistics"""
        # Add some data
        FollowedArtist.objects.create(user=self.user, artist=self.artist)

        stats = ArtistService.get_artist_statistics(str(self.artist.id))

        self.assertIn("total_albums", stats)
        self.assertIn("total_songs", stats)
        self.assertIn("total_plays", stats)
        self.assertIn("followers_count", stats)
        self.assertIn("monthly_listeners", stats)
        self.assertIn("verified", stats)
        self.assertEqual(stats["followers_count"], 1)
