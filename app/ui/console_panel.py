"""Postman-style request console.

Lives as a collapsible drawer at the bottom of the main window. Every time
a request finishes, the main window pushes the result here via `push()`.
The console keeps a rolling buffer of the last 500 entries — enough to
review what just happened without ballooning memory."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..http_client import ResponseData
from ..i18n import t, translator

_STATUS_COLORS = {
    1: ("#243245", "#7c9eff"),   # 1xx info
    2: ("#1e3a2f", "#5ed29b"),   # 2xx success
    3: ("#243245", "#6fb8ff"),   # 3xx redirect
    4: ("#3d2f1c", "#f4b860"),   # 4xx client error
    5: ("#3a1f24", "#ff6e7c"),   # 5xx server error
}

_METHOD_COLORS = {
    "GET":     "#5ed29b",
    "POST":    "#f4b860",
    "PUT":     "#6fb8ff",
    "PATCH":   "#bda6ff",
    "DELETE":  "#ff8090",
    "HEAD":    "#a89bff",
    "OPTIONS": "#a89bff",
}


class _StatusDelegate(QStyledItemDelegate):
    """Paints a coloured pill instead of plain text for the status column."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        text = index.data(Qt.DisplayRole) or ""
        if not text:
            return super().paint(painter, option, index)

        # Hover/selected background — same shading as the rest of the table.
        if option.state & (option.state.__class__(0x00000020) if False else option.state.__class__(0)):
            pass  # placeholder to silence static analysis

        from PySide6.QtWidgets import QStyle
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor("#1c1d2e"))
        elif option.state & QStyle.State_MouseOver:
            painter.fillRect(option.rect, QColor("#15161f"))

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        try:
            code = int(text.split()[0])
        except (ValueError, IndexError):
            bg, fg = "#262842", "#bda6ff"
        else:
            bucket = code // 100
            bg, fg = _STATUS_COLORS.get(bucket, ("#262842", "#bda6ff"))

        r = option.rect
        pill_w = 64
        pill_h = 20
        x = r.x() + 10
        y = r.y() + (r.height() - pill_h) / 2
        painter.setBrush(QColor(bg))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRect(int(x), int(y), int(pill_w), int(pill_h)), 4, 4)
        font = QFont(option.font)
        font.setBold(True)
        font.setPointSizeF(9.0)
        painter.setFont(font)
        painter.setPen(QColor(fg))
        painter.drawText(QRect(int(x), int(y), int(pill_w), int(pill_h)),
                         Qt.AlignCenter, text)
        painter.restore()


class _MethodDelegate(QStyledItemDelegate):
    """Method column: tinted bold text, not a full pill (keeps the row compact)."""

    def paint(self, painter, option, index) -> None:
        text = (index.data(Qt.DisplayRole) or "").upper()
        from PySide6.QtWidgets import QStyle
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor("#1c1d2e"))
        elif option.state & QStyle.State_MouseOver:
            painter.fillRect(option.rect, QColor("#15161f"))
        color = _METHOD_COLORS.get(text, "#bda6ff")
        font = QFont(option.font)
        font.setBold(True)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
        painter.save()
        painter.setFont(font)
        painter.setPen(QColor(color))
        painter.drawText(option.rect.adjusted(10, 0, -8, 0), Qt.AlignVCenter | Qt.AlignLeft, text)
        painter.restore()


class ConsolePanel(QWidget):
    """The collapsible request log at the bottom of the window."""

    entry_double_clicked = Signal(int)   # history-style id when the user wants details

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("consolePanel")
        self._next_local_id = 0
        self._rows: list[dict] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── header bar ─────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("consoleHeader")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 8, 12, 8)
        hl.setSpacing(8)

        title = QLabel("›_ " + self._tr_console())
        title.setObjectName("consoleTitle")
        hl.addWidget(title)

        self.counter = QLabel("0")
        self.counter.setObjectName("consoleCounter")
        hl.addWidget(self.counter)

        hl.addStretch()

        self.btn_clear = QPushButton(self._tr_clear())
        self.btn_clear.setObjectName("clearHistoryButton")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear)
        hl.addWidget(self.btn_clear)

        outer.addWidget(header)

        # ── table ──────────────────────────────────────────────────
        self.table = QTableWidget(0, 5)
        self.table.setObjectName("consoleTable")
        self.table.setHorizontalHeaderLabels([
            self._tr_col("time"), self._tr_col("method"), self._tr_col("url"),
            self._tr_col("status"), self._tr_col("dur_size"),
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.setMouseTracking(True)
        self.table.setItemDelegateForColumn(1, _MethodDelegate(self.table))
        self.table.setItemDelegateForColumn(3, _StatusDelegate(self.table))
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)   # time
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)   # method
        hh.setSectionResizeMode(2, QHeaderView.Stretch)            # url
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)   # status
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)   # duration / size
        outer.addWidget(self.table, 1)

        translator.language_changed.connect(self._retranslate)

    # ── translations ─────────────────────────────────────────────────
    def _tr_console(self) -> str:
        return {"en": "Console", "az": "Konsol", "tr": "Konsol"}[translator.language]

    def _tr_clear(self) -> str:
        return {"en": "Clear", "az": "Təmizlə", "tr": "Temizle"}[translator.language]

    def _tr_col(self, key: str) -> str:
        labels = {
            "en":  {"time": "Time",  "method": "Method", "url": "URL", "status": "Status", "dur_size": "Duration · Size"},
            "az":  {"time": "Vaxt",  "method": "Metod",  "url": "URL", "status": "Status", "dur_size": "Müddət · Ölçü"},
            "tr":  {"time": "Saat",  "method": "Metot",  "url": "URL", "status": "Durum",  "dur_size": "Süre · Boyut"},
        }
        return labels[translator.language][key]

    def _retranslate(self, _l: str | None = None) -> None:
        for child in self.findChildren(QLabel):
            if child.objectName() == "consoleTitle":
                child.setText("›_ " + self._tr_console())
        self.btn_clear.setText(self._tr_clear())
        self.table.setHorizontalHeaderLabels([
            self._tr_col("time"), self._tr_col("method"), self._tr_col("url"),
            self._tr_col("status"), self._tr_col("dur_size"),
        ])

    # ── public API ───────────────────────────────────────────────────
    def push(self, method: str, url: str, resp: ResponseData) -> None:
        """Add one row at the top — newest first."""
        ts = datetime.now().strftime("%H:%M:%S")
        status_text = f"{resp.status_code} {resp.reason}".strip() if resp.ok else "ERROR"
        size_text = _humanize_bytes(resp.size_bytes) if resp.ok else "—"
        dur_size = f"{resp.duration_ms} ms · {size_text}"

        self.table.insertRow(0)
        for col, text in enumerate([ts, method.upper(), url, status_text, dur_size]):
            item = QTableWidgetItem(text)
            if col == 0:
                item.setForeground(QColor("#7e8299"))
                f = QFont("JetBrains Mono", 9)
                item.setFont(f)
            elif col == 2:
                item.setForeground(QColor("#d8dcff"))
            elif col == 4:
                item.setForeground(QColor("#a4a7c2"))
            item.setToolTip(text)
            self.table.setItem(0, col, item)

        self._rows.insert(0, {"method": method, "url": url, "status": resp.status_code})
        # Cap the buffer at 500 rows so memory stays bounded.
        if self.table.rowCount() > 500:
            self.table.removeRow(self.table.rowCount() - 1)
            self._rows.pop()
        self._update_counter()

    def clear(self) -> None:
        self.table.setRowCount(0)
        self._rows.clear()
        self._update_counter()

    def _update_counter(self) -> None:
        self.counter.setText(str(self.table.rowCount()))


def _humanize_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    size = float(n)
    for u in units:
        if size < 1024 or u == units[-1]:
            return f"{size:.1f} {u}" if u != "B" else f"{int(size)} {u}"
        size /= 1024
    return f"{n} B"
