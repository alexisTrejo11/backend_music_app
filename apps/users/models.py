from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import TimestampedModel


class User(AbstractUser, TimestampedModel):
    """Extended user model"""

    email = models.EmailField(unique=True, db_index=True)
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=2, blank=True)  # ISO country code
    is_artist = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    # Subscription/Premium features
    subscription_type = models.CharField(
        max_length=20,
        choices=[
            ("free", "Free"),
            ("premium", "Premium"),
            ("family", "Family"),
            ("student", "Student"),
        ],
        default="free",
    )
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["username"]),
        ]

    def __str__(self):
        return self.username


class UserPreferences(models.Model):
    """User listening preferences and settings"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="preferences"
    )
    explicit_content = models.BooleanField(default=True)
    autoplay = models.BooleanField(default=True)
    audio_quality = models.CharField(
        max_length=20,
        choices=[
            ("low", "Low (96kbps)"),
            ("normal", "Normal (160kbps)"),
            ("high", "High (320kbps)"),
        ],
        default="normal",
    )
    language = models.CharField(max_length=10, default="en")
    private_session = models.BooleanField(default=False)

    class Meta:
        db_table = "user_preferences"
