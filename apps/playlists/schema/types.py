import graphene
from graphene_django import DjangoObjectType
from ..models import Playlist, PlaylistFollower, PlaylistSong


class PlaylistSongType(DjangoObjectType):
    class Meta:
        model = PlaylistSong
        fields = ("id", "song", "added_by", "position", "created_at")


class PlaylistFollowerType(DjangoObjectType):
    class Meta:
        model = PlaylistFollower
        fields = ("id", "user", "playlist", "created_at")
        interfaces = (graphene.relay.Node,)


class PlaylistType(DjangoObjectType):
    """Type for Playlist with computed fields"""

    songs_count = graphene.Int()
    is_following = graphene.Boolean()
    is_owner = graphene.Boolean()
    can_edit = graphene.Boolean()
    songs = graphene.List(PlaylistSongType)

    class Meta:
        model = Playlist
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "user",
            "cover_image",
            "is_public",
            "is_collaborative",
            "is_editorial",
            "follower_count",
            "total_duration",
            "created_at",
            "updated_at",
        )
        interfaces = (graphene.relay.Node,)

    def resolve_songs_count(self, info):
        """Get total number of songs in playlist"""
        return self.songs.count()

    def resolve_is_following(self, info):
        """Check if current user is following this playlist"""
        user = info.context.user
        if user.is_authenticated:
            return PlaylistFollower.objects.filter(user=user, playlist=self).exists()
        return False

    def resolve_is_owner(self, info):
        """Check if current user owns this playlist"""
        user = info.context.user
        if user.is_authenticated:
            return self.user_id == user.id
        return False

    def resolve_can_edit(self, info):
        """Check if current user can edit this playlist"""
        user = info.context.user
        if not user.is_authenticated:
            return False

        # Owner can always edit
        if self.user_id == user.id:
            return True

        # Collaborative playlists can be edited by followers
        # Maybe could create a collaborator logic later instead of all followers
        if self.is_collaborative:
            return PlaylistFollower.objects.filter(user=user, playlist=self).exists()

        return False

    def resolve_songs(self, info):
        """Get all songs in playlist ordered by position"""
        return (
            self.songs.select_related("song__artist", "song__album", "added_by")
            .all()
            .order_by("position")
        )
