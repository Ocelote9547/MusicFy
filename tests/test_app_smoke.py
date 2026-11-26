from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtCore import Qt

from musicfy.app import MusicFyWindow, draw_vector_icon


class MusicFyWindowSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt_app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.home = Path(self.temp_dir.name)
        self.home_patch = patch.object(Path, "home", return_value=self.home)
        self.home_patch.start()
        self.window = MusicFyWindow()

    def tearDown(self) -> None:
        self.window.close()
        self.home_patch.stop()
        self.temp_dir.cleanup()

    def test_main_window_builds_all_library_sections(self) -> None:
        self.assertEqual(
            set(self.window.nav_buttons),
            {"home", "tracks", "albums", "artists", "genres", "favorites", "history", "playlists"},
        )
        self.assertEqual(self.window.page_mode, "home")
        self.assertEqual(self.window.windowTitle(), "N3mesisFy")
        self.assertTrue(self.window.nav_buttons["home"].isChecked())
        self.assertFalse(self.window.home_empty_card.isHidden())
        self.assertTrue(self.window.home_album_scroll.isHidden())

    def test_navigation_switches_to_album_grid(self) -> None:
        self.window.show_page("albums")
        self.assertEqual(self.window.page_mode, "albums")
        self.assertEqual(self.window.content_stack.currentIndex(), 2)
        self.assertTrue(self.window.nav_buttons["albums"].isChecked())


    def test_home_features_real_album_and_playlist_shelves(self) -> None:
        self.window.database.save_track({
            "path": str(self.home / "first-track.mp3"),
            "title": "First track",
            "artist": "Example Artist",
            "album": "Blue Horizon",
            "genre": "Electronic",
            "duration": 180,
        })
        self.window.database.create_playlist("Night drive")
        self.window.refresh_content()

        self.assertEqual(
            self.window.hero_text_label.text(),
            "Blue Horizon  ·  Example Artist",
        )
        self.assertFalse(self.window.home_album_scroll.isHidden())
        self.assertFalse(self.window.home_playlist_section.isHidden())
        self.assertEqual(self.window.featured_album["album"], "Blue Horizon")



    def test_playlist_navigation_is_available(self) -> None:
        self.window.show_page("playlists")
        self.assertEqual(self.window.page_mode, "playlists")
        self.assertEqual(self.window.content_stack.currentIndex(), 2)
        self.assertTrue(self.window.nav_buttons["playlists"].isChecked())



    def test_playlist_detail_exposes_m3u_actions(self) -> None:
        playlist_id = self.window.database.create_playlist("Test list")
        self.window.database.save_playlist_tracks(
            playlist_id,
            [{"path": "/music/test.mp3", "title": "Test song", "artist": "Test artist"}],
        )
        playlist = self.window.database.get_playlist(playlist_id)
        self.window.show_page("playlists")
        self.window.show_playlist_detail(playlist)

        self.assertEqual(self.window.page_mode, "playlist_detail")
        self.assertEqual(self.window.active_playlist_id, playlist_id)
        self.assertFalse(self.window.export_playlist_button.isHidden())
        self.assertFalse(self.window.delete_playlist_button.isHidden())
        self.assertEqual(len(self.window.visible_tracks), 1)



    def test_vector_icon_set_paints_without_system_glyph_fonts(self) -> None:
        icon_names = (
            "home", "tracks", "albums", "artist", "genres", "star",
            "history", "plus", "folder", "globe", "arrow-right",
            "arrow-left", "search", "music-note", "play", "pause",
            "previous", "next", "playlist", "shuffle", "repeat", "import", "export", "trash",
        )
        for icon_name in icon_names:
            with self.subTest(icon=icon_name):
                pixmap = QPixmap(32, 32)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                draw_vector_icon(painter, icon_name, "#12aee9", 24)
                painter.end()
                image = pixmap.toImage()
                painted_pixels = sum(
                    1
                    for y in range(image.height())
                    for x in range(image.width())
                    if image.pixelColor(x, y).alpha() > 0
                )
                self.assertGreater(painted_pixels, 0)



if __name__ == "__main__":
    unittest.main()
