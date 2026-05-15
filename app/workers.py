"""Threaded HTTP worker — keeps the UI responsive while the server replies.

We use Qt's global `QThreadPool` (a worker-queue, not raw threads) so multiple
concurrent requests are cheap. Each worker emits its result over a `Signal`,
which Qt safely marshals back to the UI thread before invoking the callback."""
from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from .database import RequestRecord
from .http_client import ResponseData, execute


class _Signals(QObject):
    finished = Signal(object)  # ResponseData


class RequestWorker(QRunnable):
    """Single-shot HTTP runnable executed in QThreadPool."""

    def __init__(self, rec: RequestRecord, variables: dict[str, str]):
        super().__init__()
        self.rec = rec
        self.variables = variables
        self.signals = _Signals()
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:  # noqa: D401
        try:
            result = execute(self.rec, self.variables)
        except Exception as e:  # safety net
            result = ResponseData(ok=False, error=f"Worker crash: {e}")
        self.signals.finished.emit(result)


def submit(rec: RequestRecord, variables: dict[str, str], on_done) -> RequestWorker:
    """Fire-and-forget helper: build a worker, wire the callback, dispatch.

    `on_done` runs on the UI thread (because that's where the signal was
    connected) and receives a `ResponseData` instance."""
    worker = RequestWorker(rec, variables)
    worker.signals.finished.connect(on_done)
    QThreadPool.globalInstance().start(worker)
    return worker
