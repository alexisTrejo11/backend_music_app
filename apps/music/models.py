from django.db import models
from apps.core.models import TimestampedModel


class Genre(models.Model):
    """Music genre"""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subgenres",
    )

    class Meta:
        db_table = "genres"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Album(TimestampedModel):
    """Music album"""

    ALBUM_TYPES = [
        ("album", "Album"),
        ("single", "Single"),
        ("ep", "EP"),
        ("compilation", "Compilation"),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    artist = models.ForeignKey(
        "artists.Artist", on_delete=models.CASCADE, related_name="albums"
    )
    album_type = models.CharField(max_length=20, choices=ALBUM_TYPES, default="album")
    release_date = models.DateField()
    cover_image = models.ImageField(upload_to="albums/")
    description = models.TextField(blank=True)
    label = models.CharField(max_length=255, blank=True)

    # Stats
    total_duration = models.PositiveIntegerField(default=0)  # in seconds
    total_tracks = models.PositiveIntegerField(default=0)
    play_count = models.PositiveIntegerField(default=0)

    # Metadata
    is_explicit = models.BooleanField(default=False)
    copyright = models.CharField(max_length=255, blank=True)
    upc = models.CharField(max_length=20, blank=True)  # Universal Product Code

    class Meta:
        db_table = "albums"
        ordering = ["-release_date"]
        unique_together = [["artist", "slug"]]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["release_date"]),
            models.Index(fields=["artist", "release_date"]),
        ]

    def __str__(self):
        return f"{self.artist.name} - {self.title}"


class Song(TimestampedModel):
    """Music track"""

    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255)
    artist = models.ForeignKey(
        "artists.Artist", on_delete=models.CASCADE, related_name="songs"
    )
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="songs")
    featured_artists = models.ManyToManyField(
        "artists.Artist", related_name="featured_songs", blank=True
    )

    # Audio
    audio_file = models.FileField(upload_to="songs/")
    audio_url = models.URLField(blank=True)  # For external storage (S3, etc)
    duration = models.PositiveIntegerField()  # in seconds

    # Metadata
    track_number = models.PositiveIntegerField(default=1)
    disc_number = models.PositiveIntegerField(default=1)
    isrc = models.CharField(
        max_length=12, blank=True
    )  # International Standard Recording Code
    lyrics = models.TextField(blank=True)
    is_explicit = models.BooleanField(default=False)

    # Classification
    genre = models.ForeignKey(
        Genre, on_delete=models.SET_NULL, null=True, related_name="songs"
    )
    mood = models.CharField(max_length=50, blank=True)  # happy, sad, energetic, etc.
    language = models.CharField(max_length=10, blank=True)

    # Stats
    play_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)

    # Audio features (for recommendations)
    tempo = models.FloatField(null=True, blank=True)  # BPM
    key = models.CharField(max_length=5, blank=True)  # Musical key
    energy = models.FloatField(null=True, blank=True)  # 0.0 to 1.0
    danceability = models.FloatField(null=True, blank=True)  # 0.0 to 1.0
    valence = models.FloatField(null=True, blank=True)  # 0.0 to 1.0 (positivity)

    class Meta:
        db_table = "songs"
        ordering = ["album", "disc_number", "track_number"]
        unique_together = [["album", "slug"]]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["artist", "title"]),
            models.Index(fields=["play_count"]),
        ]

    def __str__(self):
        return f"{self.artist.name} - {self.title}"
