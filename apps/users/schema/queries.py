import graphene
from django.core.exceptions import PermissionDenied, ValidationError
from .types import UserType, UserPreferencesType
from graphql import GraphQLError
from django.contrib.auth import get_user_model, authenticate
from ..models import UserPreferences

User = get_user_model()


class UserQueryMixin:
    """User-related GraphQL queries"""

    me = graphene.Field(UserType, description="Get the currently authenticated user")

    user = graphene.Field(
        UserType,
        id=graphene.ID(),
        username=graphene.String(),
        description="Get user by ID or username",
    )

    user_preferences = graphene.Field(
        UserPreferencesType, description="Get current user preferences"
    )

    search_users = graphene.List(
        UserType,
        query=graphene.String(required=True),
        limit=graphene.Int(default_value=20),
        description="Search users by username or name",
    )

    def resolve_me(self, info):
        """Resolve the currently authenticated user"""
        user = info.context.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required to access this resource.")
        return user

    def resolve_user(self, info, id=None, username=None):
        """Get user by ID or username"""
        if id:
            try:
                return User.objects.get(id=id)
            except User.DoesNotExist:
                raise GraphQLError(f"User with ID {id} not found")
        elif username:
            try:
                return User.objects.get(username=username)
            except User.DoesNotExist:
                raise GraphQLError(f"User with username '{username}' not found")

        raise GraphQLError("Either 'id' or 'username' must be provided")

    def resolve_user_preferences(self, info):
        """Get current user preferences"""
        user = info.context.user
        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in")

        preferences, _ = UserPreferences.objects.get_or_create(user=user)
        return preferences

    def resolve_search_users(self, info, query, limit=20):
        """Search users by username or name"""
        from django.db.models import Q

        users = User.objects.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )[:limit]

        return users
