import graphene
from graphql import GraphQLError
from django.core.exceptions import PermissionDenied
from apps.interactions.models import FollowedArtist as Follow
from django.contrib.auth import get_user_model
from ..models import Artist
from .types import ArtistType

User = get_user_model()


class FollowArtist(graphene.Mutation):
    """Follow an artist"""

    class Arguments:
        artist_id = graphene.ID(required=True)

    success = graphene.Boolean()
    artist = graphene.Field(ArtistType)

    @classmethod
    def mutate(cls, root, info, artist_id):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in to follow artists")

        try:
            artist = Artist.objects.get(id=artist_id)

            # Check if already following
            follow, created = Follow.objects.get_or_create(user=user, artist=artist)

            if not created:
                # Already following
                return FollowArtist(success=False, artist=artist)

            # Update artist's monthly listeners (increment)
            artist.monthly_listeners += 1
            artist.save()

            return FollowArtist(success=True, artist=artist)

        except Artist.DoesNotExist:
            raise GraphQLError(f"Artist with ID {artist_id} not found")


class UnfollowArtist(graphene.Mutation):
    """Unfollow an artist"""

    class Arguments:
        artist_id = graphene.ID(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info, artist_id):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in to unfollow artists")

        try:
            artist = Artist.objects.get(id=artist_id)

            # Delete follow if exists
            deleted, _ = Follow.objects.filter(user=user, artist=artist).delete()

            if deleted > 0:
                # Update artist's monthly listeners (decrement)
                artist.monthly_listeners = max(0, artist.monthly_listeners - 1)
                artist.save()
                return UnfollowArtist(success=True)

            return UnfollowArtist(success=False)

        except Artist.DoesNotExist:
            raise GraphQLError(f"Artist with ID {artist_id} not found")


class CreateArtist(graphene.Mutation):
    """Create a new artist (admin/verified users only)"""

    class Arguments:
        name = graphene.String(required=True)
        bio = graphene.String()
        profile_image = graphene.String()  # Base64 or URL
        cover_image = graphene.String()  # Base64 or URL
        genres = graphene.List(graphene.String)
        country = graphene.String()
        website = graphene.String()
        spotify_url = graphene.String()
        instagram = graphene.String()
        twitter = graphene.String()

    artist = graphene.Field(ArtistType)

    @classmethod
    def mutate(cls, root, info, name, **kwargs):
        user = info.context.user

        # Check permissions
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        # In a real app, check if user has permission to create artists
        # For now, allow staff users only
        if not (user.is_staff or user.is_superuser):
            raise PermissionDenied("You don't have permission to create artists")

        # Create slug from name
        from django.utils.text import slugify

        slug = slugify(name)

        # Ensure slug is unique
        counter = 1
        original_slug = slug
        while Artist.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1

        # Create artist
        artist = Artist.objects.create(
            name=name,
            slug=slug,
            bio=kwargs.get("bio", ""),
            country=kwargs.get("country", ""),
            website=kwargs.get("website", ""),
            spotify_url=kwargs.get("spotify_url", ""),
            instagram=kwargs.get("instagram", ""),
            twitter=kwargs.get("twitter", ""),
        )

        # Handle images (in a real app, you'd process base64 or URLs)
        # This is a simplified version

        # Add genres
        genres = kwargs.get("genres", [])
        if genres:
            from apps.music.models import Genre

            for genre_name in genres:
                genre, _ = Genre.objects.get_or_create(name=genre_name)
                artist.genres.add(genre)

        return CreateArtist(artist=artist)


class UpdateArtist(graphene.Mutation):
    """Update an existing artist"""

    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()
        bio = graphene.String()
        profile_image = graphene.String()
        cover_image = graphene.String()
        genres = graphene.List(graphene.String)
        country = graphene.String()
        website = graphene.String()
        spotify_url = graphene.String()
        instagram = graphene.String()
        twitter = graphene.String()
        verified = graphene.Boolean()

    artist = graphene.Field(ArtistType)

    @classmethod
    def mutate(cls, root, info, id, **kwargs):
        user = info.context.user

        if not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        try:
            artist = Artist.objects.get(id=id)

            # Check permissions (staff or artist owner in future)
            if not (user.is_staff or user.is_superuser):
                raise PermissionDenied(
                    "You don't have permission to update this artist"
                )

            # Update fields
            update_fields = [
                "name",
                "bio",
                "country",
                "website",
                "spotify_url",
                "instagram",
                "twitter",
                "verified",
            ]

            for field in update_fields:
                if field in kwargs:
                    setattr(artist, field, kwargs[field])

            # Handle slug if name changed
            if "name" in kwargs:
                from django.utils.text import slugify

                artist.slug = slugify(kwargs["name"])

            # Update genres
            if "genres" in kwargs:
                artist.genres.clear()
                from apps.music.models import Genre

                for genre_name in kwargs["genres"]:
                    genre, _ = Genre.objects.get_or_create(name=genre_name)
                    artist.genres.add(genre)

            artist.save()
            return UpdateArtist(artist=artist)

        except Artist.DoesNotExist:
            raise GraphQLError(f"Artist with ID {id} not found")


class ArtistMutation(graphene.ObjectType):
    """Artist-related GraphQL mutations"""

    follow_artist = FollowArtist.Field()
    unfollow_artist = UnfollowArtist.Field()
    create_artist = CreateArtist.Field()
    update_artist = UpdateArtist.Field()
