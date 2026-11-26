from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from typing import Any

from mutagen import File as MutagenFile
from mutagen.flac import Picture
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage

AUDIO_EXTENSIONS = {
    ".mp3", ".flac", ".wav", ".ogg", ".opus", ".m4a", ".aac", ".aiff", ".wma"
}
FOLDER_COVERS = ("cover.jpg", "cover.png", "folder.jpg", "folder.png", "front.jpg", "front.png")


def read_audio_file(file_path: str | Path) -> dict[str, Any] | None:
    """Read audio tags and cache embedded artwork without changing the source."""
    path = Path(file_path).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
        return None

    title = path.stem
    artist = "Artista desconocido"
    album = "Álbum desconocido"
    genre = "Sin género"
    duration = 0.0
    cover_path: str | None = None

    try:
        audio = MutagenFile(path, easy=True)
        if audio is not None:
            tags = audio.tags or {}
            title = _first_tag(tags, "title") or title
            artist = _first_tag(tags, "artist") or artist
            album = _first_tag(tags, "album") or album
            genre = _first_tag(tags, "genre") or genre
            info = getattr(audio, "info", None)
            duration = float(getattr(info, "length", 0.0) or 0.0)
    except (OSError, ValueError, TypeError):
        # Keep the file in the library even if its tags are damaged.
        pass

    cover_path = _find_folder_cover(path)
    if cover_path is None:
        try:
            raw_audio = MutagenFile(path)
            if raw_audio is not None:
                image_data = _extract_cover_bytes(raw_audio)
                if image_data:
                    cover_path = _cache_cover(path, image_data)
        except (OSError, ValueError, TypeError):
            pass

    return {
        "path": str(path),
        "title": title,
        "artist": artist,
        "album": album,
        "genre": genre,
        "duration": duration,
        "cover_path": cover_path,
    }


def _first_tag(tags: Any, key: str) -> str | None:
    value = tags.get(key)
    if isinstance(value, (list, tuple)):
        value = value[0] if value else None
    return str(value).strip() if value else None


def _find_folder_cover(audio_path: Path) -> str | None:
    try:
        for filename in FOLDER_COVERS:
            candidate = audio_path.parent / filename
            if candidate.is_file():
                return str(candidate)
    except OSError:
        pass
    return None


def _extract_cover_bytes(audio: Any) -> bytes | None:
    pictures = getattr(audio, "pictures", None)
    if pictures:
        for picture in pictures:
            data = getattr(picture, "data", None)
            if data:
                return bytes(data)

    tags = getattr(audio, "tags", None)
    if not tags:
        return None

    # ID3 artwork (MP3).
    getall = getattr(tags, "getall", None)
    if callable(getall):
        try:
            for picture in getall("APIC"):
                data = getattr(picture, "data", None)
                if data:
                    return bytes(data)
        except (KeyError, TypeError):
            pass

    # MP4/M4A cover atoms and generic picture-like tag values.
    try:
        for key, value in tags.items():
            key_name = str(key).upper()
            values = value if isinstance(value, (list, tuple)) else [value]
            for item in values:
                data = getattr(item, "data", None)
                if data:
                    return bytes(data)
                if key_name.startswith("COVR") and isinstance(item, (bytes, bytearray)):
                    return bytes(item)

            # Vorbis comments store pictures as base64 FLAC Picture blocks.
            if "METADATA_BLOCK_PICTURE" in key_name:
                encoded = values[0]
                if isinstance(encoded, bytes):
                    encoded = encoded.decode("ascii", errors="ignore")
                try:
                    picture = Picture(base64.b64decode(encoded))
                    if picture.data:
                        return bytes(picture.data)
                except (ValueError, TypeError):
                    continue

            # Older Vorbis files may contain raw base64 COVERART.
            if "COVERART" in key_name:
                encoded = values[0]
                if isinstance(encoded, bytes):
                    encoded = encoded.decode("ascii", errors="ignore")
                try:
                    return base64.b64decode(encoded)
                except (ValueError, TypeError):
                    continue
    except (AttributeError, TypeError, ValueError):
        return None

    return None


def _cache_cover(audio_path: Path, image_data: bytes) -> str | None:
    image = QImage()
    if not image.loadFromData(image_data) or image.isNull():
        return None

    cache_dir = Path.home() / ".musicfy" / "covers"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        stat = audio_path.stat()
        identity = f"{audio_path}:{stat.st_size}:{stat.st_mtime_ns}"
        filename = hashlib.sha256(identity.encode("utf-8")).hexdigest() + ".png"
        target = cache_dir / filename

        if not target.is_file():
            scaled = image.scaled(
                512,
                512,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = max(0, (scaled.width() - 512) // 2)
            y = max(0, (scaled.height() - 512) // 2)
            thumb = scaled.copy(x, y, min(512, scaled.width()), min(512, scaled.height()))
            if not thumb.save(str(target), "PNG"):
                return None
        return str(target)
    except OSError:
        return None


def scan_folder(folder: str | Path) -> list[dict[str, Any]]:
    root = Path(folder).expanduser()
    tracks: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
            track = read_audio_file(path)
            if track is not None:
                tracks.append(track)
    return tracks
