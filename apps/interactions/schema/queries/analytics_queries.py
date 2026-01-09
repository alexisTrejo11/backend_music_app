import graphene
from apps.core.decorators import auth_required, get_authenticated_user
from ...services.analytics_service import AnalyticsService
from ..types import ListeningStatsType, TopArtistType, TopSongType, TopGenreType


class AnalyticsQueries:
    user_listening_stats = graphene.Field(
        ListeningStatsType,
        time_range=graphene.String(
            default_value="MONTH"
        ),  # WEEK, MONTH, YEAR, ALL_TIME
        description="Get comprehensive listening statistics",
    )

    user_top_artists = graphene.List(
        TopArtistType,
        time_range=graphene.String(default_value="MONTH"),
        limit=graphene.Int(default_value=10),
        description="Get user's top artists",
    )

    user_top_songs = graphene.List(
        TopSongType,
        time_range=graphene.String(default_value="MONTH"),
        limit=graphene.Int(default_value=50),
        description="Get user's top songs",
    )

    user_top_genres = graphene.List(
        TopGenreType,
        time_range=graphene.String(default_value="MONTH"),
        description="Get user's top genres",
    )

    @auth_required
    def resolve_user_listening_stats(self, info, time_range="MONTH"):
        """Get comprehensive listening statistics"""
        user = get_authenticated_user(info)

        return AnalyticsService.get_listening_stats(user, time_range)

    @auth_required
    def resolve_user_top_artists(self, info, time_range="MONTH", limit=10):
        """Get user's top artists"""
        user = get_authenticated_user(info)

        return AnalyticsService.get_top_artists(user, time_range, limit)

    @auth_required
    def resolve_user_top_songs(self, info, time_range="MONTH", limit=50):
        """Get user's top songs"""
        user = get_authenticated_user(info)

        return AnalyticsService.get_top_songs(user, time_range, limit)

    @auth_required
    def resolve_user_top_genres(self, info, time_range="MONTH"):
        """Get user's top genres"""
        user = get_authenticated_user(info)

        return AnalyticsService.get_top_genres(user, time_range)
