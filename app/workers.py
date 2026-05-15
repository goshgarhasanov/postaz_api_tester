"""QThread-based HTTP worker so the UI never freezes."""
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
    worker = RequestWorker(rec, variables)
    worker.signals.finished.connect(on_done)
    QThreadPool.globalInstance().start(worker)
    return worker
