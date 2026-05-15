"""Local API Tester — entry point."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app.database import Database
from app.ui.main_window import MainWindow


APP_DIR_NAME = "LocalAPITester"


def _data_dir() -> Path:
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData/Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library/Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    p = base / APP_DIR_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Local API Tester")
    app.setOrganizationName("local")
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    db_path = _data_dir() / "app.db"
    db = Database(db_path)

    win = MainWindow(db)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
