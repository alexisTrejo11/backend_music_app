from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from apps.music.models import Song, Album
from apps.music.services import AlbumService


@receiver(post_save, sender=Song)
def update_album_on_song_change(sender, instance, created, **kwargs):
    """
    Update album stats when a song is created or updated
    """
    if instance.album:
        transaction.on_commit(
            lambda: AlbumService.update_album_stats(instance.album.id)
        )


@receiver(post_delete, sender=Song)
def update_album_on_song_delete(sender, instance, **kwargs):
    """
    Update album stats when a song is deleted
    """
    if instance.album:
        transaction.on_commit(
            lambda: AlbumService.update_album_stats(instance.album.id)
        )


@receiver(post_save, sender=Album)
def set_default_album_slug(sender, instance, created, **kwargs):
    """
    Ensure album has a slug
    """
    if created and not instance.slug:
        from slugify import slugify

        instance.slug = slugify(instance.title)
        instance.save(update_fields=["slug"])
