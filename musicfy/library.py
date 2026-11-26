from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
from typing import Any

from mutagen import File as MutagenFile
from mutagen.flac import Picture
from PyQt6.QtCore import Qt, QThread, pyqtSignal
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
    lyrics = ""
    replaygain_track_gain = ""
    cover_path: str | None = None

    try:
        audio = MutagenFile(path, easy=True)
        if audio is not None:
            tags = audio.tags or {}
            title = _first_tag(tags, "title") or title
            artist = _first_tag(tags, "artist") or artist
            album = _first_tag(tags, "album") or album
            genre = _first_tag(tags, "genre") or genre
            lyrics = (
                _first_tag(tags, "lyrics")
                or _first_tag(tags, "unsyncedlyrics")
                or _first_tag(tags, "unsynced_lyrics")
                or ""
            )
            if not lyrics:
                raw_tags = getattr(audio, "tags", None)
                if raw_tags is not None:
                    for key in raw_tags.keys():
                        key_name = str(key).upper()
                        if key_name.startswith(("USLT", "SYLT", "LYRICS")):
                            value = raw_tags.get(key)
                            text = getattr(value, "text", value)
                            if isinstance(text, bytes):
                                text = text.decode("utf-8", errors="replace")
                            if text:
                                lyrics = str(text).strip()
                                break
            replaygain_track_gain = _first_tag(tags, "replaygain_track_gain") or ""
            info = getattr(audio, "info", None)
            duration = float(getattr(info, "length", 0.0) or 0.0)
    except Exception:
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
        except Exception:
            pass

    return {
        "path": str(path),
        "title": title,
        "artist": artist,
        "album": album,
        "genre": genre,
        "duration": duration,
        "cover_path": cover_path,
        "lyrics": lyrics,
        "replaygain_track_gain": replaygain_track_gain,
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



class LibraryImportWorker(QThread):
    """Scan folders/files without blocking the Qt GUI thread."""

    batch_ready = pyqtSignal(list)
    progress = pyqtSignal(str, int)
    completed = pyqtSignal(int)
    failed = pyqtSignal(str)

    def __init__(
        self,
        folder: str | Path | None = None,
        paths: list[str] | None = None,
        batch_size: int = 24,
    ) -> None:
        super().__init__()
        self.folder = Path(folder).expanduser() if folder else None
        self.paths = [Path(path).expanduser() for path in (paths or [])]
        self.batch_size = max(1, batch_size)

    def _iter_audio_paths(self):
        if self.folder is not None:
            def on_walk_error(_error: OSError) -> None:
                # Ignore inaccessible subdirectories instead of aborting the scan.
                return

            for root, _directories, filenames in os.walk(
                self.folder,
                onerror=on_walk_error,
                followlinks=False,
            ):
                if self.isInterruptionRequested():
                    return
                for filename in filenames:
                    path = Path(root) / filename
                    if path.suffix.lower() in AUDIO_EXTENSIONS:
                        yield path
        else:
            for path in self.paths:
                if path.suffix.lower() in AUDIO_EXTENSIONS:
                    yield path

    def run(self) -> None:
        total = 0
        batch: list[dict[str, Any]] = []
        try:
            for path in self._iter_audio_paths():
                if self.isInterruptionRequested():
                    break
                track = read_audio_file(path)
                if track is None:
                    continue
                batch.append(track)
                total += 1
                if len(batch) >= self.batch_size:
                    self.batch_ready.emit(batch)
                    batch = []
                if total == 1 or total % 12 == 0:
                    self.progress.emit(path.name, total)

            if batch:
                self.batch_ready.emit(batch)
            self.completed.emit(total)
        except Exception as exc:
            self.failed.emit(str(exc))
