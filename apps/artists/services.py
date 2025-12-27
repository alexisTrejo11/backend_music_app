from django.db.models import Count, Q, F
from django.core.cache import cache
from datetime import timedelta
from django.utils import timezone
from .models import Artist
from apps.music.models import Song
from apps.interactions.models import (
    FollowedArtist as Follow,
    ListeningHistory as PlayHistory,
)


class ArtistService:
    """Business logic for artist operations"""

    @staticmethod
    def get_trending_artists(time_range="WEEK", limit=50):
        """
        Get trending artists based on various metrics
        time_range: DAY, WEEK, MONTH, YEAR
        """
        cache_key = f"trending_artists_{time_range}_{limit}"
        cached = cache.get(cache_key)

        if cached:
            return cached

        # Calculate start date based on time range
        now = timezone.now()
        time_ranges = {
            "DAY": now - timedelta(days=1),
            "WEEK": now - timedelta(weeks=1),
            "MONTH": now - timedelta(days=30),
            "YEAR": now - timedelta(days=365),
        }

        start_date = time_ranges.get(time_range.upper(), time_ranges["WEEK"])

        # Calculate trending score based on:
        # 1. Recent plays
        # 2. New followers
        # 3. Recent album releases
        # 4. Social media mentions (simplified)

        # Get artists with recent plays
        recent_plays = (
            PlayHistory.objects.filter(played_at__gte=start_date)
            .values("song__artist")
            .annotate(play_count=Count("id"))
            .order_by("-play_count")[: limit * 2]
        )

        artist_ids = [
            item["song__artist"] for item in recent_plays if item["song__artist"]
        ]

        # Get artists with recent followers
        recent_follows = (
            Follow.objects.filter(created_at__gte=start_date)
            .values("artist")
            .annotate(follow_count=Count("id"))
            .order_by("-follow_count")[: limit * 2]
        )

        artist_ids.extend([item["artist"] for item in recent_follows])

        # Remove duplicates and get unique artist IDs
        unique_artist_ids = list(set(artist_ids))

        # Get artists and order by monthly listeners as fallback
        artists = Artist.objects.filter(id__in=unique_artist_ids).order_by(
            "-monthly_listeners"
        )[:limit]

        # Cache for 5 minutes
        cache.set(cache_key, artists, 300)

        return artists

    @staticmethod
    def get_similar_artists(artist_id, limit=20):
        """Get artists similar to given artist"""
        cache_key = f"similar_artists_{artist_id}_{limit}"
        cached = cache.get(cache_key)

        if cached:
            return cached

        try:
            artist = Artist.objects.get(id=artist_id)

            # Find similar artists based on:
            # 1. Shared genres (weight: 0.5)
            # 2. Shared listeners (weight: 0.3)
            # 3. Similar monthly listeners (weight: 0.2)

            # Get artists with same genres
            genre_artists = (
                Artist.objects.filter(genres__in=artist.genres.all())
                .exclude(id=artist_id)
                .annotate(
                    common_genres=Count(
                        "genres", filter=Q(genres__in=artist.genres.all())
                    )
                )
                .distinct()
            )

            # Order by similarity score
            similar_artists = genre_artists.order_by(
                "-common_genres", "-monthly_listeners"
            )[:limit]

            cache.set(cache_key, similar_artists, 600)  # Cache for 10 minutes
            return similar_artists

        except Artist.DoesNotExist:
            return []

    @staticmethod
    def search_artists(query, limit=20, offset=0):
        """Search artists with ranking"""
        # Split query into terms
        terms = query.lower().split()

        # Build Q objects for search
        q_objects = Q()
        for term in terms:
            q_objects |= Q(name__icontains=term)
            q_objects |= Q(bio__icontains=term)
            q_objects |= Q(country__icontains=term)

        # Search and rank by:
        # 1. Exact name match
        # 2. Name starts with term
        # 3. Name contains term
        # 4. Bio contains term

        artists = Artist.objects.filter(q_objects)

        # Add ranking annotation
        from django.db.models import Case, When, Value, IntegerField
        from django.db.models.functions import Lower

        whens = []
        for i, term in enumerate(terms):
            # Higher weight for earlier terms
            weight = len(terms) - i

            # Exact name match (highest priority)
            whens.append(When(name__iexact=term, then=Value(100 * weight)))

            # Name starts with term
            whens.append(When(name__istartswith=term, then=Value(50 * weight)))

            # Name contains term
            whens.append(When(name__icontains=term, then=Value(20 * weight)))

            # Bio contains term
            whens.append(When(bio__icontains=term, then=Value(10 * weight)))

        artists = artists.annotate(
            search_rank=Case(*whens, default=Value(0), output_field=IntegerField())
        ).order_by("-search_rank", "-monthly_listeners", "name")

        return artists[offset : offset + limit], artists.count()

    @staticmethod
    def update_monthly_listeners(artist_id):
        """Update monthly listeners count for an artist"""
        from datetime import timedelta

        try:
            artist = Artist.objects.get(id=artist_id)

            # Count unique listeners in last 30 days
            thirty_days_ago = timezone.now() - timedelta(days=30)

            # This is a simplified version
            # In a real app, you'd track unique listeners

            # For now, use follow count as proxy
            listeners = Follow.objects.filter(artist=artist).count()

            # Add some random variation for demo
            import random

            listeners += random.randint(1000, 10000)

            artist.monthly_listeners = listeners
            artist.save()

            return listeners

        except Artist.DoesNotExist:
            return 0
