import graphene
from ..types import ListeningHistoryType
from django.core.exceptions import PermissionDenied
from ...models import ListeningHistory
from apps.core.decorators import get_authenticated_user, auth_required


class ListeningHistoryQueries:
    listening_history = graphene.List(
        ListeningHistoryType,
        limit=graphene.Int(default_value=50),
        offset=graphene.Int(default_value=0),
        description="Get current user's listening history",
    )

    recent_plays = graphene.List(
        ListeningHistoryType,
        limit=graphene.Int(default_value=20),
        description="Get current user's recent plays",
    )

    @auth_required
    def resolve_listening_history(self, info, limit=50, offset=0):
        """Get user's listening history"""
        user = get_authenticated_user(info)

        return (
            ListeningHistory.objects.filter(user=user)
            .select_related("song__artist", "song__album")
            .order_by("-played_at")[offset : offset + limit]
        )

    @auth_required
    def resolve_recent_plays(self, info, limit=20):
        """Get user's recent plays"""
        user = get_authenticated_user(info)

        return (
            ListeningHistory.objects.filter(user=user)
            .select_related("song__artist", "song__album")
            .order_by("-played_at")[:limit]
        )
