from django.db import models
from apps.core.models import TimestampedModel


class ListeningHistory(TimestampedModel):
    """Track user listening history"""

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="listening_history"
    )
    song = models.ForeignKey(
        "music.Song", on_delete=models.CASCADE, related_name="plays"
    )
    played_at = models.DateTimeField(auto_now_add=True)

    # Playback details
    duration_played = models.PositiveIntegerField()  # seconds actually played
    completed = models.BooleanField(default=False)  # played >30 seconds
    source = models.CharField(max_length=50, blank=True)  # playlist, album, radio, etc.
    source_id = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "listening_history"
        ordering = ["-played_at"]
        indexes = [
            models.Index(fields=["user", "-played_at"]),
            models.Index(fields=["song", "-played_at"]),
        ]


class LikedSong(TimestampedModel):
    """User's liked songs"""

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="liked_songs"
    )
    song = models.ForeignKey(
        "music.Song", on_delete=models.CASCADE, related_name="likes"
    )

    class Meta:
        db_table = "liked_songs"
        unique_together = [["user", "song"]]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]


class FollowedArtist(TimestampedModel):
    """Artists followed by users"""

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="followed_artists"
    )
    artist = models.ForeignKey(
        "artists.Artist", on_delete=models.CASCADE, related_name="followers"
    )

    class Meta:
        db_table = "followed_artists"
        unique_together = [["user", "artist"]]


class SavedAlbum(TimestampedModel):
    """Albums saved by users"""

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="saved_albums"
    )
    album = models.ForeignKey(
        "music.Album", on_delete=models.CASCADE, related_name="saves"
    )

    class Meta:
        db_table = "saved_albums"
        unique_together = [["user", "album"]]


class Review(TimestampedModel):
    """User reviews for albums or songs"""

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="reviews"
    )
    album = models.ForeignKey(
        "music.Album",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reviews",
    )
    song = models.ForeignKey(
        "music.Song",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reviews",
    )

    rating = models.PositiveSmallIntegerField()  # 1-5 stars
    comment = models.TextField(blank=True)

    # Engagement
    helpful_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "reviews"
        indexes = [
            models.Index(fields=["album", "-created_at"]),
            models.Index(fields=["song", "-created_at"]),
        ]

    def __str__(self):
        target = self.album.title if self.album else "unknown song"
        return f"Review by {self.user.username} on {target}"
