from django.db import models
from apps.core.models import TimestampedModel


class Playlist(TimestampedModel):
    """User or editorial playlist"""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="playlists"
    )
    cover_image = models.ImageField(upload_to="playlists/", blank=True, null=True)

    # Settings
    is_public = models.BooleanField(default=True)
    is_collaborative = models.BooleanField(default=False)
    is_editorial = models.BooleanField(default=False)

    # Stats
    follower_count = models.PositiveIntegerField(default=0)
    total_duration = models.PositiveIntegerField(default=0)  # Total duration in seconds

    def __str__(self):
        return f"{self.name} by {self.user.username}"


class PlaylistSong(TimestampedModel):
    """Song in a playlist with order"""

    playlist = models.ForeignKey(
        Playlist, on_delete=models.CASCADE, related_name="songs"
    )
    song = models.ForeignKey(
        "music.Song", on_delete=models.CASCADE, related_name="playlist_entries"
    )

    added_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True)

    position = models.PositiveIntegerField()

    class Meta:
        db_table = "playlist_songs"
        ordering = ["position"]
        unique_together = [["playlist", "song", "position"]]
        indexes = [
            models.Index(fields=["playlist", "position"]),
        ]


class PlaylistFollower(TimestampedModel):
    """Users following playlists"""

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="followed_playlists"
    )
    playlist = models.ForeignKey(
        Playlist, on_delete=models.CASCADE, related_name="followers"
    )

    class Meta:
        db_table = "playlist_followers"
        unique_together = [["user", "playlist"]]
