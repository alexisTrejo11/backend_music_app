from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene.test import Client
from graphql import GraphQLError

from apps.artists.models import Artist
from apps.music.models import Genre
from apps.interactions.models import FollowedArtist
from config.schema import schema

User = get_user_model()


class ArtistQueriesTestCase(TestCase):
    """Test cases for Artist GraphQL queries"""

    def setUp(self):
        """Set up test data"""
        self.client = Client(schema)

        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create genres
        self.genre_rock = Genre.objects.create(name="Rock", slug="rock")
        self.genre_pop = Genre.objects.create(name="Pop", slug="pop")

        # Create test artists
        self.artist1 = Artist.objects.create(
            name="Test Artist 1",
            slug="test-artist-1",
            bio="Bio for artist 1",
            country="US",
            monthly_listeners=1000,
            verified=True,
        )
        self.artist1.genres.add(self.genre_rock)

        self.artist2 = Artist.objects.create(
            name="Test Artist 2",
            slug="test-artist-2",
            bio="Bio for artist 2",
            country="UK",
            monthly_listeners=2000,
        )
        self.artist2.genres.add(self.genre_pop)

        self.artist3 = Artist.objects.create(
            name="Popular Artist",
            slug="popular-artist",
            bio="Very popular artist",
            monthly_listeners=5000,
        )
        self.artist3.genres.add(self.genre_rock)

    def test_query_single_artist_by_id(self):
        """Test querying a single artist by ID"""
        query = """
            query GetArtist($id: ID!) {
                artist(id: $id) {
                    id
                    name
                    slug
                    bio
                    country
                    monthlyListeners
                    verified
                }
            }
        """

        result = self.client.execute(query, variables={"id": str(self.artist1.id)})

        self.assertIsNone(result.get("errors"))
        artist_data = result["data"]["artist"]
        self.assertEqual(artist_data["name"], "Test Artist 1")
        self.assertEqual(artist_data["slug"], "test-artist-1")
        self.assertEqual(artist_data["bio"], "Bio for artist 1")
        self.assertEqual(artist_data["country"], "US")
        self.assertEqual(artist_data["monthlyListeners"], 1000)
        self.assertTrue(artist_data["verified"])

    def test_query_single_artist_by_slug(self):
        """Test querying a single artist by slug"""
        query = """
            query GetArtist($slug: String!) {
                artist(slug: $slug) {
                    id
                    name
                    slug
                }
            }
        """

        result = self.client.execute(query, variables={"slug": "test-artist-1"})

        self.assertIsNone(result.get("errors"))
        artist_data = result["data"]["artist"]
        self.assertEqual(artist_data["name"], "Test Artist 1")
        self.assertEqual(artist_data["slug"], "test-artist-1")

    def test_query_artist_not_found(self):
        """Test querying non-existent artist returns error"""
        query = """
            query GetArtist($id: ID!) {
                artist(id: $id) {
                    id
                    name
                }
            }
        """

        result = self.client.execute(query, variables={"id": "99999"})

        self.assertIsNotNone(result.get("errors"))
        self.assertIn("not found", str(result["errors"]))

    def test_query_all_artists(self):
        """Test querying all artists"""
        query = """
            query {
                allArtists {
                    edges {
                        node {
                            id
                            name
                            slug
                        }
                    }
                }
            }
        """

        result = self.client.execute(query)

        self.assertIsNone(result.get("errors"))
        edges = result["data"]["allArtists"]["edges"]
        self.assertEqual(len(edges), 3)

    def test_search_artists_by_name(self):
        """Test searching artists by name"""
        query = """
            query SearchArtists($query: String!) {
                searchArtists(query: $query) {
                    id
                    name
                    slug
                }
            }
        """

        result = self.client.execute(query, variables={"query": "Test Artist"})

        self.assertIsNone(result.get("errors"))
        artists = result["data"]["searchArtists"]
        self.assertEqual(len(artists), 2)  # artist1 and artist2
        names = [a["name"] for a in artists]
        self.assertIn("Test Artist 1", names)
        self.assertIn("Test Artist 2", names)

    def test_search_artists_by_bio(self):
        """Test searching artists by bio"""
        query = """
            query SearchArtists($query: String!) {
                searchArtists(query: $query) {
                    id
                    name
                }
            }
        """

        result = self.client.execute(query, variables={"query": "popular"})

        self.assertIsNone(result.get("errors"))
        artists = result["data"]["searchArtists"]
        self.assertEqual(len(artists), 1)
        self.assertEqual(artists[0]["name"], "Popular Artist")

    def test_search_artists_with_limit(self):
        """Test searching artists with limit"""
        query = """
            query SearchArtists($query: String!, $limit: Int!) {
                searchArtists(query: $query, limit: $limit) {
                    id
                    name
                }
            }
        """

        result = self.client.execute(query, variables={"query": "Artist", "limit": 1})

        self.assertIsNone(result.get("errors"))
        artists = result["data"]["searchArtists"]
        self.assertEqual(len(artists), 1)

    def test_trending_artists(self):
        """Test getting trending artists"""
        # Add followers to make artist3 trending
        user2 = User.objects.create_user(username="user2", email="user2@example.com")
        FollowedArtist.objects.create(user=self.user, artist=self.artist3)
        FollowedArtist.objects.create(user=user2, artist=self.artist3)

        query = """
            query {
                trendingArtists(timeRange: "WEEK", limit: 5) {
                    id
                    name
                    monthlyListeners
                }
            }
        """

        result = self.client.execute(query)

        self.assertIsNone(result.get("errors"))
        trending = result["data"]["trendingArtists"]
        self.assertGreater(len(trending), 0)

    def test_similar_artists(self):
        """Test getting similar artists based on genres"""
        query = """
            query SimilarArtists($artistId: ID!, $limit: Int!) {
                similarArtists(artistId: $artistId, limit: $limit) {
                    id
                    name
                }
            }
        """

        result = self.client.execute(
            query, variables={"artistId": str(self.artist1.id), "limit": 5}
        )

        self.assertIsNone(result.get("errors"))
        similar = result["data"]["similarArtists"]

        # artist3 has same genre (Rock) as artist1
        similar_names = [a["name"] for a in similar]
        self.assertIn("Popular Artist", similar_names)
        # artist1 should not be in its own similar list
        self.assertNotIn("Test Artist 1", similar_names)
        FollowedArtist.objects.create(user=self.user, artist=self.artist1)
        FollowedArtist.objects.create(user=self.user, artist=self.artist2)

        query = """
            query {
                followedArtists {
                    id
                    name
                }
            }
        """

        # Mock authenticated context
        class MockContext:
            def __init__(self, user):
                self.user = user

        context = MockContext(self.user)
        result = self.client.execute(query, context_value=context)

        self.assertIsNone(result.get("errors"))
        followed = result["data"]["followedArtists"]
        self.assertEqual(len(followed), 2)
        followed_names = [a["name"] for a in followed]
        self.assertIn("Test Artist 1", followed_names)
        self.assertIn("Test Artist 2", followed_names)

    def test_followed_artists_unauthenticated(self):
        """Test getting followed artists without authentication fails"""
        query = """
            query {
                followedArtists {
                    id
                    name
                }
            }
        """

        # Mock unauthenticated context
        class MockContext:
            def __init__(self):
                self.user = type("AnonymousUser", (), {"is_authenticated": False})()

        context = MockContext()
        result = self.client.execute(query, context_value=context)

        self.assertIsNotNone(result.get("errors"))
        self.assertIn("logged in", str(result["errors"]).lower())

    def test_artist_with_genres(self):
        """Test querying artist with genres relationship"""
        query = """
            query GetArtist($id: ID!) {
                artist(id: $id) {
                    id
                    name
                    genres {
                        id
                        name
                        slug
                    }
                }
            }
        """

        result = self.client.execute(query, variables={"id": str(self.artist1.id)})

        self.assertIsNone(result.get("errors"))
        artist_data = result["data"]["artist"]
        genres = artist_data["genres"]
        self.assertEqual(len(genres), 1)
        self.assertEqual(genres[0]["name"], "Rock")

    def test_query_without_required_parameter(self):
        """Test querying artist without required parameter fails"""
        query = """
            query {
                artist {
                    id
                    name
                }
            }
        """

        result = self.client.execute(query)

        self.assertIsNotNone(result.get("errors"))
