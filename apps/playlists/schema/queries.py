import graphene
from graphql import GraphQLError
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from .types import PlaylistType
from ..models import Playlist, PlaylistFollower

# TODO: Add logging after fix logging issues
User = get_user_model()


class PlaylistQuery(graphene.ObjectType):
    """Playlist-related GraphQL queries"""

    playlist = graphene.Field(
        PlaylistType,
        id=graphene.ID(),
        slug=graphene.String(),
        description="Get a single playlist by ID or slug",
    )

    my_playlists = graphene.List(
        PlaylistType, description="Get all playlists created by current user"
    )

    user_playlists = graphene.List(
        PlaylistType,
        user_id=graphene.ID(),
        username=graphene.String(),
        include_private=graphene.Boolean(default_value=False),
        description="Get playlists by a specific user",
    )

    followed_playlists = graphene.List(
        PlaylistType, description="Get playlists followed by current user"
    )

    featured_playlists = graphene.List(
        PlaylistType,
        limit=graphene.Int(default_value=20),
        description="Get featured/editorial playlists",
    )

    search_playlists = graphene.List(
        PlaylistType,
        query=graphene.String(required=True),
        limit=graphene.Int(default_value=20),
        offset=graphene.Int(default_value=0),
        description="Search playlists by name or description",
    )

    trending_playlists = graphene.List(
        PlaylistType,
        limit=graphene.Int(default_value=20),
        description="Get trending playlists based on follower count",
    )

    def resolve_playlist(self, info, id=None, slug=None):
        """Get single playlist by ID or slug"""
        if id:
            try:
                playlist = Playlist.objects.select_related("user").get(id=id)
            except Playlist.DoesNotExist:
                raise GraphQLError(f"Playlist with ID {id} not found")
        elif slug:
            try:
                playlist = Playlist.objects.select_related("user").get(slug=slug)
            except Playlist.DoesNotExist:
                raise GraphQLError(f"Playlist with slug '{slug}' not found")
        else:
            raise GraphQLError("Either 'id' or 'slug' must be provided")

        # Check permissions for private playlists
        user = info.context.user
        if not playlist.is_public:
            if not user.is_authenticated or (playlist.user_id != user.id):
                raise PermissionDenied("This playlist is private")

        return playlist

    def resolve_my_playlists(self, info):
        """Get current user's playlists"""
        user = info.context.user
        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in")

        return Playlist.objects.filter(user=user).order_by("-created_at")

    def resolve_user_playlists(
        self, info, user_id=None, username=None, include_private=False
    ):
        """Get playlists by a specific user"""
        current_user = info.context.user

        # Get target user
        if user_id:
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise GraphQLError(f"User with ID {user_id} not found")
        elif username:
            try:
                target_user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise GraphQLError(f"User with username '{username}' not found")
        else:
            raise GraphQLError("Either 'user_id' or 'username' must be provided")

        # Build query
        qs = Playlist.objects.filter(user=target_user)

        # Filter by privacy
        if (
            not include_private
            or not current_user.is_authenticated
            or current_user.id != target_user.id
        ):
            qs = qs.filter(is_public=True)

        return qs.order_by("-created_at")

    def resolve_followed_playlists(self, info):
        """Get playlists followed by current user"""
        user = info.context.user
        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in")

        followed_ids = PlaylistFollower.objects.filter(user=user).values_list(
            "playlist_id", flat=True
        )
        return Playlist.objects.filter(id__in=followed_ids).order_by("-created_at")

    def resolve_featured_playlists(self, info, limit=20):
        """Get featured/editorial playlists"""
        return Playlist.objects.filter(is_public=True, is_editorial=True).order_by(
            "-created_at"
        )[:limit]

    def resolve_search_playlists(self, info, query, limit=20, offset=0):
        """Search playlists by name or description"""
        qs = Playlist.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query), is_public=True
        )
        return qs.order_by("-created_at")[offset : offset + limit]

    def resolve_trending_playlists(self, info, limit=20):
        """Get trending playlists based on follower count"""
        return Playlist.objects.filter(is_public=True).order_by(
            "-follower_count", "-created_at"
        )[:limit]
