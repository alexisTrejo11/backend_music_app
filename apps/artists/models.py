from django.db import models
from apps.core.models import TimestampedModel


class Artist(TimestampedModel):
    """Music artist or band"""

    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(unique=True, max_length=255)
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to="artists/", blank=True, null=True)
    cover_image = models.ImageField(upload_to="artists/covers/", blank=True, null=True)
    verified = models.BooleanField(default=False)
    monthly_listeners = models.PositiveIntegerField(default=0)

    # Social links
    website = models.URLField(blank=True)
    spotify_url = models.URLField(blank=True)
    instagram = models.CharField(max_length=100, blank=True)
    twitter = models.CharField(max_length=100, blank=True)

    # Metadata
    country = models.CharField(max_length=2, blank=True)
    genres = models.ManyToManyField("music.Genre", related_name="artists", blank=True)

    class Meta:
        db_table = "artists"
        ordering = ["-monthly_listeners", "name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.name


class ArtistMember(models.Model):
    """Members of a band/group"""

    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="members")
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=100)  # vocalist, guitarist, etc.
    image = models.ImageField(upload_to="artist_members/", blank=True, null=True)
    join_date = models.DateField(null=True, blank=True)
    leave_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "artist_members"
