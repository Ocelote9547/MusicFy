from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal


class OnlineResolver(QThread):
    """Resolve a user-provided, permitted audio URL with yt-dlp.

    This worker only inspects the media and returns a stream URL. It does not
    download or save audio to disk.
    """

    resolved = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, source_url: str) -> None:
        super().__init__()
        self.source_url = source_url.strip()

    def run(self) -> None:
        try:
            from yt_dlp import YoutubeDL

            options = {
                "format": "bestaudio/best",
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "socket_timeout": 15,
            }

            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(self.source_url, download=False)

            if not isinstance(info, dict):
                raise RuntimeError("La fuente no devolvió información reproducible.")

            # Some extractors return a list of entries even with noplaylist.
            if info.get("entries"):
                info = next((item for item in info["entries"] if item), None)
                if not isinstance(info, dict):
                    raise RuntimeError("No se ha encontrado ninguna pista reproducible.")

            stream_url = info.get("url")
            if not stream_url:
                audio_formats = [
                    item for item in info.get("formats", [])
                    if item.get("url") and item.get("acodec") != "none"
                ]
                if audio_formats:
                    stream_url = audio_formats[-1]["url"]

            if not stream_url:
                raise RuntimeError("La fuente no ofrece un flujo de audio compatible.")

            self.resolved.emit(
                {
                    "title": str(info.get("track") or info.get("title") or "Reproducción online"),
                    "artist": str(info.get("artist") or info.get("uploader") or "Fuente online"),
                    "album": str(info.get("album") or "Online"),
                    "duration": float(info.get("duration") or 0),
                    "url": str(stream_url),
                }
            )
        except ImportError:
            self.failed.emit(
                "No se ha encontrado yt-dlp. Instala las dependencias con: "
                "python -m pip install -r requirements.txt"
            )
        except Exception as exc:  # The extractor raises several source-specific errors.
            self.failed.emit(str(exc))
