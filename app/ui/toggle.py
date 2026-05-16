"""Animated toggle switch — a modern replacement for QCheckBox.

Looks and feels like the iOS / Material switch:
  · pill-shaped track that slides between off-state grey and brand-purple
  · circular thumb that animates horizontally with an easing curve
  · subtle drop shadow under the thumb, glow ring on hover
  · keyboard friendly (Space toggles, focus ring around track)
"""
from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QAbstractButton, QSizePolicy


class ToggleSwitch(QAbstractButton):
    """A pure-Qt animated toggle. Drop-in replacement for QCheckBox."""

    toggled_now = Signal(bool)

    # tunable visuals
    _TRACK_OFF       = QColor("#3A3A3A")
    _TRACK_OFF_HOVER = QColor("#4A4A4A")
    _TRACK_ON        = QColor("#FF6C37")
    _TRACK_ON_HOVER  = QColor("#FF8557")
    _THUMB           = QColor("#FFFFFF")
    _FOCUS_RING      = QColor(255, 108, 55, 90)

    def __init__(self, checked: bool = False, parent=None, width: int = 38, height: int = 22):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._w = width
        self._h = height
        self._pad = 3
        # Position of the thumb's centre on the X axis; animated via QPropertyAnimation
        self._thumb_x = self._thumb_x_for(checked)
        self._hover = False
        self._anim = QPropertyAnimation(self, b"thumb_x", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self.toggled.connect(self._animate_to_state)

    # ── geometry helpers ─────────────────────────────────────────
    def sizeHint(self) -> QSize:
        return QSize(self._w, self._h)

    def _thumb_radius(self) -> float:
        return (self._h - 2 * self._pad) / 2

    def _thumb_x_for(self, checked: bool) -> float:
        r = self._thumb_radius()
        if checked:
            return self._w - self._pad - r
        return self._pad + r

    # ── animated property ────────────────────────────────────────
    def get_thumb_x(self) -> float:
        return self._thumb_x

    def set_thumb_x(self, x: float) -> None:
        self._thumb_x = x
        self.update()

    thumb_x = Property(float, get_thumb_x, set_thumb_x)

    def _animate_to_state(self, checked: bool) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._thumb_x)
        self._anim.setEndValue(self._thumb_x_for(checked))
        self._anim.start()
        self.toggled_now.emit(checked)

    # ── interaction ──────────────────────────────────────────────
    def enterEvent(self, e):
        self._hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self.update()
        super().leaveEvent(e)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self.toggle()
            return
        super().keyPressEvent(e)

    # ── paint ────────────────────────────────────────────────────
    def paintEvent(self, _ev) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        # track
        checked = self.isChecked()
        if checked:
            track = self._TRACK_ON_HOVER if self._hover else self._TRACK_ON
        else:
            track = self._TRACK_OFF_HOVER if self._hover else self._TRACK_OFF
        p.setBrush(QBrush(track))
        p.setPen(Qt.NoPen)
        track_rect = QRectF(0, 0, self._w, self._h)
        radius = self._h / 2
        p.drawRoundedRect(track_rect, radius, radius)

        # focus ring (only when keyboard-focused)
        if self.hasFocus():
            ring_pen = QPen(self._FOCUS_RING)
            ring_pen.setWidthF(2.0)
            p.setPen(ring_pen)
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(track_rect.adjusted(-1, -1, 1, 1), radius + 1, radius + 1)

        # subtle thumb shadow
        r = self._thumb_radius()
        p.setPen(Qt.NoPen)
        shadow = QColor(0, 0, 0, 70)
        p.setBrush(shadow)
        p.drawEllipse(QRectF(self._thumb_x - r + 0.5, self._pad + 1.2, r * 2, r * 2))

        # thumb
        p.setBrush(self._THUMB)
        p.drawEllipse(QRectF(self._thumb_x - r, self._pad, r * 2, r * 2))
