"""Top-level window: splitters, menu, theme, state."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ..database import Database, RequestRecord
from ..http_client import ResponseData
from ..workers import submit
from .dialogs import EnvironmentDialog, SaveRequestDialog
from .request_editor import RequestEditor
from .response_viewer import ResponseViewer
from .sidebar import Sidebar
from .styles import DARK, LIGHT
from .widgets import show_toast


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.current_request: RequestRecord = RequestRecord()
        self._sending = False

        self.setWindowTitle("Local API Tester")
        self.resize(1320, 820)
        self.setMinimumSize(960, 600)

        # ── central layout ───────────────────────────────────────
        self.sidebar = Sidebar(db, self)
        self.editor = RequestEditor()
        self.response = ResponseViewer()

        center = QSplitter(Qt.Vertical)
        center.addWidget(self.editor)
        center.addWidget(self.response)
        center.setStretchFactor(0, 3)
        center.setStretchFactor(1, 2)
        center.setSizes([460, 360])
        center.setHandleWidth(1)

        main_split = QSplitter(Qt.Horizontal)
        main_split.addWidget(self.sidebar)
        main_split.addWidget(center)
        main_split.setStretchFactor(0, 0)
        main_split.setStretchFactor(1, 1)
        main_split.setSizes([280, 1040])
        main_split.setHandleWidth(1)
        self.setCentralWidget(main_split)

        # ── menu + status ────────────────────────────────────────
        self._build_menu()
        self._build_status()

        # ── signals ──────────────────────────────────────────────
        self.editor.send_requested.connect(self.on_send)
        self.editor.save_requested.connect(self.on_save)
        self.editor.record_changed.connect(self._on_editor_changed)
        self.sidebar.request_selected.connect(self.open_request)
        self.sidebar.history_selected.connect(self.open_history)
        self.sidebar.new_request_requested.connect(self.new_request_in_collection)

        # ── theme ────────────────────────────────────────────────
        self.theme = self.db.get_setting("theme", "dark")
        self.apply_theme(self.theme)

        # ── ready ────────────────────────────────────────────────
        self._update_env_label()

    # ── menu / shortcuts ─────────────────────────────────────────────
    def _build_menu(self) -> None:
        mb = self.menuBar()

        m_file = mb.addMenu("&File")
        a_new = QAction("New Request", self)
        a_new.setShortcut(QKeySequence.New)
        a_new.triggered.connect(self.new_request)
        m_file.addAction(a_new)

        a_save = QAction("Save", self)
        a_save.setShortcut(QKeySequence.Save)
        a_save.triggered.connect(self.on_save)
        m_file.addAction(a_save)
        m_file.addSeparator()

        a_export = QAction("Export Response…", self)
        a_export.triggered.connect(self._export_response)
        m_file.addAction(a_export)
        m_file.addSeparator()

        a_quit = QAction("Quit", self)
        a_quit.setShortcut("Ctrl+Q")
        a_quit.triggered.connect(self.close)
        m_file.addAction(a_quit)

        m_req = mb.addMenu("&Request")
        a_send = QAction("Send", self)
        a_send.setShortcut("Ctrl+Return")
        a_send.triggered.connect(self.on_send)
        m_req.addAction(a_send)

        m_env = mb.addMenu("&Environments")
        a_envs = QAction("Manage…", self)
        a_envs.setShortcut("Ctrl+E")
        a_envs.triggered.connect(self.open_environments)
        m_env.addAction(a_envs)

        m_view = mb.addMenu("&View")
        a_theme = QAction("Toggle Theme", self)
        a_theme.setShortcut("Ctrl+T")
        a_theme.triggered.connect(self.toggle_theme)
        m_view.addAction(a_theme)

        a_clear_hist = QAction("Clear History", self)
        a_clear_hist.triggered.connect(self.clear_history)
        m_view.addAction(a_clear_hist)

        m_help = mb.addMenu("&Help")
        a_about = QAction("About", self)
        a_about.triggered.connect(self._about)
        m_help.addAction(a_about)

    def _build_status(self) -> None:
        bar = QStatusBar()
        self.env_label = QLabel("No env")
        self.env_label.setStyleSheet("padding: 2px 8px;")
        bar.addPermanentWidget(self.env_label)
        self.setStatusBar(bar)
        bar.showMessage("Ready", 2500)

    # ── theme ────────────────────────────────────────────────────────
    def apply_theme(self, theme: str) -> None:
        self.theme = theme
        self.setStyleSheet(DARK if theme == "dark" else LIGHT)
        self.db.set_setting("theme", theme)

    def toggle_theme(self) -> None:
        self.apply_theme("light" if self.theme == "dark" else "dark")

    # ── request lifecycle ────────────────────────────────────────────
    def new_request(self) -> None:
        self.current_request = RequestRecord()
        self.editor.load(self.current_request)
        self.response.clear()
        self.statusBar().showMessage("New request", 1500)

    def new_request_in_collection(self, collection_id: int) -> None:
        self.current_request = RequestRecord(collection_id=collection_id or None)
        self.editor.load(self.current_request)
        self.response.clear()

    def open_request(self, request_id: int) -> None:
        rec = self.db.get_request(request_id)
        if not rec:
            return
        self.current_request = rec
        self.editor.load(rec)
        self.response.clear()
        self.statusBar().showMessage(f"Opened: {rec.name}", 1500)

    def open_history(self, history_id: int) -> None:
        for h in self.db.list_history(200):
            if h["id"] != history_id:
                continue
            snap = h["snapshot"] or {}
            req = snap.get("request", {})
            rec = RequestRecord(
                name=h["url"],
                method=h["method"],
                url=h["url"],
                headers=req.get("headers", []),
                params=req.get("params", []),
                body=req.get("body", ""),
                body_type=req.get("body_type", "none"),
                auth_type=req.get("auth_type", "none"),
                auth_data=req.get("auth_data", {}),
            )
            self.current_request = rec
            self.editor.load(rec)
            # reconstruct ResponseData lightly for view
            from ..http_client import ResponseData as RD
            r = snap.get("response", {})
            resp = RD(
                ok=bool(r.get("ok", True)),
                error=r.get("error"),
                status_code=h["status_code"] or 0,
                reason=r.get("reason", ""),
                headers=r.get("headers", {}),
                body_text=r.get("body_text", ""),
                content_type=r.get("content_type", ""),
                duration_ms=h["duration_ms"] or 0,
                size_bytes=r.get("size_bytes", 0),
                final_url=r.get("final_url", ""),
            )
            self.response.show_response(resp)
            self.statusBar().showMessage("Loaded from history", 1500)
            return

    def _on_editor_changed(self) -> None:
        self.editor.to_record(self.current_request)

    # ── send ─────────────────────────────────────────────────────────
    def on_send(self) -> None:
        if self._sending:
            return
        rec = self.editor.to_record(self.current_request)
        if not rec.url.strip():
            show_toast(self, "URL is required", "warn")
            return
        env = self.db.get_active_environment()
        variables = (env or {}).get("variables", {}) if env else {}

        self._sending = True
        self.editor.set_sending(True)
        self.response.show_loading()
        self.statusBar().showMessage(f"Sending {rec.method} {rec.url}…")

        submit(rec, variables, self._on_response_ready)

    def _on_response_ready(self, resp: ResponseData) -> None:
        self._sending = False
        self.editor.set_sending(False)
        self.response.show_response(resp)
        rec = self.current_request
        snapshot = {
            "request": {
                "method": rec.method,
                "url": rec.url,
                "headers": rec.headers,
                "params": rec.params,
                "body": rec.body,
                "body_type": rec.body_type,
                "auth_type": rec.auth_type,
                "auth_data": rec.auth_data,
            },
            "response": {
                "ok": resp.ok,
                "error": resp.error,
                "reason": resp.reason,
                "headers": resp.headers,
                "body_text": resp.body_text[:200_000],  # cap stored size
                "content_type": resp.content_type,
                "size_bytes": resp.size_bytes,
                "final_url": resp.final_url,
            },
        }
        self.db.add_history(
            rec.method,
            rec.url,
            resp.status_code,
            resp.duration_ms,
            snapshot,
        )
        self.sidebar._reload_history()
        if resp.ok:
            self.statusBar().showMessage(
                f"{resp.status_code} {resp.reason} • {resp.duration_ms} ms", 4000
            )
        else:
            show_toast(self, resp.error or "Request failed", "error")
            self.statusBar().showMessage("Request failed", 4000)

    # ── save ─────────────────────────────────────────────────────────
    def on_save(self) -> None:
        rec = self.editor.to_record(self.current_request)
        if rec.id is None:
            dlg = SaveRequestDialog(self.db, default_name=rec.name, parent=self)
            if dlg.exec() != dlg.Accepted:
                return
            name, collection_id = dlg.selected()
            rec.name = name
            rec.collection_id = collection_id
        self.db.save_request(rec)
        self.current_request = rec
        self.editor.load(rec)  # picks up id-aware state
        self.sidebar._reload_tree()
        show_toast(self, "Saved", "success")

    # ── env / misc ───────────────────────────────────────────────────
    def open_environments(self) -> None:
        dlg = EnvironmentDialog(self.db, self)
        dlg.changed.connect(self._update_env_label)
        dlg.exec()
        self._update_env_label()

    def _update_env_label(self) -> None:
        env = self.db.get_active_environment()
        if env:
            self.env_label.setText(f"⌁ {env['name']}")
            self.env_label.setStyleSheet(
                "padding: 2px 10px; color: #7c5cff; font-weight: 600;"
            )
        else:
            self.env_label.setText("No environment")
            self.env_label.setStyleSheet("padding: 2px 10px; color: #6b6f88;")

    def clear_history(self) -> None:
        r = QMessageBox.question(
            self, "Clear", "Clear all request history?", QMessageBox.Yes | QMessageBox.No
        )
        if r == QMessageBox.Yes:
            self.db.clear_history()
            self.sidebar._reload_history()
            show_toast(self, "History cleared", "info")

    def _export_response(self) -> None:
        body = self.response.body_view.toPlainText()
        if not body:
            show_toast(self, "No response to export", "warn")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export response", "response.txt")
        if path:
            Path(path).write_text(body, encoding="utf-8")
            show_toast(self, "Exported", "success")

    def _about(self) -> None:
        QMessageBox.about(
            self,
            "About",
            "<h3>Local API Tester</h3>"
            "<p>A lightweight Postman-style client.</p>"
            "<p>Built with PySide6 + SQLite.</p>",
        )
