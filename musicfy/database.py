from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class MusicDatabase:
    """Small SQLite store for the user's local music library."""

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
                    duration REAL NOT NULL DEFAULT 0,
                    is_favorite INTEGER NOT NULL DEFAULT 0,
                    last_played TEXT
                )
                """
            )

    def save_track(self, track: dict[str, Any]) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO tracks(path, title, artist, album, duration)
                VALUES(:path, :title, :artist, :album, :duration)
                ON CONFLICT(path) DO UPDATE SET
                    title=excluded.title,
                    artist=excluded.artist,
                    album=excluded.album,
                    duration=excluded.duration
                """,
                track,
            )

    def list_tracks(self, mode: str = "all") -> list[dict[str, Any]]:
        if mode == "favorites":
            query = "SELECT * FROM tracks WHERE is_favorite=1 ORDER BY artist, album, title"
        elif mode == "history":
            query = (
                "SELECT * FROM tracks WHERE last_played IS NOT NULL "
                "ORDER BY last_played DESC LIMIT 100"
            )
        else:
            query = "SELECT * FROM tracks ORDER BY artist, album, title"

        rows = self.connection.execute(query).fetchall()
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
