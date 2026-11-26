from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from musicfy.database import MusicDatabase


class MusicDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.home = Path(self.temp_dir.name)
        self.home_patch = patch.object(Path, "home", return_value=self.home)
        self.home_patch.start()
        self.database = MusicDatabase()

    def tearDown(self) -> None:
        self.database.close()
        self.home_patch.stop()
        self.temp_dir.cleanup()

    def test_album_artist_and_genre_groups(self) -> None:
        self.database.save_track({
            "path": "/music/one.flac",
            "title": "First Song",
            "artist": "The Example",
            "album": "Blue Skies",
            "genre": "Jazz",
            "duration": 180,
            "cover_path": "/covers/blue.png",
        })
        self.database.save_track({
            "path": "/music/two.flac",
            "title": "Second Song",
            "artist": "The Example",
            "album": "Blue Skies",
            "genre": "Jazz",
            "duration": 200,
            "cover_path": "/covers/blue.png",
        })
        self.database.save_track({
            "path": "/music/three.flac",
            "title": "Third Song",
            "artist": "Another Artist",
            "album": "Green Fields",
            "genre": "Ambient",
            "duration": 220,
        })

        albums = self.database.list_albums()
        artists = self.database.list_artists()
        genres = self.database.list_genres()

        self.assertEqual(len(albums), 2)
        self.assertEqual(len(artists), 2)
        self.assertEqual(len(genres), 2)

        blue_skies = next(album for album in albums if album["album"] == "Blue Skies")
        self.assertEqual(blue_skies["track_count"], 2)
        self.assertEqual(blue_skies["cover_path"], "/covers/blue.png")

        album_tracks = self.database.tracks_for_collection("album", "Blue Skies", "The Example")
        self.assertEqual([track["title"] for track in album_tracks], ["First Song", "Second Song"])
        artist_tracks = self.database.tracks_for_collection("artist", "The Example")
        self.assertEqual(len(artist_tracks), 2)
        genre_tracks = self.database.tracks_for_collection("genre", "Ambient")
        self.assertEqual(len(genre_tracks), 1)

    def test_favorites_and_history_are_preserved(self) -> None:
        self.database.save_track({
            "path": "/music/favorite.mp3",
            "title": "Favorite",
            "artist": "Artist",
            "album": "Album",
            "duration": 100,
        })
        self.database.set_favorite("/music/favorite.mp3", True)
        self.database.mark_played("/music/favorite.mp3")

        self.assertEqual(len(self.database.list_tracks("favorites")), 1)
        self.assertEqual(len(self.database.list_tracks("history")), 1)

    def test_old_database_is_migrated_without_losing_tracks(self) -> None:
        self.database.close()
        db_path = self.home / ".musicfy" / "library.sqlite3"
        connection = sqlite3.connect(db_path)
        try:
            # Build an actual legacy schema on the same temporary database file.
            connection.execute("DROP TABLE IF EXISTS tracks")
            connection.execute(
                """
                CREATE TABLE tracks (
                    path TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL DEFAULT 'Artista desconocido',
                    album TEXT NOT NULL DEFAULT 'Álbum desconocido',
                    duration REAL NOT NULL DEFAULT 0,
                    is_favorite INTEGER NOT NULL DEFAULT 0,
                    last_played TEXT
                )
                """
            )
            connection.execute(
                "INSERT INTO tracks(path,title,artist,album,duration) VALUES(?,?,?,?,?)",
                ("/music/legacy.mp3", "Legacy track", "Legacy artist", "Legacy album", 90),
            )
            connection.commit()
        finally:
            connection.close()

        self.database = MusicDatabase()
        tracks = self.database.list_tracks()
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0]["title"], "Legacy track")
        self.assertEqual(tracks[0]["genre"], "Sin género")
        self.assertIsNone(tracks[0]["cover_path"])

    def test_playlist_storage_order_and_library_metadata(self) -> None:
        self.database.save_track({
            "path": "/music/library-song.mp3",
            "title": "Tagged title",
            "artist": "Tagged artist",
            "album": "Tagged album",
            "duration": 180,
        })
        playlist_id = self.database.create_playlist("Road trip")
        self.database.save_playlist_tracks(
            playlist_id,
            [
                {
                    "path": "/music/library-song.mp3",
                    "title": "M3U title",
                    "artist": "M3U artist",
                    "duration": 100,
                },
                {
                    "path": "/external/missing-song.mp3",
                    "title": "Offline song",
                    "artist": "Guest",
                    "duration": 90,
                },
            ],
        )

        playlists = self.database.list_playlists()
        self.assertEqual(len(playlists), 1)
        self.assertEqual(playlists[0]["track_count"], 2)

        tracks = self.database.get_playlist_tracks(playlist_id)
        self.assertEqual([item["title"] for item in tracks], ["Tagged title", "Offline song"])
        self.assertEqual(tracks[0]["artist"], "Tagged artist")
        self.assertEqual(tracks[1]["path"], "/external/missing-song.mp3")

        self.database.remove_from_playlist(playlist_id, 0)
        remaining = self.database.get_playlist_tracks(playlist_id)
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["title"], "Offline song")
        self.assertEqual(remaining[0]["playlist_position"], 0)

        self.database.delete_playlist(playlist_id)
        self.assertEqual(self.database.list_playlists(), [])



if __name__ == "__main__":
    unittest.main()
