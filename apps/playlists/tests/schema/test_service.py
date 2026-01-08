from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.playlists.models import Playlist, PlaylistFollower, PlaylistSong
from apps.playlists.services import PlaylistService
from apps.music.models import Album, Song
from apps.artists.models import Artist

User = get_user_model()


class PlaylistServiceTestCase(TestCase):
    """Unit tests for PlaylistService"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="testpass"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass"
        )

        self.artist = Artist.objects.create(name="Artist", slug="artist")
        self.album = Album.objects.create(
            title="Album", slug="album", artist=self.artist, release_date="2024-01-01"
        )
        self.song1 = Song.objects.create(
            title="Song 1",
            slug="song-1",
            artist=self.artist,
            album=self.album,
            duration=210,
        )
        self.song2 = Song.objects.create(
            title="Song 2",
            slug="song-2",
            artist=self.artist,
            album=self.album,
            duration=180,
        )
        self.song3 = Song.objects.create(
            title="Song 3",
            slug="song-3",
            artist=self.artist,
            album=self.album,
            duration=150,
        )

        self.playlist = Playlist.objects.create(
            name="Base Playlist",
            slug="base-playlist",
            user=self.user1,
            is_public=True,
        )
        self.private_playlist = Playlist.objects.create(
            name="Private",
            slug="private",
            user=self.user1,
            is_public=False,
        )

    def test_create_playlist_success(self):
        payload = {"name": "My Playlist", "description": "desc"}
        playlist = PlaylistService.create_playlist(self.user1, payload)

        self.assertEqual(playlist.name, "My Playlist")
        self.assertEqual(playlist.slug, "my-playlist")
        self.assertEqual(playlist.user, self.user1)

    def test_create_playlist_requires_name(self):
        with self.assertRaises(ValidationError):
            PlaylistService.create_playlist(self.user1, {"name": ""})

    def test_update_playlist_success(self):
        updated = PlaylistService.update_playlist(
            self.user1,
            str(self.playlist.id),
            {"name": "Renamed", "description": "new desc", "is_public": False},
        )

        self.assertEqual(updated.name, "Renamed")
        self.assertFalse(updated.is_public)
        self.assertEqual(updated.description, "new desc")

    def test_update_playlist_not_owner(self):
        with self.assertRaises(PermissionDenied):
            PlaylistService.update_playlist(
                self.user2, str(self.playlist.id), {"name": "Nope"}
            )

    def test_delete_playlist_success(self):
        self.assertTrue(
            PlaylistService.delete_playlist(self.user1, str(self.playlist.id))
        )
        self.assertFalse(Playlist.objects.filter(id=self.playlist.id).exists())

    def test_delete_editorial_playlist(self):
        editorial = Playlist.objects.create(
            name="Editorial",
            slug="editorial",
            user=self.user1,
            is_editorial=True,
        )
        with self.assertRaises(PermissionDenied):
            PlaylistService.delete_playlist(self.user1, str(editorial.id))

    def test_add_song_appends(self):
        song_entry = PlaylistService.add_song_to_playlist(
            self.user1, str(self.playlist.id), str(self.song1.id)
        )
        self.assertEqual(song_entry.position, 1)
        self.playlist.refresh_from_db()
        self.assertEqual(self.playlist.total_duration, 210)

    def test_add_song_at_position(self):
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song1, added_by=self.user1, position=1
        )
        PlaylistService.add_song_to_playlist(
            self.user1, str(self.playlist.id), str(self.song2.id), position=1
        )
        positions = list(
            PlaylistSong.objects.filter(playlist=self.playlist)
            .order_by("position")
            .values_list("position", flat=True)
        )
        self.assertEqual(positions, [1, 2])

    def test_add_duplicate_song(self):
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song1, added_by=self.user1, position=1
        )
        with self.assertRaises(ValidationError):
            PlaylistService.add_song_to_playlist(
                self.user1, str(self.playlist.id), str(self.song1.id)
            )

    def test_remove_song_reorders(self):
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song1, added_by=self.user1, position=1
        )
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song2, added_by=self.user1, position=2
        )
        PlaylistService.remove_song_from_playlist(
            self.user1, str(self.playlist.id), str(self.song1.id)
        )
        remaining = PlaylistSong.objects.get(song=self.song2)
        self.assertEqual(remaining.position, 1)

    def test_reorder_songs(self):
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song1, added_by=self.user1, position=1
        )
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song2, added_by=self.user1, position=2
        )
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song3, added_by=self.user1, position=3
        )
        PlaylistService.reorder_songs(
            self.user1, str(self.playlist.id), str(self.song3.id), new_position=1
        )
        ordered_titles = list(
            PlaylistSong.objects.filter(playlist=self.playlist)
            .order_by("position")
            .values_list("song__title", flat=True)
        )
        self.assertEqual(ordered_titles[0], "Song 3")

    def test_follow_playlist(self):
        result = PlaylistService.follow_playlist(self.user2, str(self.playlist.id))
        self.assertTrue(result["success"])
        self.assertEqual(PlaylistFollower.objects.count(), 1)
        playlist = Playlist.objects.get(id=self.playlist.id)
        self.assertEqual(playlist.follower_count, 1)

    def test_follow_private_playlist(self):
        with self.assertRaises(PermissionDenied):
            PlaylistService.follow_playlist(self.user2, str(self.private_playlist.id))

    def test_follow_own_playlist(self):
        result = PlaylistService.follow_playlist(self.user1, str(self.playlist.id))
        self.assertFalse(result["success"])

    def test_unfollow_playlist(self):
        PlaylistFollower.objects.create(user=self.user2, playlist=self.playlist)
        response = PlaylistService.unfollow_playlist(self.user2, str(self.playlist.id))
        self.assertTrue(response["success"])
        self.assertEqual(PlaylistFollower.objects.count(), 0)

    def test_duplicate_playlist_copies_songs(self):
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song1, added_by=self.user1, position=1
        )
        duplicate = PlaylistService.duplicate_playlist(
            self.user2, str(self.playlist.id)
        )
        self.assertEqual(duplicate.user, self.user2)
        self.assertEqual(PlaylistSong.objects.filter(playlist=duplicate).count(), 1)

    def test_add_collaborator_requires_collaborative(self):
        with self.assertRaises(ValidationError):
            PlaylistService.add_collaborator(
                self.user1, str(self.playlist.id), str(self.user2.id)
            )

    def test_add_collaborator_success(self):
        self.playlist.is_collaborative = True
        self.playlist.save()
        PlaylistService.add_collaborator(
            self.user1, str(self.playlist.id), str(self.user2.id)
        )
        self.assertTrue(
            PlaylistFollower.objects.filter(
                user=self.user2, playlist=self.playlist
            ).exists()
        )

    def test_remove_collaborator_not_owner(self):
        self.playlist.is_collaborative = True
        self.playlist.save()
        PlaylistFollower.objects.create(user=self.user2, playlist=self.playlist)
        with self.assertRaises(PermissionDenied):
            PlaylistService.remove_collaborator(
                self.user2, str(self.playlist.id), str(self.user2.id)
            )

    def test_remove_collaborator_success(self):
        self.playlist.is_collaborative = True
        self.playlist.save()
        PlaylistFollower.objects.create(user=self.user2, playlist=self.playlist)
        self.assertTrue(
            PlaylistService.remove_collaborator(
                self.user1, str(self.playlist.id), str(self.user2.id)
            )
        )

    def test_search_playlists(self):
        PlaylistService.create_playlist(
            self.user1, {"name": "Match", "is_public": True}
        )
        results = PlaylistService.search_playlists("Match")
        self.assertGreaterEqual(len(results), 1)

    def test_get_playlist_stats(self):
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song1, added_by=self.user1, position=1
        )
        PlaylistSong.objects.create(
            playlist=self.playlist, song=self.song2, added_by=self.user1, position=2
        )
        PlaylistService._update_playlist_stats(self.playlist)
        self.playlist.refresh_from_db()
        stats = PlaylistService.get_playlist_stats(self.playlist)
        self.assertEqual(stats["songs_count"], 2)
        self.assertEqual(stats["follower_count"], self.playlist.follower_count)
        self.assertEqual(stats["total_duration"], self.playlist.total_duration)
