from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from musicfy.app import MusicFyWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MusicFy")
    app.setOrganizationName("N3mesis Studio")

    window = MusicFyWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
