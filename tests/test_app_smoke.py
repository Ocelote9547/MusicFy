from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from musicfy.app import MusicFyWindow


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
            {"home", "tracks", "albums", "artists", "genres", "favorites", "history"},
        )
        self.assertEqual(self.window.page_mode, "home")
        self.assertTrue(self.window.home_empty_card.isVisible())
        self.assertFalse(self.window.home_album_scroll.isVisible())

    def test_navigation_switches_to_album_grid(self) -> None:
        self.window.show_page("albums")
        self.assertEqual(self.window.page_mode, "albums")
        self.assertEqual(self.window.content_stack.currentIndex(), 2)
        self.assertTrue(self.window.nav_buttons["albums"].isChecked())


if __name__ == "__main__":
    unittest.main()
