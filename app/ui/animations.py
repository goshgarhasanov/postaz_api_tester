"""Tiny library of animation helpers wrapped around `QPropertyAnimation`.

Each function returns the live animation object so callers can chain or
cancel it, but already calls `start()` so the common case is one-liner
ergonomic: `fade_in(my_widget)`. All animations clean themselves up via
`DeleteWhenStopped`."""
from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QRect,
    QSequentialAnimationGroup,
    QSize,
    Qt,
)
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget


def fade_in(widget: QWidget, duration: int = 220) -> QPropertyAnimation:
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    effect.setOpacity(0.0)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    return anim


def fade_out(widget: QWidget, duration: int = 180, on_done=None) -> QPropertyAnimation:
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(effect.opacity())
    anim.setEndValue(0.0)
    anim.setEasingCurve(QEasingCurve.InCubic)
    if on_done:
        anim.finished.connect(on_done)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    return anim


def slide_in_from_top(widget: QWidget, distance: int = 12, duration: int = 260) -> QParallelAnimationGroup:
    start_pos = widget.pos()
    widget.move(start_pos.x(), start_pos.y() - distance)
    pos_anim = QPropertyAnimation(widget, b"pos", widget)
    pos_anim.setDuration(duration)
    pos_anim.setStartValue(widget.pos())
    pos_anim.setEndValue(start_pos)
    pos_anim.setEasingCurve(QEasingCurve.OutCubic)

    fade = fade_in(widget, duration)

    group = QParallelAnimationGroup(widget)
    group.addAnimation(pos_anim)
    # fade already running; just keep reference
    group.start(QParallelAnimationGroup.DeleteWhenStopped)
    return group


def animate_width(widget: QWidget, end: int, duration: int = 240) -> QPropertyAnimation:
    anim = QPropertyAnimation(widget, b"maximumWidth", widget)
    anim.setDuration(duration)
    anim.setStartValue(widget.maximumWidth())
    anim.setEndValue(end)
    anim.setEasingCurve(QEasingCurve.InOutCubic)
    anim.start(QPropertyAnimation.DeleteWhenStopped)
    return anim


def pulse(widget: QWidget, duration: int = 320) -> QSequentialAnimationGroup:
    """Brief scale-pulse via geometry. Cheap visual feedback."""
    geom = widget.geometry()
    grown = QRect(geom.x() - 2, geom.y() - 2, geom.width() + 4, geom.height() + 4)
    group = QSequentialAnimationGroup(widget)
    a = QPropertyAnimation(widget, b"geometry", widget)
    a.setDuration(duration // 2)
    a.setStartValue(geom)
    a.setEndValue(grown)
    a.setEasingCurve(QEasingCurve.OutCubic)
    b = QPropertyAnimation(widget, b"geometry", widget)
    b.setDuration(duration // 2)
    b.setStartValue(grown)
    b.setEndValue(geom)
    b.setEasingCurve(QEasingCurve.InCubic)
    group.addAnimation(a)
    group.addAnimation(b)
    group.start(QSequentialAnimationGroup.DeleteWhenStopped)
    return group
