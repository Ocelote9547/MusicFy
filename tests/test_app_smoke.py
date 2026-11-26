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


    def test_playlist_navigation_is_available(self) -> None:
        self.window.show_page("playlists")
        self.assertEqual(self.window.page_mode, "playlists")
        self.assertEqual(self.window.content_stack.currentIndex(), 2)
        self.assertTrue(self.window.nav_buttons["playlists"].isChecked())



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
