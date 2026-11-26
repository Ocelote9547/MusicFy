from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class MusicDatabase:
    """SQLite-backed library with safe, additive schema migrations."""

    def __init__(self) -> None:
        data_dir = Path.home() / ".musicfy"
        data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = data_dir / "library.sqlite3"
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        with self.connection:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tracks (
                    path TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL DEFAULT 'Artista desconocido',
                    album TEXT NOT NULL DEFAULT 'Álbum desconocido',
                    genre TEXT NOT NULL DEFAULT 'Sin género',
                    duration REAL NOT NULL DEFAULT 0,
                    cover_path TEXT,
                    is_favorite INTEGER NOT NULL DEFAULT 0,
                    last_played TEXT
                )
                """
            )

            # Keep existing MusicFy databases usable without deleting user data.
            columns = {
                row["name"]
                for row in self.connection.execute("PRAGMA table_info(tracks)")
            }
            migrations = {
                "genre": "ALTER TABLE tracks ADD COLUMN genre TEXT NOT NULL DEFAULT 'Sin género'",
                "cover_path": "ALTER TABLE tracks ADD COLUMN cover_path TEXT",
            }
            for column, statement in migrations.items():
                if column not in columns:
                    self.connection.execute(statement)

    def save_track(self, track: dict[str, Any]) -> None:
        values = {
            "path": str(track["path"]),
            "title": str(track.get("title") or Path(track["path"]).stem),
            "artist": str(track.get("artist") or "Artista desconocido"),
            "album": str(track.get("album") or "Álbum desconocido"),
            "genre": str(track.get("genre") or "Sin género"),
            "duration": float(track.get("duration") or 0),
            "cover_path": track.get("cover_path"),
        }
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO tracks(
                    path, title, artist, album, genre, duration, cover_path
                )
                VALUES(
                    :path, :title, :artist, :album, :genre, :duration, :cover_path
                )
                ON CONFLICT(path) DO UPDATE SET
                    title=excluded.title,
                    artist=excluded.artist,
                    album=excluded.album,
                    genre=excluded.genre,
                    duration=excluded.duration,
                    cover_path=COALESCE(excluded.cover_path, tracks.cover_path)
                """,
                values,
            )

    def list_tracks(self, mode: str = "all") -> list[dict[str, Any]]:
        if mode == "favorites":
            query = (
                "SELECT * FROM tracks WHERE is_favorite=1 "
                "ORDER BY artist COLLATE NOCASE, album COLLATE NOCASE, title COLLATE NOCASE"
            )
        elif mode == "history":
            query = (
                "SELECT * FROM tracks WHERE last_played IS NOT NULL "
                "ORDER BY last_played DESC LIMIT 100"
            )
        else:
            query = (
                "SELECT * FROM tracks "
                "ORDER BY artist COLLATE NOCASE, album COLLATE NOCASE, title COLLATE NOCASE"
            )
        rows = self.connection.execute(query).fetchall()
        return [dict(row) for row in rows]

    def list_albums(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT
                COALESCE(NULLIF(TRIM(album), ''), 'Álbum desconocido') AS album,
                COALESCE(NULLIF(TRIM(artist), ''), 'Artista desconocido') AS artist,
                COUNT(*) AS track_count,
                SUM(duration) AS total_duration,
                MAX(cover_path) AS cover_path
            FROM tracks
            GROUP BY LOWER(TRIM(album)), LOWER(TRIM(artist))
            ORDER BY artist COLLATE NOCASE, album COLLATE NOCASE
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def list_artists(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT
                COALESCE(NULLIF(TRIM(artist), ''), 'Artista desconocido') AS artist,
                COUNT(*) AS track_count,
                COUNT(DISTINCT album) AS album_count,
                MAX(cover_path) AS cover_path
            FROM tracks
            GROUP BY LOWER(TRIM(artist))
            ORDER BY artist COLLATE NOCASE
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def list_genres(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT
                COALESCE(NULLIF(TRIM(genre), ''), 'Sin género') AS genre,
                COUNT(*) AS track_count,
                MAX(cover_path) AS cover_path
            FROM tracks
            GROUP BY LOWER(TRIM(genre))
            ORDER BY genre COLLATE NOCASE
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def tracks_for_collection(
        self,
        kind: str,
        value: str,
        artist: str | None = None,
    ) -> list[dict[str, Any]]:
        if kind == "album":
            rows = self.connection.execute(
                """
                SELECT * FROM tracks
                WHERE LOWER(TRIM(album))=LOWER(TRIM(?))
                  AND LOWER(TRIM(artist))=LOWER(TRIM(?))
                ORDER BY title COLLATE NOCASE
                """,
                (value, artist or ""),
            ).fetchall()
        elif kind == "artist":
            rows = self.connection.execute(
                """
                SELECT * FROM tracks
                WHERE LOWER(TRIM(artist))=LOWER(TRIM(?))
                ORDER BY album COLLATE NOCASE, title COLLATE NOCASE
                """,
                (value,),
            ).fetchall()
        elif kind == "genre":
            rows = self.connection.execute(
                """
                SELECT * FROM tracks
                WHERE LOWER(TRIM(genre))=LOWER(TRIM(?))
                ORDER BY artist COLLATE NOCASE, album COLLATE NOCASE, title COLLATE NOCASE
                """,
                (value,),
            ).fetchall()
        else:
            return []
        return [dict(row) for row in rows]

    def set_favorite(self, path: str, favorite: bool) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE tracks SET is_favorite=? WHERE path=?",
                (1 if favorite else 0, path),
            )

    def mark_played(self, path: str) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE tracks SET last_played=CURRENT_TIMESTAMP WHERE path=?",
                (path,),
            )

    def remove_track(self, path: str) -> None:
        with self.connection:
            self.connection.execute("DELETE FROM tracks WHERE path=?", (path,))

    def close(self) -> None:
        self.connection.close()
