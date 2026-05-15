"""Live log viewer — tails the rotating log file with colour highlighting."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..logger import get_logger, log_path
from .widgets import GhostButton

log = get_logger(__name__)


_LEVEL_TINTS = {
    "DEBUG":    "#7e8299",
    "INFO":     "#6fb8ff",
    "WARNING":  "#f4b860",
    "ERROR":    "#ff8090",
    "CRITICAL": "#ff8090",
}


class LogViewer(QDialog):
    """Tail-style live log inspector.

    Reads the current log file, paints level names in colour, and refreshes
    whenever the file changes on disk (or every 1.2 s as a fallback for
    filesystems where QFileSystemWatcher misses writes)."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._path = log_path()
        self._last_size = 0
        self.setWindowTitle("Postaz — Logs")
        self.setMinimumSize(900, 560)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(12)

        # Header
        head = QHBoxLayout()
        head.setSpacing(10)
        title = QLabel("Activity Log")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #ffffff;")
        head.addWidget(title)
        self.path_label = QLabel(str(self._path) if self._path else "(no log file)")
        self.path_label.setStyleSheet("color: #7e8299; font-size: 11px;")
        head.addStretch()
        head.addWidget(self.path_label)
        outer.addLayout(head)

        # Body
        self.view = QPlainTextEdit()
        self.view.setReadOnly(True)
        self.view.setFont(QFont("JetBrains Mono", 10))
        self.view.setLineWrapMode(QPlainTextEdit.NoWrap)
        outer.addWidget(self.view, 1)

        # Buttons
        btn_row = QHBoxLayout()
        clear_btn = GhostButton("Scroll to bottom")
        clear_btn.clicked.connect(self._scroll_bottom)
        copy_btn = GhostButton("Copy all")
        copy_btn.clicked.connect(self._copy_all)
        close_btn = GhostButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(clear_btn)
        btn_row.addWidget(copy_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        outer.addLayout(btn_row)

        # Watch file for changes
        self._watcher = QFileSystemWatcher(self)
        if self._path and self._path.exists():
            self._watcher.addPath(str(self._path))
        self._watcher.fileChanged.connect(self._refresh)

        # Fallback poller — some FS / editors fire watcher only on close.
        self._timer = QTimer(self)
        self._timer.setInterval(1200)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()

        self._refresh(force=True)

    # ── private ──────────────────────────────────────────────────────────
    def _refresh(self, _path: str | None = None, force: bool = False) -> None:
        if not self._path or not self._path.exists():
            return
        size = self._path.stat().st_size
        if size == self._last_size and not force:
            return
        try:
            text = self._path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return
        self._last_size = size
        self._render(text)
        self._scroll_bottom()

    def _render(self, text: str) -> None:
        # Show only the last ~2000 lines so the viewer stays snappy.
        lines = text.splitlines()[-2000:]
        self.view.clear()
        for line in lines:
            self._append_colored(line)

    def _append_colored(self, line: str) -> None:
        cursor = self.view.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Find a [LEVEL] tag and colour just that portion.
        tinted = None
        for level, color in _LEVEL_TINTS.items():
            tag = f"[{level:<7}]"
            if tag in line:
                tinted = (tag, color)
                break

        base = QTextCharFormat()
        base.setForeground(QColor("#c9cce0"))

        if tinted:
            tag, color = tinted
            idx = line.index(tag)
            cursor.setCharFormat(base)
            cursor.insertText(line[:idx])
            highlight = QTextCharFormat()
            highlight.setForeground(QColor(color))
            highlight.setFontWeight(QFont.DemiBold)
            cursor.setCharFormat(highlight)
            cursor.insertText(tag)
            cursor.setCharFormat(base)
            cursor.insertText(line[idx + len(tag):])
        else:
            cursor.setCharFormat(base)
            cursor.insertText(line)
        cursor.insertBlock()

    def _scroll_bottom(self) -> None:
        cursor = self.view.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.view.setTextCursor(cursor)
        self.view.ensureCursorVisible()

    def _copy_all(self) -> None:
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(self.view.toPlainText())
