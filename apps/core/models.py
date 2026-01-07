from django.db import models
from django.conf import settings
import uuid


class SystemLog(models.Model):
    """Modelo to store system logs in the database"""

    LEVEL_CHOICES = [
        ("DEBUG", "Debug"),
        ("INFO", "Info"),
        ("WARNING", "Warning"),
        ("ERROR", "Error"),
        ("CRITICAL", "Critical"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    logger = models.CharField(max_length=255)
    message = models.TextField()
    module = models.CharField(max_length=255)
    function = models.CharField(max_length=255)
    line = models.IntegerField()
    path = models.TextField()
    exception = models.TextField(blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    request_method = models.CharField(max_length=10, null=True, blank=True)
    request_path = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.level}] {self.logger}: {self.message[:50]}"


class TimestampedModel(models.Model):
    """Abstract base model with created and updated timestamps"""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Abstract base model with UUID primary key"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
