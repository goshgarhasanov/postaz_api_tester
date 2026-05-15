"""Response panel.

Top row: colored status badge + timing + size meta.
Bottom: tabbed view of the response — pretty JSON / Headers / Raw bytes.
While a request is in flight, a translucent overlay with a spinner covers
the whole panel."""
from __future__ import annotations

import json

from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..http_client import ResponseData
from ..i18n import t, translator
from .animations import fade_in
from .widgets import LoaderOverlay, StatusBadge


class JsonHighlighter(QSyntaxHighlighter):
    """Minimal JSON colorizer.

    Just enough rules to make a response readable at a glance: object keys
    in blue, strings in green, numbers in orange, true/false/null in pink,
    structural punctuation in muted grey."""

    def __init__(self, doc):
        super().__init__(doc)
        self.rules: list[tuple[QRegularExpression, QTextCharFormat]] = []

        def fmt(color: str, bold: bool = False) -> QTextCharFormat:
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(QFont.DemiBold)
            return f

        self.rules.append((QRegularExpression(r'"(?:[^"\\]|\\.)*"\s*:'), fmt("#7c9eff", True)))
        self.rules.append((QRegularExpression(r'"(?:[^"\\]|\\.)*"'), fmt("#7fe6b3")))
        self.rules.append((QRegularExpression(r"\b-?\d+(\.\d+)?([eE][+-]?\d+)?\b"), fmt("#f5b86c")))
        self.rules.append((QRegularExpression(r"\b(true|false|null)\b"), fmt("#ff8090", True)))
        self.rules.append((QRegularExpression(r"[\{\}\[\],:]"), fmt("#8b8fab")))

    def highlightBlock(self, text: str) -> None:
        for rx, fmt_ in self.rules:
            it = rx.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt_)


class ResponseViewer(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 14, 20, 16)
        outer.setSpacing(12)

        meta = QFrame()
        meta.setMinimumHeight(28)
        ml = QHBoxLayout(meta)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(10)

        self.status = StatusBadge()
        self.time_label = QLabel("—")
        self.size_label = QLabel("—")
        for lbl in (self.time_label, self.size_label):
            lbl.setStyleSheet("color: #8b8fab; font-size: 12px;")

        self.icon_time = QLabel("⏱")
        self.icon_size = QLabel("⇣")
        for ic in (self.icon_time, self.icon_size):
            ic.setStyleSheet("color: #6b6f88; font-size: 13px;")

        ml.addWidget(self.status)
        ml.addSpacing(8)
        ml.addWidget(self.icon_time)
        ml.addWidget(self.time_label)
        ml.addSpacing(12)
        ml.addWidget(self.icon_size)
        ml.addWidget(self.size_label)
        ml.addStretch()
        outer.addWidget(meta)

        self.tabs = QTabWidget()
        outer.addWidget(self.tabs, 1)

        # Each tab content gets its own padded wrapper so the inner widget
        # never touches the tab strip or the panel edge.
        def _padded(child: QWidget) -> QWidget:
            wrap = QWidget()
            ly = QVBoxLayout(wrap)
            ly.setContentsMargins(2, 12, 2, 8)
            ly.addWidget(child)
            return wrap

        self.body_view = QPlainTextEdit()
        self.body_view.setReadOnly(True)
        self.body_view.setFont(QFont("Consolas", 11))
        self.body_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.body_view.setPlaceholderText(t("Response body will appear here."))
        self.body_highlighter = JsonHighlighter(self.body_view.document())
        self.tabs.addTab(_padded(self.body_view), t("Body"))

        self.headers_table = QTableWidget(0, 2)
        self.headers_table.setHorizontalHeaderLabels([t("Header"), t("Value")])
        self.headers_table.verticalHeader().setVisible(False)
        self.headers_table.verticalHeader().setDefaultSectionSize(34)
        self.headers_table.setShowGrid(False)
        self.headers_table.setAlternatingRowColors(False)
        self.headers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.headers_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabs.addTab(_padded(self.headers_table), t("Headers"))

        self.raw_view = QPlainTextEdit()
        self.raw_view.setReadOnly(True)
        self.raw_view.setFont(QFont("Consolas", 11))
        self.tabs.addTab(_padded(self.raw_view), t("Raw"))

        self.loader = LoaderOverlay(self)
        translator.language_changed.connect(self._retranslate)
        self.clear()

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self.loader.resize(self.size())

    def _retranslate(self, _lang: str | None = None) -> None:
        self.tabs.setTabText(0, t("Body"))
        self.tabs.setTabText(1, t("Headers"))
        self.tabs.setTabText(2, t("Raw"))
        self.headers_table.setHorizontalHeaderLabels([t("Header"), t("Value")])
        self.body_view.setPlaceholderText(t("Response body will appear here."))

    def show_loading(self) -> None:
        self.loader.start(t("Sending request…"))

    def hide_loading(self) -> None:
        self.loader.stop()

    def clear(self) -> None:
        self.status.clear_status()
        self.time_label.setText("—")
        self.size_label.setText("—")
        self.body_view.setPlainText("")
        self.raw_view.setPlainText("")
        self.headers_table.setRowCount(0)

    def show_response(self, resp: ResponseData) -> None:
        """Paint a finished response (success OR network/parse failure).

        On failure the status badge turns red and the error message goes
        into the body tab so it's the first thing the user sees."""
        self.hide_loading()
        if not resp.ok:
            self.status.set_error()
            self.body_view.setPlainText(resp.error or "")
            self.raw_view.setPlainText(resp.error or "")
            self.time_label.setText(f"{resp.duration_ms} ms")
            self.size_label.setText("—")
            self.headers_table.setRowCount(0)
            fade_in(self.body_view, 220)
            return

        self.status.set_status(resp.status_code, resp.reason)
        self.time_label.setText(f"{resp.duration_ms} ms")
        self.size_label.setText(_humanize_size(resp.size_bytes))

        body = resp.body_text
        if resp.is_json:
            try:
                body = json.dumps(json.loads(resp.body_text), indent=2, ensure_ascii=False)
            except Exception:
                pass
        self.body_view.setPlainText(body)
        self.raw_view.setPlainText(resp.body_text)

        self.headers_table.setRowCount(0)
        for k, v in resp.headers.items():
            r = self.headers_table.rowCount()
            self.headers_table.insertRow(r)
            self.headers_table.setItem(r, 0, QTableWidgetItem(k))
            self.headers_table.setItem(r, 1, QTableWidgetItem(v))

        fade_in(self.body_view, 220)


def _humanize_size(n: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    size = float(n)
    for u in units:
        if size < 1024 or u == units[-1]:
            return f"{size:.1f} {u}" if u != "B" else f"{int(size)} {u}"
        size /= 1024
    return f"{n} B"
