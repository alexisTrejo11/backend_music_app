from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import Artist, ArtistMember


@receiver(pre_save, sender=Artist)
def create_artist_slug(sender, instance, **kwargs):
    """Create slug from artist name before saving"""
    if not instance.slug:
        instance.slug = slugify(instance.name)

        # Ensure uniqueness
        counter = 1
        original_slug = instance.slug
        while (
            Artist.objects.filter(slug=instance.slug).exclude(id=instance.id).exists()
        ):
            instance.slug = f"{original_slug}-{counter}"
            counter += 1


@receiver(post_save, sender=Artist)
def artist_post_save(sender, instance, created, **kwargs):
    """Actions after artist is saved"""
    if created:
        # Send welcome notification to staff
        pass

    # Clear related caches
    from django.core.cache import cache

    cache.delete_pattern(f"trending_artists_*")
    cache.delete_pattern(f"similar_artists_{instance.id}_*")


@receiver(post_save, sender=ArtistMember)
def member_post_save(sender, instance, created, **kwargs):
    """Actions after artist member is saved"""
    if created:
        # Notify artist followers about new member
        pass


@receiver(post_delete, sender=Artist)
def artist_post_delete(sender, instance, **kwargs):
    """Actions after artist is deleted"""
    # Clear caches
    from django.core.cache import cache

    cache.delete_pattern(f"similar_artists_{instance.id}_*")
