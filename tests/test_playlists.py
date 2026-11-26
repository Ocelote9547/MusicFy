from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from musicfy.playlists import parse_m3u, write_m3u


class M3UPlaylistTests(unittest.TestCase):
    def test_parse_extended_playlist_with_relative_paths_and_unicode(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            music = root / "Music"
            music.mkdir()
            (music / "canción.mp3").write_bytes(b"")
            playlist_file = root / "mix.m3u8"
            playlist_file.write_text(
                "#EXTM3U\n"
                "#PLAYLIST:Mi colección\n"
                "#EXTINF:213,Artista Ñ - Canción especial\n"
                "Music/canción.mp3\n"
                "Music/otra pista.flac\n",
                encoding="utf-8",
            )

            parsed = parse_m3u(playlist_file)

            self.assertEqual(parsed["name"], "Mi colección")
            self.assertEqual(len(parsed["tracks"]), 2)
            self.assertEqual(parsed["tracks"][0]["title"], "Canción especial")
            self.assertEqual(parsed["tracks"][0]["artist"], "Artista Ñ")
            self.assertEqual(parsed["tracks"][0]["duration"], 213)
            self.assertEqual(
                parsed["tracks"][0]["path"],
                str((music / "canción.mp3").resolve()),
            )
            self.assertEqual(parsed["tracks"][1]["title"], "otra pista")

    def test_remote_stream_entries_are_skipped_and_counted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            playlist_file = root / "radio.m3u"
            playlist_file.write_text(
                "#EXTM3U\n"
                "#EXTINF:-1,Radio\n"
                "https://example.invalid/live.mp3\n"
                "#EXTINF:100,Local song\n"
                "local.mp3\n",
                encoding="utf-8",
            )

            parsed = parse_m3u(playlist_file)

            self.assertEqual(parsed["skipped_remote"], 1)
            self.assertEqual(len(parsed["tracks"]), 1)
            self.assertEqual(parsed["tracks"][0]["title"], "Local song")

    def test_export_then_import_keeps_playlist_order_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            song_a = root / "a.mp3"
            song_b = root / "b.mp3"
            song_a.write_bytes(b"")
            song_b.write_bytes(b"")
            output = root / "export" / "mix.m3u8"

            write_m3u(
                output,
                "Orden de prueba",
                [
                    {"path": str(song_a), "title": "Primera", "artist": "Uno", "duration": 123},
                    {"path": str(song_b), "title": "Segunda", "artist": "Dos", "duration": 245},
                ],
            )
            parsed = parse_m3u(output)

            self.assertEqual(parsed["name"], "Orden de prueba")
            self.assertEqual(
                [track["path"] for track in parsed["tracks"]],
                [str(song_a.resolve()), str(song_b.resolve())],
            )
            self.assertEqual(
                [track["title"] for track in parsed["tracks"]],
                ["Primera", "Segunda"],
            )


if __name__ == "__main__":
    unittest.main()
