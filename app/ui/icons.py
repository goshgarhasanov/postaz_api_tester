"""Programmatically painted icons — vector-clean, theme-aware, no external assets."""
from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, QRectF, QSize, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)


def _pix(size: int = 22, color: str = "#c9cce0", draw=None) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    pen = QPen(QColor(color))
    pen.setWidthF(1.8)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    if draw:
        draw(p, size, color)
    p.end()
    return pm


def _icon(draw, size: int = 22, color: str = "#c9cce0") -> QIcon:
    return QIcon(_pix(size, color, draw))


# ── individual painters ──────────────────────────────────────────────
def _plus(p: QPainter, s: int, _c: str) -> None:
    p.drawLine(s // 2, int(s * 0.25), s // 2, int(s * 0.75))
    p.drawLine(int(s * 0.25), s // 2, int(s * 0.75), s // 2)


def _trash(p: QPainter, s: int, _c: str) -> None:
    # lid
    p.drawLine(int(s * 0.22), int(s * 0.30), int(s * 0.78), int(s * 0.30))
    # handle
    p.drawLine(int(s * 0.40), int(s * 0.22), int(s * 0.60), int(s * 0.22))
    p.drawLine(int(s * 0.40), int(s * 0.22), int(s * 0.40), int(s * 0.30))
    p.drawLine(int(s * 0.60), int(s * 0.22), int(s * 0.60), int(s * 0.30))
    # body
    path = QPainterPath()
    path.moveTo(s * 0.28, s * 0.32)
    path.lineTo(s * 0.34, s * 0.80)
    path.lineTo(s * 0.66, s * 0.80)
    path.lineTo(s * 0.72, s * 0.32)
    p.drawPath(path)
    p.drawLine(int(s * 0.42), int(s * 0.40), int(s * 0.44), int(s * 0.72))
    p.drawLine(int(s * 0.58), int(s * 0.40), int(s * 0.56), int(s * 0.72))


def _send(p: QPainter, s: int, c: str) -> None:
    # paper-plane / send arrow
    path = QPainterPath()
    path.moveTo(s * 0.18, s * 0.50)
    path.lineTo(s * 0.82, s * 0.22)
    path.lineTo(s * 0.62, s * 0.82)
    path.lineTo(s * 0.50, s * 0.55)
    path.closeSubpath()
    p.setBrush(QColor(c))
    p.drawPath(path)
    p.setBrush(Qt.NoBrush)
    p.drawLine(int(s * 0.50), int(s * 0.55), int(s * 0.82), int(s * 0.22))


def _save(p: QPainter, s: int, _c: str) -> None:
    # floppy disk silhouette
    p.drawRoundedRect(QRectF(s * 0.22, s * 0.22, s * 0.56, s * 0.56), 3, 3)
    p.drawRect(QRectF(s * 0.34, s * 0.22, s * 0.32, s * 0.20))
    p.drawRect(QRectF(s * 0.30, s * 0.52, s * 0.40, s * 0.24))


def _folder(p: QPainter, s: int, c: str) -> None:
    path = QPainterPath()
    path.moveTo(s * 0.18, s * 0.30)
    path.lineTo(s * 0.42, s * 0.30)
    path.lineTo(s * 0.48, s * 0.38)
    path.lineTo(s * 0.82, s * 0.38)
    path.lineTo(s * 0.82, s * 0.74)
    path.lineTo(s * 0.18, s * 0.74)
    path.closeSubpath()
    p.drawPath(path)


def _gear(p: QPainter, s: int, _c: str) -> None:
    center = QPointF(s / 2, s / 2)
    inner = s * 0.16
    outer = s * 0.30
    from math import cos, pi, sin
    poly = QPolygonF()
    teeth = 8
    for i in range(teeth * 2):
        ang = i * pi / teeth
        r = outer if i % 2 == 0 else outer * 0.78
        poly.append(QPointF(center.x() + r * cos(ang), center.y() + r * sin(ang)))
    p.drawPolygon(poly)
    p.drawEllipse(center, inner, inner)


def _moon(p: QPainter, s: int, _c: str) -> None:
    path = QPainterPath()
    path.moveTo(s * 0.72, s * 0.25)
    path.arcTo(QRectF(s * 0.20, s * 0.20, s * 0.60, s * 0.60), 60, 240)
    path.closeSubpath()
    p.drawPath(path)


def _sun(p: QPainter, s: int, _c: str) -> None:
    center = QPointF(s / 2, s / 2)
    p.drawEllipse(center, s * 0.16, s * 0.16)
    from math import cos, pi, sin
    for i in range(8):
        ang = i * pi / 4
        x1 = center.x() + s * 0.24 * cos(ang)
        y1 = center.y() + s * 0.24 * sin(ang)
        x2 = center.x() + s * 0.34 * cos(ang)
        y2 = center.y() + s * 0.34 * sin(ang)
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))


def _search(p: QPainter, s: int, _c: str) -> None:
    p.drawEllipse(QPointF(s * 0.42, s * 0.42), s * 0.22, s * 0.22)
    p.drawLine(int(s * 0.60), int(s * 0.60), int(s * 0.80), int(s * 0.80))


def _globe(p: QPainter, s: int, _c: str) -> None:
    center = QPointF(s / 2, s / 2)
    r = s * 0.32
    p.drawEllipse(center, r, r)
    p.drawEllipse(QRectF(center.x() - r * 0.5, center.y() - r, r, r * 2))
    p.drawLine(int(center.x() - r), int(center.y()), int(center.x() + r), int(center.y()))


def _clock(p: QPainter, s: int, _c: str) -> None:
    center = QPointF(s / 2, s / 2)
    r = s * 0.30
    p.drawEllipse(center, r, r)
    p.drawLine(center, QPointF(center.x(), center.y() - r * 0.6))
    p.drawLine(center, QPointF(center.x() + r * 0.45, center.y()))


def _info(p: QPainter, s: int, _c: str) -> None:
    p.drawEllipse(QPointF(s / 2, s / 2), s * 0.30, s * 0.30)
    p.drawLine(int(s / 2), int(s * 0.42), int(s / 2), int(s * 0.66))
    p.drawPoint(int(s / 2), int(s * 0.34))


def _chevron_down(p: QPainter, s: int, _c: str) -> None:
    p.drawLine(int(s * 0.30), int(s * 0.42), int(s * 0.50), int(s * 0.62))
    p.drawLine(int(s * 0.70), int(s * 0.42), int(s * 0.50), int(s * 0.62))


def _close(p: QPainter, s: int, _c: str) -> None:
    p.drawLine(int(s * 0.30), int(s * 0.30), int(s * 0.70), int(s * 0.70))
    p.drawLine(int(s * 0.70), int(s * 0.30), int(s * 0.30), int(s * 0.70))


def _export(p: QPainter, s: int, _c: str) -> None:
    # arrow pointing up out of a tray
    p.drawLine(int(s * 0.50), int(s * 0.20), int(s * 0.50), int(s * 0.55))
    p.drawLine(int(s * 0.50), int(s * 0.20), int(s * 0.38), int(s * 0.32))
    p.drawLine(int(s * 0.50), int(s * 0.20), int(s * 0.62), int(s * 0.32))
    p.drawLine(int(s * 0.22), int(s * 0.60), int(s * 0.22), int(s * 0.78))
    p.drawLine(int(s * 0.22), int(s * 0.78), int(s * 0.78), int(s * 0.78))
    p.drawLine(int(s * 0.78), int(s * 0.78), int(s * 0.78), int(s * 0.60))


def _import(p: QPainter, s: int, _c: str) -> None:
    # arrow pointing down INTO a tray (mirror of _export)
    p.drawLine(int(s * 0.50), int(s * 0.20), int(s * 0.50), int(s * 0.55))
    p.drawLine(int(s * 0.50), int(s * 0.55), int(s * 0.38), int(s * 0.42))
    p.drawLine(int(s * 0.50), int(s * 0.55), int(s * 0.62), int(s * 0.42))
    p.drawLine(int(s * 0.22), int(s * 0.60), int(s * 0.22), int(s * 0.78))
    p.drawLine(int(s * 0.22), int(s * 0.78), int(s * 0.78), int(s * 0.78))
    p.drawLine(int(s * 0.78), int(s * 0.78), int(s * 0.78), int(s * 0.60))


def _power(p: QPainter, s: int, _c: str) -> None:
    p.drawArc(QRectF(s * 0.22, s * 0.22, s * 0.56, s * 0.56), 70 * 16, 320 * 16)
    p.drawLine(int(s / 2), int(s * 0.18), int(s / 2), int(s * 0.45))


def _copy(p: QPainter, s: int, _c: str) -> None:
    p.drawRoundedRect(QRectF(s * 0.32, s * 0.20, s * 0.46, s * 0.46), 2, 2)
    p.drawRoundedRect(QRectF(s * 0.20, s * 0.34, s * 0.46, s * 0.46), 2, 2)


# ── public ────────────────────────────────────────────────────────────
def icon_plus(color: str = "#c9cce0") -> QIcon:        return _icon(_plus, color=color)
def icon_trash(color: str = "#c9cce0") -> QIcon:       return _icon(_trash, color=color)
def icon_send(color: str = "#ffffff") -> QIcon:        return _icon(_send, color=color)
def icon_save(color: str = "#c9cce0") -> QIcon:        return _icon(_save, color=color)
def icon_folder(color: str = "#c9cce0") -> QIcon:      return _icon(_folder, color=color)
def icon_gear(color: str = "#c9cce0") -> QIcon:        return _icon(_gear, color=color)
def icon_moon(color: str = "#c9cce0") -> QIcon:        return _icon(_moon, color=color)
def icon_sun(color: str = "#c9cce0") -> QIcon:         return _icon(_sun, color=color)
def icon_search(color: str = "#8b8fab") -> QIcon:      return _icon(_search, color=color)
def icon_globe(color: str = "#c9cce0") -> QIcon:       return _icon(_globe, color=color)
def icon_clock(color: str = "#c9cce0") -> QIcon:       return _icon(_clock, color=color)
def icon_info(color: str = "#c9cce0") -> QIcon:        return _icon(_info, color=color)
def icon_chevron(color: str = "#c9cce0") -> QIcon:     return _icon(_chevron_down, color=color)
def icon_close(color: str = "#c9cce0") -> QIcon:       return _icon(_close, color=color)
def icon_export(color: str = "#c9cce0") -> QIcon:      return _icon(_export, color=color)
def icon_import(color: str = "#c9cce0") -> QIcon:      return _icon(_import, color=color)
def icon_power(color: str = "#c9cce0") -> QIcon:       return _icon(_power, color=color)
def icon_copy(color: str = "#c9cce0") -> QIcon:        return _icon(_copy, color=color)


# ── Azerbaijan flag (reusable painter) ────────────────────────────────
def _draw_star(p: QPainter, center: QPointF, radius: float, color: QColor, points: int = 8) -> None:
    """An 8-pointed star (octagram) — the emblem on Azerbaijan's flag."""
    from math import cos, pi, sin
    poly = QPolygonF()
    inner = radius * 0.46
    for i in range(points * 2):
        ang = -pi / 2 + i * pi / points
        r = radius if i % 2 == 0 else inner
        poly.append(QPointF(center.x() + r * cos(ang), center.y() + r * sin(ang)))
    p.setPen(Qt.NoPen)
    p.setBrush(color)
    p.drawPolygon(poly)


def paint_az_flag(p: QPainter, rect: QRectF, radius: float = 0.0, emblem: bool = True) -> None:
    """Paint the flag of Azerbaijan inside `rect`.

    Three equal horizontal bands — cyan-blue, red, green. When `emblem` is
    True a white crescent and eight-pointed star are centred on the red
    band; set it False for the bands alone. `radius` rounds the corners
    (0 = sharp rectangle)."""
    p.save()
    if radius > 0:
        clip = QPainterPath()
        clip.addRoundedRect(rect, radius, radius)
        p.setClipPath(clip)
    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
    band = h / 3.0
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#00B5E2"))          # top — cyan blue
    p.drawRect(QRectF(x, y, w, band + 1))
    p.setBrush(QColor("#EF3340"))          # middle — red
    p.drawRect(QRectF(x, y + band, w, band + 1))
    p.setBrush(QColor("#4FA72E"))          # bottom — green
    p.drawRect(QRectF(x, y + 2 * band, w, band + 1))

    if emblem:
        cy = y + h / 2.0
        cx = x + w * 0.44
        r_out = band * 0.48
        # crescent: white disc, then carve it with a red disc shifted right
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(QPointF(cx, cy), r_out, r_out)
        p.setBrush(QColor("#EF3340"))
        p.drawEllipse(QPointF(cx + r_out * 0.40, cy), r_out * 0.84, r_out * 0.84)
        # eight-pointed star to the right of the crescent opening
        _draw_star(p, QPointF(x + w * 0.62, cy), r_out * 0.60, QColor("#FFFFFF"))
    p.restore()


# ── App / window icon (the Postaz mark) ───────────────────────────────
def app_icon(size: int = 256) -> QIcon:
    """The Postaz logomark — the same rounded-square + paper-plane mark,
    with the square painted in the colours of the flag of Azerbaijan
    (cyan-blue / red / green bands). Used as the window icon and the corner
    mark of the brand header in the sidebar."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    # background — Azerbaijan flag bands filling the rounded square
    r = size * 0.22
    paint_az_flag(p, QRectF(0, 0, size, size), radius=r, emblem=False)
    # a soft dark scrim so the white plane stays legible over all 3 bands
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 38))
    p.drawRoundedRect(QRectF(0, 0, size, size), r, r)
    # paper plane (white)
    pen = QPen(QColor("#FFFFFF"))
    pen.setWidthF(size * 0.05)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    path = QPainterPath()
    path.moveTo(size * 0.22, size * 0.50)
    path.lineTo(size * 0.78, size * 0.26)
    path.lineTo(size * 0.60, size * 0.78)
    path.lineTo(size * 0.48, size * 0.54)
    path.closeSubpath()
    p.setBrush(QColor("#FFFFFF"))
    p.drawPath(path)
    # crease — translucent dark so the fold reads on any band
    p.setBrush(Qt.NoBrush)
    pen2 = QPen(QColor(0, 0, 0, 90))
    pen2.setWidthF(size * 0.03)
    p.setPen(pen2)
    p.drawLine(QPointF(size * 0.48, size * 0.54), QPointF(size * 0.78, size * 0.26))
    p.end()
    return QIcon(pm)
