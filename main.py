"""
Postaz — entry point.

Bootstraps the QApplication, opens (or creates) the local SQLite database
under the OS-specific app-data folder, then shows the main window.

Run from project root:
    python main.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app.database import Database
from app.logger import get_logger, setup_logging
from app.ui.icons import app_icon
from app.ui.main_window import MainWindow


APP_DIR_NAME = "Postaz"  # folder name under %APPDATA% / Application Support / .local/share


def _data_dir() -> Path:
    """Return the writable per-user data directory for Postaz.

    Resolves to a platform-native location so the user's SQLite database
    survives reinstalls and stays out of the project tree:

      * Windows : %APPDATA%\\Postaz
      * macOS   : ~/Library/Application Support/Postaz
      * Linux   : ~/.local/share/Postaz   (or $XDG_DATA_HOME/Postaz)
    """
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
    """Build the Qt app, attach the database, show the window, enter the event loop."""
    # Smooth HiDPI scaling — avoids fractional-DPI rounding artefacts.
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Postaz")
    app.setApplicationDisplayName("Postaz")
    app.setOrganizationName("Postaz")
    app.setWindowIcon(app_icon(256))

    # Set a clean default font; widgets that need monospace pick their own.
    app.setFont(QFont("Segoe UI", 10))

    # Configure logging first so the rest of bootstrap is captured.
    data = _data_dir()
    log_file = setup_logging(data)
    log = get_logger(__name__)
    log.info("data dir: %s", data)
    log.info("log file: %s", log_file)
    log.info("python: %s | qt: %s", sys.version.split()[0], _qt_version())

    # Open or create the local DB; schema migrations run on first use.
    db_path = data / "postaz.db"
    log.info("opening database: %s", db_path)
    db = Database(db_path)

    window = MainWindow(db)
    window.show()
    log.info("main window shown — entering event loop")
    code = app.exec()
    log.info("event loop exited with code %d", code)
    return code


def _qt_version() -> str:
    try:
        from PySide6 import __version__ as v
        return v
    except Exception:
        return "?"


if __name__ == "__main__":
    sys.exit(main())
