from __future__ import annotations

from pathlib import Path
from typing import Any

from mutagen import File as MutagenFile

AUDIO_EXTENSIONS = {
    ".mp3", ".flac", ".wav", ".ogg", ".opus", ".m4a", ".aac", ".aiff", ".wma"
}


def read_audio_file(file_path: str | Path) -> dict[str, Any] | None:
    """Read basic tags without modifying the audio file."""
    path = Path(file_path).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
        return None

    title = path.stem
    artist = "Artista desconocido"
    album = "Álbum desconocido"
    duration = 0.0

    try:
        audio = MutagenFile(path, easy=True)
        if audio is not None:
            tags = audio.tags or {}
            title = _first_tag(tags, "title") or title
            artist = _first_tag(tags, "artist") or artist
            album = _first_tag(tags, "album") or album
            info = getattr(audio, "info", None)
            duration = float(getattr(info, "length", 0.0) or 0.0)
    except (OSError, ValueError, TypeError):
        # Keep the file in the library even if its tags are damaged.
        pass

    return {
        "path": str(path),
        "title": title,
        "artist": artist,
        "album": album,
        "duration": duration,
    }


def _first_tag(tags: Any, key: str) -> str | None:
    value = tags.get(key)
    if isinstance(value, (list, tuple)):
        value = value[0] if value else None
    return str(value).strip() if value else None


def scan_folder(folder: str | Path) -> list[dict[str, Any]]:
    root = Path(folder).expanduser()
    tracks: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
            track = read_audio_file(path)
            if track is not None:
                tracks.append(track)
    return tracks
