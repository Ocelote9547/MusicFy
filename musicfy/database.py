from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class MusicDatabase:
    """SQLite-backed music library and playlist store."""

    def __init__(self) -> None:
        data_dir = Path.home() / ".musicfy"
        data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = data_dir / "library.sqlite3"
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
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

            # Additive migrations preserve libraries from earlier MusicFy builds.
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

            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS playlist_tracks (
                    playlist_id INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    path TEXT NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    artist TEXT NOT NULL DEFAULT '',
                    duration REAL NOT NULL DEFAULT 0,
                    PRIMARY KEY (playlist_id, position),
                    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE
                )
                """
            )
            self.connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_playlist_tracks_path ON playlist_tracks(path)"
            )

    def save_track(self, track: dict[str, Any]) -> None:
        self.save_tracks([track])

    def save_tracks(self, tracks: list[dict[str, Any]]) -> None:
        if not tracks:
            return
        values = [
            {
                "path": str(track["path"]),
                "title": str(track.get("title") or Path(track["path"]).stem),
                "artist": str(track.get("artist") or "Artista desconocido"),
                "album": str(track.get("album") or "Álbum desconocido"),
                "genre": str(track.get("genre") or "Sin género"),
                "duration": float(track.get("duration") or 0),
                "cover_path": track.get("cover_path"),
            }
            for track in tracks
            if track.get("path")
        ]
        if not values:
            return
        with self.connection:
            self.connection.executemany(
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
        return [dict(row) for row in self.connection.execute(query).fetchall()]

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

    # ------------------------------------------------------------------
    # Playlists
    # ------------------------------------------------------------------
    def create_playlist(self, name: str) -> int:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("El nombre de la playlist no puede estar vacío.")
        with self.connection:
            cursor = self.connection.execute(
                "INSERT INTO playlists(name) VALUES(?)",
                (clean_name,),
            )
        return int(cursor.lastrowid)

    def get_playlist(self, playlist_id: int) -> dict[str, Any] | None:
        row = self.connection.execute(
            """
            SELECT p.id, p.name, p.created_at, p.updated_at,
                   COUNT(pt.position) AS track_count
            FROM playlists p
            LEFT JOIN playlist_tracks pt ON pt.playlist_id=p.id
            WHERE p.id=?
            GROUP BY p.id
            """,
            (playlist_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_playlists(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT p.id, p.name, p.created_at, p.updated_at,
                   COUNT(pt.position) AS track_count
            FROM playlists p
            LEFT JOIN playlist_tracks pt ON pt.playlist_id=p.id
            GROUP BY p.id
            ORDER BY p.updated_at DESC, p.name COLLATE NOCASE
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def rename_playlist(self, playlist_id: int, name: str) -> None:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("El nombre de la playlist no puede estar vacío.")
        with self.connection:
            self.connection.execute(
                "UPDATE playlists SET name=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (clean_name, playlist_id),
            )

    def delete_playlist(self, playlist_id: int) -> None:
        with self.connection:
            self.connection.execute("DELETE FROM playlists WHERE id=?", (playlist_id,))

    def save_playlist_tracks(
        self,
        playlist_id: int,
        tracks: list[dict[str, Any]],
    ) -> None:
        values = [
            (
                playlist_id,
                position,
                str(track.get("path") or ""),
                str(track.get("title") or Path(str(track.get("path") or "Pista")).stem),
                str(track.get("artist") or "Artista desconocido"),
                float(track.get("duration") or 0),
            )
            for position, track in enumerate(tracks)
            if track.get("path")
        ]
        with self.connection:
            self.connection.execute(
                "DELETE FROM playlist_tracks WHERE playlist_id=?",
                (playlist_id,),
            )
            self.connection.executemany(
                """
                INSERT INTO playlist_tracks(
                    playlist_id, position, path, title, artist, duration
                ) VALUES(?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            self.connection.execute(
                "UPDATE playlists SET updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (playlist_id,),
            )

    def add_to_playlist(self, playlist_id: int, track: dict[str, Any]) -> None:
        row = self.connection.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 AS next_position "
            "FROM playlist_tracks WHERE playlist_id=?",
            (playlist_id,),
        ).fetchone()
        position = int(row["next_position"])
        values = (
            playlist_id,
            position,
            str(track["path"]),
            str(track.get("title") or Path(track["path"]).stem),
            str(track.get("artist") or "Artista desconocido"),
            float(track.get("duration") or 0),
        )
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO playlist_tracks(
                    playlist_id, position, path, title, artist, duration
                ) VALUES(?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            self.connection.execute(
                "UPDATE playlists SET updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (playlist_id,),
            )

    def get_playlist_tracks(self, playlist_id: int) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT
                pt.position AS playlist_position,
                pt.path AS path,
                COALESCE(NULLIF(t.title, ''), NULLIF(pt.title, ''), 'Pista desconocida') AS title,
                COALESCE(NULLIF(t.artist, ''), NULLIF(pt.artist, ''), 'Artista desconocido') AS artist,
                COALESCE(NULLIF(t.album, ''), 'Lista de reproducción') AS album,
                COALESCE(t.genre, 'Sin género') AS genre,
                COALESCE(t.duration, pt.duration, 0) AS duration,
                t.cover_path AS cover_path,
                COALESCE(t.is_favorite, 0) AS is_favorite,
                t.last_played AS last_played,
                CASE WHEN t.path IS NULL THEN 0 ELSE 1 END AS in_library
            FROM playlist_tracks pt
            LEFT JOIN tracks t ON t.path=pt.path
            WHERE pt.playlist_id=?
            ORDER BY pt.position
            """,
            (playlist_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def remove_from_playlist(self, playlist_id: int, position: int) -> None:
        current = self.get_playlist_tracks(playlist_id)
        remaining = [
            {
                "path": track["path"],
                "title": track["title"],
                "artist": track["artist"],
                "duration": track["duration"],
            }
            for track in current
            if int(track["playlist_position"]) != position
        ]
        self.save_playlist_tracks(playlist_id, remaining)

    # ------------------------------------------------------------------
    # Track state
    # ------------------------------------------------------------------
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
