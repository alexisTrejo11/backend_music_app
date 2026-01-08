import logging
from typing import Dict
from apps.core.logging.logging_utils import log_execution_time, audit_log, LoggingMixin
from django.core.exceptions import ValidationError
from slugify import slugify
from apps.artists.models import Artist
from apps.music.models import Album, Genre, Song
from apps.interactions.models import LikedSong, ListeningHistory
from django.db.models import Q, Count, F
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger("apps.music.services")


class SongService:
    """Service layer for Song business logic"""

    @log_execution_time("performance")
    @staticmethod
    def create_song(data: Dict, audio_file=None, user=None):
        """
        Create a new song with validation and async processing
        """
        logger.info("Starting song creation", extra={"data_keys": list(data.keys())})

        try:
            title = data.get("title", "").strip()
            artist_id = data.get("artist_id")
            album_id = data.get("album_id")
            duration = data.get("duration")

            if not title:
                logger.warning("Song creation failed: missing title")
                raise ValidationError("Song title is required")

            if not duration or duration <= 0:
                logger.warning(
                    "Song creation failed: invalid duration",
                    extra={"duration": duration},
                )
                raise ValidationError("Valid duration is required")

            # Log de auditoría
            audit_log("SONG_CREATE_START", user=user, object_type="Song", title=title)

            try:
                artist = Artist.objects.get(id=artist_id)
                logger.debug(
                    "Artist found",
                    extra={"artist_id": artist_id, "artist_name": artist.name},
                )
            except Artist.DoesNotExist:
                logger.error("Artist not found", extra={"artist_id": artist_id})
                raise ValidationError(f"Artist with ID {artist_id} not found")

            try:
                album = Album.objects.get(id=album_id)
                logger.debug(
                    "Album found",
                    extra={"album_id": album_id, "album_title": album.title},
                )
            except Album.DoesNotExist:
                logger.error("Album not found", extra={"album_id": album_id})
                raise ValidationError(f"Album with ID {album_id} not found")

            if album.artist_id != artist_id:
                logger.warning(
                    "Artist mismatch",
                    extra={
                        "album_artist": album.artist_id,
                        "provided_artist": artist_id,
                    },
                )
                raise ValidationError("Artist must match album's artist")

            # Create unique slug
            slug = slugify(title)
            original_slug = slug
            counter = 1
            while Song.objects.filter(album=album, slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1

            logger.debug("Generated slug", extra={"title": title, "slug": slug})

            # Get genre if provided
            genre = None
            genre_id = data.get("genre_id")
            if genre_id:
                try:
                    genre = Genre.objects.get(id=genre_id)
                    logger.debug(
                        "Genre found",
                        extra={"genre_id": genre_id, "genre_name": genre.name},
                    )
                except Genre.DoesNotExist:
                    logger.warning("Genre not found", extra={"genre_id": genre_id})
                    raise ValidationError(f"Genre with ID {genre_id} not found")

            # Create song
            song = Song.objects.create(
                title=title,
                slug=slug,
                artist=artist,
                album=album,
                duration=duration,
                track_number=data.get("track_number", 1),
                disc_number=data.get("disc_number", 1),
                isrc=data.get("isrc", ""),
                lyrics=data.get("lyrics", ""),
                is_explicit=data.get("is_explicit", False),
                genre=genre,
                mood=data.get("mood", ""),
                language=data.get("language", ""),
                is_processed=False,
                processing_status="PENDING",
                created_by=user,
            )

            # Add featured artists
            featured_artist_ids = data.get("featured_artist_ids", [])
            if featured_artist_ids:
                featured_artists = Artist.objects.filter(id__in=featured_artist_ids)
                song.featured_artists.set(featured_artists)
                logger.debug(
                    "Featured artists added", extra={"count": len(featured_artist_ids)}
                )

            # Handle audio_file upload and processing
            task_id = None
            if audio_file:
                logger.info(
                    "Starting audio file processing",
                    extra={"song_id": str(song.id), "file_name": audio_file.name},
                )
                task_id = SongService.process_audio_file_async(
                    song, audio_file, user.id if user else None
                )

            # Log de auditoría exitoso
            audit_log(
                "SONG_CREATE_SUCCESS",
                user=user,
                object_type="Song",
                object_id=str(song.id),
                title=title,
                artist=artist.name,
                album=album.title,
            )

            logger.info(
                "Song created successfully",
                extra={"song_id": str(song.id), "title": title, "task_id": task_id},
            )

            return song, task_id

        except ValidationError as e:
            # Log de auditoría fallido
            audit_log(
                "SONG_CREATE_FAILED",
                user=user,
                object_type="Song",
                error=str(e),
                title=data.get("title"),
                artist_id=data.get("artist_id"),
            )

            logger.error(
                "Song creation failed",
                exc_info=e,
                extra={"title": data.get("title"), "error": str(e)},
            )
            raise

        except Exception as e:
            logger.critical(
                "Unexpected error in song creation", exc_info=e, extra={"data": data}
            )
            raise

    @staticmethod
    def process_audio_file_async(song: Song, audio_file, user_id=None):
        """
        Subir archivo de audio y disparar procesamiento asíncrono
        """
        try:
            from apps.music.services.file_upload_service import FileUploadService
            from apps.music.tasks import process_audio_file_task

            logger.info(
                "Processing audio file",
                extra={"song_id": str(song.id), "file_size": audio_file.size},
            )

            # Validar archivo
            FileUploadService.validate_audio_file(audio_file)
            logger.debug("Audio file validated")

            # Subir a almacenamiento
            file_path = f"audio/songs/{song.id}/{audio_file.name}"
            file_url = FileUploadService.upload_to_s3(audio_file, file_path)

            # Actualizar song con URL
            song.audio_file = file_url
            song.save(update_fields=["audio_file"])

            logger.debug(
                "Audio file uploaded",
                extra={"file_path": file_path, "file_url": file_url},
            )

            # Disparar tarea asíncrona
            task = process_audio_file_task.delay(
                song_id=str(song.id), audio_file_path=file_path
            )

            logger.info(
                "Audio processing task dispatched",
                extra={"song_id": str(song.id), "task_id": task.id},
            )

            return task.id

        except Exception as e:
            logger.error(
                "Error processing audio file",
                exc_info=e,
                extra={"song_id": str(song.id)},
            )
            raise

    @staticmethod
    def update_song(song_id: str, data: Dict) -> Song:
        """
        Update an existing song

        Args:
            song_id: ID of the song to update
            data: Dictionary with updated data from UpdateSongInput

        Returns:
            Song: Updated song instance
        """
        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            raise ValidationError(f"Song with ID {song_id} not found")

        # Update basic fields
        updateable_fields = ["lyrics", "is_explicit", "mood", "language"]
        for field in updateable_fields:
            if field in data:
                setattr(song, field, data[field])

        # Handle title update
        if "title" in data:
            new_title = data["title"].strip()
            if not new_title:
                raise ValidationError("Song title cannot be empty")
            song.title = new_title
            song.slug = slugify(new_title)

        # Update genre
        if "genre_id" in data:
            try:
                genre = Genre.objects.get(id=data["genre_id"])
                song.genre = genre
            except Genre.DoesNotExist:
                raise ValidationError(f"Genre with ID {data['genre_id']} not found")

        # Update featured artists
        if "featured_artist_ids" in data:
            featured_artists = Artist.objects.filter(id__in=data["featured_artist_ids"])
            song.featured_artists.set(featured_artists)

        song.save()
        return song

    @staticmethod
    def delete_song(song_id: str) -> bool:
        """
        Delete a song

        Args:
            song_id: ID of the song to delete

        Returns:
            bool: True if deleted successfully
        """
        try:
            song = Song.objects.get(id=song_id)
            album = song.album
            song.delete()

            # Update album stats after deletion
            # AlbumService.update_album_stats(album)

            return True
        except Song.DoesNotExist:
            raise ValidationError(f"Song with ID {song_id} not found")

    @staticmethod
    def like_song(user, song_id: str) -> Dict:
        """
        Like a song

        Args:
            user: User instance
            song_id: ID of the song to like

        Returns:
            Dict with success, message, and song
        """
        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            raise ValidationError(f"Song with ID {song_id} not found")

        # Check if already liked
        like, created = LikedSong.objects.get_or_create(user=user, song=song)

        if not created:
            return {
                "success": False,
                "message": "You already liked this song",
                "song": song,
            }

        # Update like count
        song.like_count = LikedSong.objects.filter(song=song).count()
        song.save(update_fields=["like_count"])

        return {"success": True, "message": "Song liked successfully", "song": song}

    @staticmethod
    def unlike_song(user, song_id: str) -> Dict:
        """
        Unlike a song

        Args:
            user: User instance
            song_id: ID of the song to unlike

        Returns:
            Dict with success and message
        """
        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            raise ValidationError(f"Song with ID {song_id} not found")

        # Try to delete the like
        deleted, _ = LikedSong.objects.filter(user=user, song=song).delete()

        if deleted == 0:
            return {"success": False, "message": "You have not liked this song"}

        # Update like count
        song.like_count = LikedSong.objects.filter(song=song).count()
        song.save(update_fields=["like_count"])

        return {"success": True, "message": "Song unliked successfully"}

    @staticmethod
    def track_play(user, song_id: str, source=None, source_id=None):
        """
        Track a song play in listening history

        Args:
            user: User instance
            song_id: ID of the song played
            source: Source of play (playlist, album, radio, search)
            source_id: ID of the source
        """
        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            raise ValidationError(f"Song with ID {song_id} not found")

        # Create listening history entry
        ListeningHistory.objects.create(
            user=user,
            song=song,
            duration_played=song.duration,  # Assume full play for now
            completed=True,
            source=source or "",
            source_id=source_id or "",
        )

        # Update play count (TODO: this asynchronously in production with Celery)
        song.play_count = F("play_count") + 1
        song.save(update_fields=["play_count"])

        # Refresh to get actual value
        song.refresh_from_db()

    @staticmethod
    def search_songs(
        query: str, genre=None, is_explicit=None, limit: int = 20, offset: int = 0
    ):
        """
        Search songs with filters

        Args:
            query: Search query
            genre: Genre filter (slug)
            is_explicit: Filter by explicit content
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of Song instances
        """
        qs = Song.objects.select_related("artist", "album", "genre").filter(
            Q(title__icontains=query)
            | Q(artist__name__icontains=query)
            | Q(album__title__icontains=query)
            | Q(lyrics__icontains=query)
        )

        # Apply filters
        if genre:
            qs = qs.filter(genre__slug=genre)

        if is_explicit is not None:
            qs = qs.filter(is_explicit=is_explicit)

        return qs.distinct()[offset : offset + limit]

    @staticmethod
    def get_trending_songs(time_range: str = "WEEK", limit: int = 50):
        """
        Get trending songs based on recent plays

        Args:
            time_range: One of DAY, WEEK, MONTH, YEAR
            limit: Maximum number of songs

        Returns:
            List of Song instances
        """
        time_filters = {
            "DAY": timezone.now() - timedelta(days=1),
            "WEEK": timezone.now() - timedelta(weeks=1),
            "MONTH": timezone.now() - timedelta(days=30),
            "YEAR": timezone.now() - timedelta(days=365),
        }

        time_filter = time_filters.get(time_range, time_filters["WEEK"])

        # Get songs with most recent plays
        trending = Song.objects.annotate(
            recent_plays=Count("plays", filter=Q(plays__played_at__gte=time_filter))
        ).order_by("-recent_plays", "-play_count")[:limit]

        return trending

    @staticmethod
    def get_recommended_songs(user, limit: int = 30):
        """
        Get personalized song recommendations

        Args:
            user: User instance
            limit: Maximum number of recommendations

        Returns:
            List of Song instances
        """
        # Simple recommendation based on:
        # 1. User's liked songs genres
        # 2. Artists user follows
        # 3. Similar songs to what they've listened to

        # Get user's favorite genres from liked songs
        liked_songs = LikedSong.objects.filter(user=user).select_related("song__genre")
        favorite_genres = set()
        for like in liked_songs[:50]:  # Last 50 likes
            if like.song.genre:
                favorite_genres.add(like.song.genre_id)

        # Get followed artists
        from apps.interactions.models import FollowedArtist

        followed_artists = FollowedArtist.objects.filter(user=user).values_list(
            "artist_id", flat=True
        )

        # Build recommendation query
        recommendations = (
            Song.objects.exclude(id__in=liked_songs.values_list("song_id", flat=True))
            .filter(Q(genre_id__in=favorite_genres) | Q(artist_id__in=followed_artists))
            .distinct()
            .order_by("-play_count", "?")[:limit]
        )

        return recommendations
