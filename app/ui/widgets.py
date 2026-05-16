"""Reusable UI building blocks.

Everything here is widget-level — no business logic, no DB. These pieces
are shared by sidebar / editor / response panels:
  · `Spinner`        — round arc that rotates while loading
  · `StatusBadge`    — coloured pill showing HTTP status
  · `PrimaryButton`  — gradient call-to-action with drop shadow
  · `GhostButton`    — subtle bordered button for secondary actions
  · `IconButton`     — square 28×28 toolbar-style icon button
  · `Toast`          — auto-dismissing floating notification
  · `KeyValueTable`  — editable rows of `{enabled, key, value, description}`
  · `LoaderOverlay`  — full-panel translucent loading state
"""
from __future__ import annotations

import math

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRect,
    QRectF,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QFont,
    QGuiApplication,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .animations import fade_in, fade_out


# ── Spinner ───────────────────────────────────────────────────────────────
class Spinner(QWidget):
    """A smooth circular loading indicator.

    Repaint frequency is a 16 ms QTimer — slow enough not to wake the CPU
    while idle, fast enough (≈60 fps) to feel modern. Paint with antialiasing
    on a transparent background so it composites cleanly over any color."""

    def __init__(self, parent: QWidget | None = None, size: int = 18, color: str = "#FF6C37"):
        super().__init__(parent)
        self._size = size
        self._color = QColor(color)
        self._angle = 0
        self.setFixedSize(size, size)
        self._timer = QTimer(self)
        self._timer.setInterval(16)  # ~60fps
        self._timer.timeout.connect(self._tick)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()

    def start(self) -> None:
        self.show()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

    def _tick(self) -> None:
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, _ev) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(2, 2, self._size - 4, self._size - 4)
        # background track
        track_pen = QPen(QColor(255, 255, 255, 35))
        track_pen.setWidthF(2.2)
        p.setPen(track_pen)
        p.drawArc(rect, 0, 360 * 16)
        # spinning arc
        pen = QPen(self._color)
        pen.setWidthF(2.4)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, int(-self._angle * 16), 110 * 16)


# ── Status badge ──────────────────────────────────────────────────────────
class StatusBadge(QLabel):
    """The little coloured pill on the response meta bar.

    Bucket → color rule:
        2xx → green   (success)
        3xx → blue    (redirect)
        4xx → orange  (client error)
        5xx → red     (server error)
        net error → red"""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Segoe UI", 9, QFont.DemiBold))
        self.setMinimumWidth(72)
        self.setFixedHeight(24)
        self.clear_status()

    def clear_status(self) -> None:
        self.setText("—")
        self._apply("#3A3A3A", "#A0A0A0")

    def set_status(self, code: int, reason: str = "") -> None:
        text = f"{code} {reason}".strip()
        self.setText(text)
        if 200 <= code < 300:
            self._apply("#1F3A2F", "#6BBE7B")
        elif 300 <= code < 400:
            self._apply("#243245", "#66B5F5")
        elif 400 <= code < 500:
            self._apply("#3D2F1C", "#FFB400")
        elif code >= 500:
            self._apply("#3A1F24", "#F45B69")
        else:
            self._apply("#3A3A3A", "#A0A0A0")

    def set_error(self) -> None:
        self.setText("ERROR")
        self._apply("#3A1F24", "#F45B69")

    def _apply(self, bg: str, fg: str) -> None:
        self.setStyleSheet(
            f"background:{bg}; color:{fg}; border-radius:12px; padding:0 12px;"
        )


# ── Animated primary button ───────────────────────────────────────────────
class PrimaryButton(QPushButton):
    """Brand call-to-action button.

    Gradient fill (purple → deep purple), bold uppercase-ish weight, and a
    soft brand-coloured drop shadow so it feels like it's lifting off the
    surface. Disabled state in QSS turns the shadow visually-flat."""

    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("primaryButton")
        self.setMinimumHeight(44)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(255, 108, 55, 120))
        self.setGraphicsEffect(shadow)


class GhostButton(QPushButton):
    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("ghostButton")
        self.setMinimumHeight(32)


class IconButton(QToolButton):
    def __init__(self, text: str = "", tip: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setText(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("iconButton")
        self.setToolTip(tip)
        self.setMinimumSize(28, 28)


# ── Toast notification ────────────────────────────────────────────────────
class Toast(QLabel):
    """Floating notification — fades in, holds, fades out."""

    KINDS = {
        "info": ("#202130", "#cfd2ff", "#3a3d70"),
        "success": ("#16322a", "#7fe6b3", "#1f5e48"),
        "error": ("#321a20", "#ff8090", "#6a2730"),
        "warn": ("#322a1a", "#f5c97a", "#6b4e20"),
    }

    def __init__(self, parent: QWidget, text: str, kind: str = "info", duration: int = 2400):
        super().__init__(parent)
        self.setText(text)
        self.setObjectName("toast")
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(False)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        bg, fg, border = self.KINDS.get(kind, self.KINDS["info"])
        self.setStyleSheet(
            f"background:{bg}; color:{fg}; border:1px solid {border};"
            f"border-radius:10px; padding:10px 18px; font-weight:500;"
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 140))
        self.setGraphicsEffect(shadow)

        self.adjustSize()
        self._position()
        fade_in(self, 200)
        QTimer.singleShot(duration, self._dismiss)

    def _position(self) -> None:
        p = self.parentWidget()
        if p is None:
            return
        x = (p.width() - self.width()) // 2
        y = p.height() - self.height() - 32
        self.move(x, y)

    def _dismiss(self) -> None:
        fade_out(self, 220, on_done=self.deleteLater)


def show_toast(parent: QWidget, text: str, kind: str = "info") -> None:
    Toast(parent, text, kind).show()


# ── Key-value list (headers / params) ─────────────────────────────────────
from PySide6.QtWidgets import (
    QHeaderView,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
)
from .toggle import ToggleSwitch


class KeyValueTable(QTableWidget):
    """Generic table used for Headers and Query Params.

    Self-managing: the last row is always blank so the user can type into
    it without clicking a "+" button. As soon as they fill a key in the
    trailing row, a new blank row spawns below it.
    Empties (no key AND no value) are filtered out by `get_rows()`."""

    changed = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(0, 4, parent)
        self.setHorizontalHeaderLabels(["", "Key", "Value", "Description"])
        self.verticalHeader().setVisible(False)
        self.setObjectName("kvTable")
        self.setShowGrid(False)
        self.setAlternatingRowColors(False)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.AllEditTriggers)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        hh = self.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        self.setColumnWidth(0, 64)              # 38px switch + breathing room
        self.verticalHeader().setDefaultSectionSize(42)  # rows that breathe
        self.itemChanged.connect(self._on_item_changed)
        self._loading = False
        self._ensure_blank_row()

    def _on_item_changed(self, _item) -> None:
        if self._loading:
            return
        self._ensure_blank_row()
        self.changed.emit()

    def _ensure_blank_row(self) -> None:
        if self.rowCount() == 0:
            self._add_row({"enabled": True, "key": "", "value": "", "description": ""})
            return
        last = self.rowCount() - 1
        key_item = self.item(last, 1)
        if key_item and key_item.text().strip():
            self._add_row({"enabled": True, "key": "", "value": "", "description": ""})

    def _add_row(self, data: dict) -> None:
        """Append one row.

        The first cell hosts an animated `ToggleSwitch` (modern replacement
        for QCheckBox). The switch is centred in its column with a tiny
        transparent wrapper so the click target feels generous."""
        self._loading = True
        r = self.rowCount()
        self.insertRow(r)
        sw = ToggleSwitch(checked=bool(data.get("enabled", True)))
        sw.setToolTip("Enable / disable this entry")
        sw.toggled_now.connect(lambda _v: self.changed.emit())
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(wrapper)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(Qt.AlignCenter)
        lay.addWidget(sw)
        self.setCellWidget(r, 0, wrapper)
        for col, key in [(1, "key"), (2, "value"), (3, "description")]:
            item = QTableWidgetItem(str(data.get(key, "")))
            self.setItem(r, col, item)
        self._loading = False

    def set_rows(self, rows: list[dict]) -> None:
        self._loading = True
        self.setRowCount(0)
        for row in rows:
            self._add_row(row)
        self._loading = False
        self._ensure_blank_row()

    def get_rows(self) -> list[dict]:
        out: list[dict] = []
        for r in range(self.rowCount()):
            wrapper = self.cellWidget(r, 0)
            sw = wrapper.findChild(ToggleSwitch) if wrapper else None
            enabled = bool(sw.isChecked()) if sw else True
            key = (self.item(r, 1).text() if self.item(r, 1) else "").strip()
            value = (self.item(r, 2).text() if self.item(r, 2) else "")
            desc = (self.item(r, 3).text() if self.item(r, 3) else "")
            if not key and not value:
                continue
            out.append({"enabled": enabled, "key": key, "value": value, "description": desc})
        return out


# ── Animated overlay loader ───────────────────────────────────────────────
class LoaderOverlay(QWidget):
    """Full-panel dim layer + centred spinner.

    Painted on top of the response viewer while the HTTP worker is busy.
    Sized to its parent in `resizeEvent` so it always covers the surface
    no matter how the splitter is dragged."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: rgba(20, 20, 20, 150);")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.spinner = Spinner(self, size=42, color="#FF6C37")
        self.spinner.setFixedSize(42, 42)
        self.label = QLabel("Sending request…")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: #E1E1E1; font-size: 13px; margin-top: 14px;")
        layout.addWidget(self.spinner, alignment=Qt.AlignCenter)
        layout.addWidget(self.label)
        self.hide()

    def start(self, text: str = "Sending request…") -> None:
        self.label.setText(text)
        self.resize(self.parentWidget().size())
        self.raise_()
        self.show()
        self.spinner.start()
        fade_in(self, 160)

    def stop(self) -> None:
        self.spinner.stop()
        fade_out(self, 180, on_done=self.hide)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if self.parentWidget():
            self.resize(self.parentWidget().size())
