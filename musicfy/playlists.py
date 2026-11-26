from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def parse_m3u(file_path: str | Path) -> dict[str, Any]:
    """Parse an M3U/M3U8 file, resolving relative entries from its directory.

    Local entries are retained even if the referenced audio file is currently
    missing; this lets a playlist survive moving an external drive offline.
    Remote stream URLs are ignored by this local-library importer.
    """
    source = Path(file_path).expanduser().resolve()
    raw = source.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp1252")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")

    name = source.stem
    tracks: list[dict[str, Any]] = []
    pending_title = ""
    pending_duration = 0.0
    pending_artist = ""
    skipped = 0

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.upper().startswith("#PLAYLIST:"):
            explicit_name = line.split(":", 1)[1].strip()
            if explicit_name:
                name = explicit_name
            continue

        if line.upper().startswith("#EXTINF:"):
            payload = line.split(":", 1)[1]
            duration_text, separator, display = payload.partition(",")
            try:
                pending_duration = max(0.0, float(duration_text.strip()))
            except ValueError:
                pending_duration = 0.0
            display = display.strip() if separator else ""
            if " - " in display:
                pending_artist, pending_title = display.split(" - ", 1)
            else:
                pending_artist, pending_title = "", display
            continue

        if line.startswith("#"):
            continue

        if line.lower().startswith(("http://", "https://", "rtsp://")):
            skipped += 1
            pending_title = ""
            pending_artist = ""
            pending_duration = 0.0
            continue

        entry = Path(line)
        if not entry.is_absolute():
            entry = source.parent / entry
        entry = entry.resolve()

        title = pending_title or entry.stem
        tracks.append(
            {
                "path": str(entry),
                "title": title,
                "artist": pending_artist or "Artista desconocido",
                "duration": pending_duration,
            }
        )
        pending_title = ""
        pending_artist = ""
        pending_duration = 0.0

    return {"name": name, "tracks": tracks, "skipped_remote": skipped}


def write_m3u(
    file_path: str | Path,
    playlist_name: str,
    tracks: list[dict[str, Any]],
) -> Path:
    """Write a UTF-8 extended M3U using relative paths where possible."""
    target = Path(file_path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    lines = ["#EXTM3U", f"#PLAYLIST:{playlist_name}"]
    for track in tracks:
        raw_path = str(track.get("path") or "").strip()
        if not raw_path:
            continue

        audio_path = Path(raw_path)
        try:
            m3u_path = audio_path.relative_to(target.parent)
        except ValueError:
            try:
                m3u_path = Path(os.path.relpath(audio_path, target.parent))
            except ValueError:
                m3u_path = audio_path

        duration = max(0, int(float(track.get("duration") or 0)))
        artist = str(track.get("artist") or "").strip()
        title = str(track.get("title") or audio_path.stem).strip()
        display = f"{artist} - {title}" if artist else title
        lines.append(f"#EXTINF:{duration},{display}")
        lines.append(m3u_path.as_posix())

    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target
