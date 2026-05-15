"""Import dialog — cURL paste with auto-detection.

Paste a `curl …` command into the editor and Postaz parses it on the spot:
no button clicks, no friction. If the parse fails, a red error line below
the editor explains exactly what went wrong."""
from __future__ import annotations

from PySide6.QtCore import QMimeData, Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..curl_import import parse_curl
from ..database import RequestRecord
from ..i18n import t
from .widgets import GhostButton


class _PasteEdit(QPlainTextEdit):
    """QPlainTextEdit that emits a `pasted` signal *after* any paste lands.

    We override `insertFromMimeData` (called by Qt for both Ctrl+V and
    middle-click paste on X11) and schedule the signal on the next tick so
    the document has finished updating before listeners read it back."""

    pasted = Signal()

    def insertFromMimeData(self, source: QMimeData) -> None:
        super().insertFromMimeData(source)
        QTimer.singleShot(0, self.pasted.emit)


_IMPORT_TITLE = {"en": "Import cURL", "az": "cURL İdxalı", "tr": "cURL İçe Aktar"}
_IMPORT_HINT = {
    "en": "Paste a `curl …` command — Postaz detects it automatically.",
    "az": "`curl …` əmrini yapışdırın — Postaz onu avtomatik tanıyır.",
    "tr": "Bir `curl …` komutunu yapıştırın — Postaz onu otomatik algılar.",
}
_INVALID_CURL = {
    "en": "This doesn't look like a valid cURL command.",
    "az": "Bu, etibarlı bir cURL əmrinə bənzəmir.",
    "tr": "Bu, geçerli bir cURL komutuna benzemiyor.",
}


class ImportDialog(QDialog):
    """cURL importer.

    Two ways to drive it:
      1. Paste — the dialog accepts itself the moment a valid cURL lands.
      2. Manual edit + click `Import` — fallback for typed-out commands.

    Successful imports leave the parsed record on `self.record`."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        from ..i18n import translator
        self._lang = translator.language
        self.record: RequestRecord | None = None
        self.setWindowTitle(_IMPORT_TITLE.get(self._lang, _IMPORT_TITLE["en"]))
        self.setMinimumSize(660, 460)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(22, 22, 22, 22)
        outer.setSpacing(12)

        title = QLabel(_IMPORT_TITLE.get(self._lang, _IMPORT_TITLE["en"]))
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        outer.addWidget(title)

        hint = QLabel(_IMPORT_HINT.get(self._lang, _IMPORT_HINT["en"]))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #8b8fab; font-size: 12px;")
        outer.addWidget(hint)

        # editor — subclass that signals on paste so we can auto-import
        self.editor = _PasteEdit()
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.setPlaceholderText(
            "curl -X POST https://api.example.com/users \\\n"
            "  -H 'Authorization: Bearer xxx' \\\n"
            "  -H 'Content-Type: application/json' \\\n"
            "  -d '{\"name\":\"Ada\"}'"
        )
        self.editor.pasted.connect(self._on_paste)
        outer.addWidget(self.editor, 1)

        # red error line shown only when a paste fails to parse
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(
            "color: #ff6e7c; font-size: 12px; padding: 6px 10px;"
            "background: rgba(255, 110, 124, 0.08);"
            "border: 1px solid rgba(255, 110, 124, 0.35);"
            "border-radius: 6px;"
        )
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        outer.addWidget(self.error_label)

        # Only one button is needed — paste is the import action.
        btns = QHBoxLayout()
        btns.addStretch()
        cancel = GhostButton(t("Cancel"))
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        outer.addLayout(btns)

    def _on_paste(self) -> None:
        """Triggered after Ctrl+V completes — try to import without prompting."""
        text = self.editor.toPlainText().strip()
        if not text:
            return
        # Reject pastes that obviously aren't cURL (helps avoid false positives
        # when the user paste-replaces a snippet by accident).
        if "curl" not in text.lower().split(None, 1)[0:1] and not text.lstrip().lower().startswith("curl"):
            self._show_error(_INVALID_CURL.get(self._lang, _INVALID_CURL["en"]))
            return
        try:
            self.record = parse_curl(text)
        except Exception as e:
            self._show_error(str(e))
            return
        # Valid — close the dialog with success.
        self.accept()

    def _show_error(self, message: str) -> None:
        self.error_label.setText(f"⚠  {message}")
        self.error_label.setVisible(True)
