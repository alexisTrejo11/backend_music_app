import graphene
from graphene_django import DjangoObjectType
from ..models import UserPreferences
from django.contrib.auth import get_user_model

User = get_user_model()


class UserPreferencesType(DjangoObjectType):
    class Meta:
        model = UserPreferences
        fields = (
            "explicit_content",
            "autoplay",
            "audio_quality",
            "language",
            "private_session",
        )


class UserType(DjangoObjectType):
    """User type with computed fields"""

    followers_count = graphene.Int()
    following_count = graphene.Int()
    playlists_count = graphene.Int()
    is_premium = graphene.Boolean()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "profile_image",
            "bio",
            "birth_date",
            "country",
            "is_artist",
            "is_verified",
            "subscription_type",
            "created_at",
            "updated_at",
        )
        interfaces = (graphene.relay.Node,)

    def resolve_followers_count(self, info):
        """Get followers count - to be implemented with social features"""

        # TODO: Implement actual logic to count followers
        return 0

    def resolve_following_count(self, info):
        """Get following count"""
        from apps.interactions.models import FollowedArtist

        return FollowedArtist.objects.filter(user=self).count()

    def resolve_playlists_count(self, info):
        """Get public playlists count"""
        from apps.playlists.models import Playlist

        return Playlist.objects.filter(user=self, is_public=True).count()

    def resolve_is_premium(self, info):
        """Check if user has premium subscription"""
        return self.subscription_type in ["premium", "family", "student"]


class AuthPayloadType(graphene.ObjectType):
    """Authentication response payload"""

    access_token = graphene.String()
    refresh_token = graphene.String()
    user = graphene.Field(UserType)
