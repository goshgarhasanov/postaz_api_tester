"""Postman-style request console.

Two-pane drawer:
   ┌──────────────────────────────────────────────────────┐
   │  ›_ Console                          [42]  [ Clear ] │   ← header
   ├──────────────────────────────────────────────────────┤
   │  14:22  GET   /users         200   142 ms · 1.2 KB   │
   │  14:21  POST  /users         201    87 ms · 320 B    │   ← entry list
   │  14:18  GET   /unknown       404    44 ms · 86 B     │
   ├──────────────────────────────────────────────────────┤
   │  ◐ Request   |   Response                            │   ← detail tabs
   │  ─────────────────────────────────────────────────── │
   │  GET https://localhost:8787/users                    │
   │                                                      │
   │  Headers                                             │
   │    Authorization: Bearer …                           │
   │    Accept:        application/json                   │
   │                                                      │
   │  Body                                                │
   │    {"name": "Ada"}                                   │
   └──────────────────────────────────────────────────────┘

Click any row in the upper list → the lower pane shows the full request +
response. Captures everything: method, URL, headers, body, status,
timings, response headers and body."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..database import RequestRecord
from ..http_client import ResponseData
from ..i18n import translator


# ── palette ──────────────────────────────────────────────────────────────
_STATUS_COLORS = {
    1: ("#243245", "#66B5F5"),   # 1xx info
    2: ("#1F3A2F", "#6BBE7B"),   # 2xx success
    3: ("#243245", "#66B5F5"),   # 3xx redirect
    4: ("#3D2F1C", "#FFB400"),   # 4xx client error
    5: ("#3A1F24", "#F45B69"),   # 5xx server error
}

_METHOD_COLORS = {
    "GET":     "#6BBE7B",
    "POST":    "#FFB400",
    "PUT":     "#66B5F5",
    "PATCH":   "#C792EA",
    "DELETE":  "#F45B69",
    "HEAD":    "#80CBC4",
    "OPTIONS": "#80CBC4",
}


@dataclass
class _Entry:
    """Everything we captured about one request — used to repaint the detail
    panel when a row is selected."""
    timestamp: str
    method: str
    url: str
    request_headers: list[dict]
    request_params: list[dict]
    request_body: str
    request_body_type: str
    auth_type: str
    response: ResponseData


class _StatusDelegate(QStyledItemDelegate):
    """Paints a coloured pill instead of plain text for the status column."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        text = index.data(Qt.DisplayRole) or ""
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor("#3A3A3A"))
        elif option.state & QStyle.State_MouseOver:
            painter.fillRect(option.rect, QColor("#2A2A2A"))
        if not text:
            return
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        try:
            code = int(text.split()[0])
            bucket = code // 100
            bg, fg = _STATUS_COLORS.get(bucket, ("#3A3A3A", "#C7C7C7"))
        except (ValueError, IndexError):
            bg, fg = "#3A1F24", "#F45B69"  # ERROR row
        r = option.rect
        pill_w, pill_h = 64, 20
        x = r.x() + 10
        y = r.y() + (r.height() - pill_h) / 2
        painter.setBrush(QColor(bg))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRect(int(x), int(y), pill_w, pill_h), 4, 4)
        font = QFont(option.font); font.setBold(True); font.setPointSizeF(9.0)
        painter.setFont(font)
        painter.setPen(QColor(fg))
        painter.drawText(QRect(int(x), int(y), pill_w, pill_h), Qt.AlignCenter, text)
        painter.restore()


class _MethodDelegate(QStyledItemDelegate):
    """Method column: bold tinted text."""

    def paint(self, painter, option, index) -> None:
        text = (index.data(Qt.DisplayRole) or "").upper()
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor("#3A3A3A"))
        elif option.state & QStyle.State_MouseOver:
            painter.fillRect(option.rect, QColor("#2A2A2A"))
        color = _METHOD_COLORS.get(text, "#C7C7C7")
        font = QFont(option.font); font.setBold(True); font.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
        painter.save()
        painter.setFont(font)
        painter.setPen(QColor(color))
        painter.drawText(option.rect.adjusted(10, 0, -8, 0),
                         Qt.AlignVCenter | Qt.AlignLeft, text)
        painter.restore()


class ConsolePanel(QWidget):
    """Live, two-pane request log."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("consolePanel")
        self._entries: list[_Entry] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── header bar ─────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("consoleHeader")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 8, 12, 8)
        hl.setSpacing(8)
        self.title = QLabel("›_ " + self._tr_console())
        self.title.setObjectName("consoleTitle")
        hl.addWidget(self.title)
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

        # ── body: split between list and detail viewer ─────────────
        split = QSplitter(Qt.Vertical)
        split.setHandleWidth(1)
        split.setChildrenCollapsible(False)

        # 1. Entry list
        self.table = QTableWidget(0, 5)
        self.table.setObjectName("consoleTable")
        self.table.setHorizontalHeaderLabels([
            self._tr_col("time"), self._tr_col("method"), self._tr_col("url"),
            self._tr_col("status"), self._tr_col("dur_size"),
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.setMouseTracking(True)
        self.table.setItemDelegateForColumn(1, _MethodDelegate(self.table))
        self.table.setItemDelegateForColumn(3, _StatusDelegate(self.table))
        self.table.itemSelectionChanged.connect(self._on_select)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        split.addWidget(self.table)

        # 2. Detail viewer
        self.detail = self._build_detail()
        split.addWidget(self.detail)

        split.setSizes([200, 240])
        outer.addWidget(split, 1)

        translator.language_changed.connect(self._retranslate)

    # ── detail viewer ────────────────────────────────────────────────
    def _build_detail(self) -> QWidget:
        wrap = QFrame()
        wrap.setObjectName("consoleDetail")
        layout = QVBoxLayout(wrap)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Request tab
        self.req_view = QPlainTextEdit()
        self.req_view.setReadOnly(True)
        self.req_view.setFont(QFont("JetBrains Mono", 10))
        self.req_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.req_view.setPlaceholderText(self._tr_empty())
        self.tabs.addTab(self._pad(self.req_view), self._tr_tab_req())

        # Response tab
        self.resp_view = QPlainTextEdit()
        self.resp_view.setReadOnly(True)
        self.resp_view.setFont(QFont("JetBrains Mono", 10))
        self.resp_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.resp_view.setPlaceholderText(self._tr_empty())
        self.tabs.addTab(self._pad(self.resp_view), self._tr_tab_resp())

        layout.addWidget(self.tabs)
        return wrap

    def _pad(self, widget: QWidget) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(8, 8, 8, 8)
        l.addWidget(widget)
        return w

    # ── translations ─────────────────────────────────────────────────
    def _tr_console(self) -> str:
        return {"en": "Console", "az": "Konsol", "tr": "Konsol"}[translator.language]

    def _tr_clear(self) -> str:
        return {"en": "Clear", "az": "Təmizlə", "tr": "Temizle"}[translator.language]

    def _tr_col(self, key: str) -> str:
        labels = {
            "en": {"time": "Time", "method": "Method", "url": "URL", "status": "Status", "dur_size": "Duration · Size"},
            "az": {"time": "Vaxt", "method": "Metod", "url": "URL", "status": "Status", "dur_size": "Müddət · Ölçü"},
            "tr": {"time": "Saat", "method": "Metot", "url": "URL", "status": "Durum", "dur_size": "Süre · Boyut"},
        }
        return labels[translator.language][key]

    def _tr_tab_req(self) -> str:
        return {"en": "Request", "az": "Sorğu", "tr": "İstek"}[translator.language]

    def _tr_tab_resp(self) -> str:
        return {"en": "Response", "az": "Cavab", "tr": "Yanıt"}[translator.language]

    def _tr_empty(self) -> str:
        return {"en": "Select a row above to see the full request / response.",
                "az": "Tam sorğunu və cavabı görmək üçün yuxarıdan bir sətir seçin.",
                "tr": "Tam isteği ve yanıtı görmek için yukarıdan bir satır seçin."}[translator.language]

    def _retranslate(self, _l: str | None = None) -> None:
        self.title.setText("›_ " + self._tr_console())
        self.btn_clear.setText(self._tr_clear())
        self.table.setHorizontalHeaderLabels([
            self._tr_col("time"), self._tr_col("method"), self._tr_col("url"),
            self._tr_col("status"), self._tr_col("dur_size"),
        ])
        self.tabs.setTabText(0, self._tr_tab_req())
        self.tabs.setTabText(1, self._tr_tab_resp())
        self.req_view.setPlaceholderText(self._tr_empty())
        self.resp_view.setPlaceholderText(self._tr_empty())

    # ── public API ───────────────────────────────────────────────────
    def push(self, rec: RequestRecord, resp: ResponseData) -> None:
        """Add one entry at the top — newest first. Captures everything."""
        entry = _Entry(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            method=rec.method.upper(),
            url=rec.url,
            request_headers=list(rec.headers),
            request_params=list(rec.params),
            request_body=rec.body,
            request_body_type=rec.body_type,
            auth_type=rec.auth_type,
            response=resp,
        )
        self._entries.insert(0, entry)

        status_text = f"{resp.status_code} {resp.reason}".strip() if resp.ok else "ERROR"
        size_text = _humanize_bytes(resp.size_bytes) if resp.ok else "—"
        dur_size = f"{resp.duration_ms} ms · {size_text}"

        self.table.insertRow(0)
        cells = [entry.timestamp, entry.method, entry.url, status_text, dur_size]
        for col, text in enumerate(cells):
            item = QTableWidgetItem(text)
            if col == 0:
                item.setForeground(QColor("#A0A0A0"))
                item.setFont(QFont("JetBrains Mono", 9))
            elif col == 2:
                item.setForeground(QColor("#E1E1E1"))
            elif col == 4:
                item.setForeground(QColor("#A0A0A0"))
            item.setToolTip(text)
            self.table.setItem(0, col, item)

        # Cap the buffer at 500 rows so memory stays bounded.
        if self.table.rowCount() > 500:
            self.table.removeRow(self.table.rowCount() - 1)
            self._entries.pop()
        self.counter.setText(str(self.table.rowCount()))

        # Auto-focus the newest entry so the detail pane updates.
        self.table.selectRow(0)

    def clear(self) -> None:
        self.table.setRowCount(0)
        self._entries.clear()
        self.counter.setText("0")
        self.req_view.setPlainText("")
        self.resp_view.setPlainText("")

    # ── selection → detail panel ─────────────────────────────────────
    def _on_select(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        idx = rows[0].row()
        if 0 <= idx < len(self._entries):
            self._render_detail(self._entries[idx])

    def _render_detail(self, e: _Entry) -> None:
        # Request view
        req_lines = [f"{e.method} {e.url}", ""]
        if e.request_params:
            req_lines.append("Query Params")
            for p in e.request_params:
                if not p.get("enabled", True):
                    continue
                k = p.get("key", ""); v = p.get("value", "")
                if k:
                    req_lines.append(f"  {k}: {v}")
            req_lines.append("")
        req_lines.append("Headers")
        if e.request_headers:
            for h in e.request_headers:
                if not h.get("enabled", True):
                    continue
                k = h.get("key", ""); v = h.get("value", "")
                if k:
                    req_lines.append(f"  {k}: {v}")
        else:
            req_lines.append("  (none)")
        if e.auth_type and e.auth_type != "none":
            req_lines.append("")
            req_lines.append(f"Auth: {e.auth_type}")
        if e.request_body:
            req_lines.append("")
            req_lines.append(f"Body  ({e.request_body_type})")
            req_lines.append(_pretty_if_json(e.request_body))
        self.req_view.setPlainText("\n".join(req_lines))

        # Response view
        r = e.response
        resp_lines: list[str] = []
        if r.ok:
            resp_lines.append(f"HTTP {r.status_code} {r.reason}".rstrip())
            resp_lines.append(f"{r.duration_ms} ms · {_humanize_bytes(r.size_bytes)}")
            if r.final_url and r.final_url != e.url:
                resp_lines.append(f"Final URL: {r.final_url}")
            resp_lines.append("")
            resp_lines.append("Headers")
            if r.headers:
                for k, v in r.headers.items():
                    resp_lines.append(f"  {k}: {v}")
            else:
                resp_lines.append("  (none)")
            resp_lines.append("")
            resp_lines.append("Body")
            body = r.body_text
            if r.is_json:
                body = _pretty_if_json(body)
            resp_lines.append(body if body else "(empty)")
        else:
            resp_lines.append("ERROR")
            resp_lines.append(r.error or "(unknown)")
            if r.duration_ms:
                resp_lines.append("")
                resp_lines.append(f"Failed after {r.duration_ms} ms")
        self.resp_view.setPlainText("\n".join(resp_lines))


# ── helpers ──────────────────────────────────────────────────────────────
def _humanize_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    size = float(n)
    for u in units:
        if size < 1024 or u == units[-1]:
            return f"{size:.1f} {u}" if u != "B" else f"{int(size)} {u}"
        size /= 1024
    return f"{n} B"


def _pretty_if_json(text: str) -> str:
    """Try to pretty-print JSON. Return original text on any failure."""
    if not text:
        return ""
    stripped = text.strip()
    if not (stripped.startswith("{") or stripped.startswith("[")):
        return text
    try:
        return json.dumps(json.loads(stripped), indent=2, ensure_ascii=False)
    except Exception:
        return text
