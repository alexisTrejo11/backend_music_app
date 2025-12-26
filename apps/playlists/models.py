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
    is_editorial = models.BooleanField(default=False)  # Create your models here.

    def __str__(self):
        return f"{self.name} by {self.user.username}"
