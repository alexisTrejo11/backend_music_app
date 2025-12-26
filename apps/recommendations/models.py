from django.db import models
from apps.core.models import TimestampedModel


class UserTaste(models.Model):
    """User taste profile for recommendations"""

    user = models.OneToOneField(
        "users.User", on_delete=models.CASCADE, related_name="taste"
    )
    favorite_genres = models.ManyToManyField("music.Genre", related_name="fans")
    top_artists = models.ManyToManyField("artists.Artist", related_name="top_listeners")

    # Computed features
    energy_preference = models.FloatField(default=0.5)
    danceability_preference = models.FloatField(default=0.5)
    valence_preference = models.FloatField(default=0.5)

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_taste"


class Radio(TimestampedModel):
    """Generated radio stations based on seed"""

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="radios"
    )
    name = models.CharField(max_length=255)

    # Seeds (at least one required)
    seed_artist = models.ForeignKey(
        "artists.Artist", on_delete=models.SET_NULL, null=True, blank=True
    )
    seed_song = models.ForeignKey(
        "music.Song", on_delete=models.SET_NULL, null=True, blank=True
    )
    seed_genre = models.ForeignKey(
        "music.Genre", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table = "radios"
