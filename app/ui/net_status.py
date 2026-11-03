"""Top-bar internet status + latency indicator.

Shows whether we're online and the round-trip latency to a reliable host,
colour-coded by speed:

    online · fast     (≤ 100 ms)  → green
    online · ok       (≤ 300 ms)  → amber
    online · slow     (> 300 ms)  → red
    offline                        → red

Latency is measured with a plain TCP connect (no external `ping` binary,
no raw sockets / root) on Qt's global thread pool, so the UI never blocks.
A QTimer re-checks every few seconds."""
from __future__ import annotations

import socket
import time

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, Signal, Slot
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from ..i18n import t
from ..logger import get_logger

log = get_logger(__name__)

# Cloudflare's resolver — fast, globally anycast, answers on 443.
_HOST = "1.1.1.1"
_PORT = 443
_TIMEOUT = 3.0

# latency thresholds (ms)
_FAST = 100
_OK = 300

# palette (matches styles.py status colours)
_GREEN = "#5FD38A"
_AMBER = "#FFC24D"
_RED = "#FF6B78"
_MUTED = "#63656F"


def _measure(host: str = _HOST, port: int = _PORT, timeout: float = _TIMEOUT) -> tuple[bool, int]:
    """Return (online, latency_ms). latency_ms is -1 when offline."""
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, int((time.perf_counter() - start) * 1000)
    except OSError:
        return False, -1


class _Signals(QObject):
    done = Signal(bool, int)  # online, latency_ms


class _PingWorker(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = _Signals()
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        online, ms = _measure()
        self.signals.done.emit(online, ms)


class NetStatus(QWidget):
    """Compact pill: a coloured dot + 'latency ms' (or 'Offline').

    Lives in the menu bar's top-right corner. Poll interval is generous so
    the check never becomes a bandwidth or CPU cost."""

    def __init__(self, parent: QWidget | None = None, interval_ms: int = 6000):
        super().__init__(parent)
        self.setObjectName("netStatus")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 10, 0)
        lay.setSpacing(0)

        self._label = QLabel()
        self._label.setObjectName("netStatusLabel")
        self._label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self._label.setToolTip(t("Internet connection & latency"))
        self._label.setMinimumWidth(104)
        lay.addWidget(self._label)

        self._set_checking()

        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._check)
        self._timer.start()
        # first probe shortly after startup so the window paints instantly
        QTimer.singleShot(400, self._check)

    # ── probing ──────────────────────────────────────────────────────
    def _check(self) -> None:
        worker = _PingWorker()
        worker.signals.done.connect(self._update)
        QThreadPool.globalInstance().start(worker)

    def _update(self, online: bool, ms: int) -> None:
        if not online:
            self._render(_RED, t("Offline"))
            return
        if ms <= _FAST:
            color = _GREEN
        elif ms <= _OK:
            color = _AMBER
        else:
            color = _RED
        self._render(color, f"{ms} ms")

    # ── rendering ────────────────────────────────────────────────────
    def _set_checking(self) -> None:
        self._render(_MUTED, "…")

    def _render(self, color: str, text: str) -> None:
        self._label.setText(
            f'<span style="color:{color}; font-size:15px;">●</span>'
            f'&nbsp;<span style="color:#C4C6CE; font-weight:700;'
            f' font-family:\'JetBrains Mono\',Consolas; font-size:11px;'
            f' letter-spacing:0.4px;">{text}</span>'
        )
