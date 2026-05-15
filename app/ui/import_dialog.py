"""Import dialog — cURL paste + future formats."""
from __future__ import annotations

from PySide6.QtCore import Qt
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
from .widgets import GhostButton, PrimaryButton


_IMPORT_TITLE = {"en": "Import cURL", "az": "cURL İdxalı", "tr": "cURL İçe Aktar"}
_IMPORT_HINT = {
    "en": "Paste a `curl …` command — query string, headers, body and basic auth are extracted automatically.",
    "az": "`curl …` əmrini yapışdırın — sorğu sətri, başlıqlar, gövdə və basic auth avtomatik çıxarılır.",
    "tr": "Bir `curl …` komutu yapıştırın — sorgu dizesi, başlıklar, gövde ve basic auth otomatik çıkarılır.",
}
_IMPORT_BTN = {"en": "Import", "az": "İdxal et", "tr": "İçe Aktar"}


class ImportDialog(QDialog):
    """Returns a RequestRecord via `.record` after accept()."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        from ..i18n import translator
        lang = translator.language
        self.record: RequestRecord | None = None
        self.setWindowTitle(_IMPORT_TITLE.get(lang, _IMPORT_TITLE["en"]))
        self.setMinimumSize(640, 440)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(22, 22, 22, 22)
        outer.setSpacing(12)

        title = QLabel(_IMPORT_TITLE.get(lang, _IMPORT_TITLE["en"]))
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        outer.addWidget(title)

        hint = QLabel(_IMPORT_HINT.get(lang, _IMPORT_HINT["en"]))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #8b8fab; font-size: 12px;")
        outer.addWidget(hint)

        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.setPlaceholderText(
            "curl -X POST https://api.example.com/users \\\n"
            "  -H 'Authorization: Bearer xxx' \\\n"
            "  -H 'Content-Type: application/json' \\\n"
            "  -d '{\"name\":\"Ada\"}'"
        )
        outer.addWidget(self.editor, 1)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff8090; font-size: 12px;")
        self.error_label.setVisible(False)
        outer.addWidget(self.error_label)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel = GhostButton(t("Cancel"))
        cancel.clicked.connect(self.reject)
        ok = PrimaryButton(_IMPORT_BTN.get(lang, _IMPORT_BTN["en"]))
        ok.clicked.connect(self._import)
        btns.addWidget(cancel)
        btns.addWidget(ok)
        outer.addLayout(btns)

    def _import(self) -> None:
        text = self.editor.toPlainText().strip()
        if not text:
            return
        try:
            self.record = parse_curl(text)
        except Exception as e:
            self.error_label.setText(str(e))
            self.error_label.setVisible(True)
            return
        self.accept()
