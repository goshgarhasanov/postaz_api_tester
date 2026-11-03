"""The Postaz brand logo — a custom-painted widget."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QWidget

from .icons import paint_az_flag


class Logo(QWidget):
    """Compact horizontal lockup: [icon] POSTAZ [az-flag]"""

    def __init__(self, parent: QWidget | None = None, height: int = 30):
        super().__init__(parent)
        self._height = height
        self.setFixedHeight(height + 4)
        self.setMinimumWidth(140)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def sizeHint(self) -> QSize:
        return QSize(160, self._height + 4)

    def paintEvent(self, _ev) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        s = self._height
        # ── mark: rounded square painted in Azerbaijan flag colours ──
        rect = QRectF(2, 2, s, s)
        rad = s * 0.24
        paint_az_flag(p, rect, radius=rad, emblem=False)
        # soft dark scrim keeps the white paper plane legible on all bands
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 38))
        p.drawRoundedRect(rect, rad, rad)

        # paper plane (white, on top)
        path = QPainterPath()
        cx, cy = rect.x(), rect.y()
        path.moveTo(cx + s * 0.24, cy + s * 0.52)
        path.lineTo(cx + s * 0.78, cy + s * 0.26)
        path.lineTo(cx + s * 0.60, cy + s * 0.78)
        path.lineTo(cx + s * 0.48, cy + s * 0.56)
        path.closeSubpath()
        p.setBrush(QColor("#ffffff"))
        p.drawPath(path)

        # ── wordmark ──────────────────────────────────────────
        p.setBrush(Qt.NoBrush)
        # orange → light gradient for the wordmark
        text_grad = QLinearGradient(s + 12, 0, s + 130, 0)
        text_grad.setColorAt(0.0, QColor("#FF8557"))
        text_grad.setColorAt(1.0, QColor("#FFFFFF"))
        pen = QPen(QBrush(text_grad), 1)
        p.setPen(pen)

        font = QFont("Segoe UI", int(s * 0.50))
        font.setWeight(QFont.Black)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1.2)
        p.setFont(font)
        p.drawText(
            QRectF(s + 12, 0, self.width() - s - 14, self.height()),
            Qt.AlignVCenter | Qt.AlignLeft,
            "POSTAZ",
        )
        p.end()
