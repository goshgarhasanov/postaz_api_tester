"""Top-level window.

Owns the three primary panels (sidebar / request editor / response viewer),
the menu bar, the status bar, and every cross-panel signal wire. State that
needs to outlive a single session (theme, current language) lives in the DB
settings table — everything else is reactive."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QWidget,
)

from ..database import Database, RequestRecord
from ..http_client import ResponseData
from ..i18n import t, translator
from ..logger import get_logger
from ..workers import submit
from .dialogs import (
    AboutDialog,
    EnvironmentDialog,
    SaveRequestDialog,
    confirm_delete,
    reset_confirmations,
)
from .log_viewer import LogViewer

log = get_logger(__name__)
from .icons import (
    app_icon,
    icon_export,
    icon_globe,
    icon_info,
    icon_plus,
    icon_power,
    icon_save,
    icon_send,
    icon_trash,
)
from .import_dialog import ImportDialog
from .request_editor import RequestEditor
from .response_viewer import ResponseViewer
from .sidebar import Sidebar
from .styles import DARK
from .widgets import show_toast


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.current_request: RequestRecord = RequestRecord()
        self._sending = False

        self.setWindowIcon(app_icon(64))
        self.setWindowTitle("Postaz")
        self.resize(1360, 860)
        # 1024×680 fits a 1366×768 laptop after taskbar — anything smaller
        # starts clipping the URL bar / response meta.
        self.setMinimumSize(1024, 680)

        # ── language (load saved before building UI) ────────────
        saved_lang = self.db.get_setting("language", "en") or "en"
        translator.set_language(saved_lang)

        # ── central layout ───────────────────────────────────────
        self.sidebar = Sidebar(db, self)
        self.editor = RequestEditor()
        self.response = ResponseViewer()

        # Vertical split: request editor (top) over response viewer (bottom)
        center = QSplitter(Qt.Vertical)
        center.addWidget(self.editor)
        center.addWidget(self.response)
        center.setStretchFactor(0, 3)
        center.setStretchFactor(1, 2)
        center.setSizes([500, 380])
        center.setHandleWidth(3)
        center.setChildrenCollapsible(False)

        # Horizontal split: sidebar | (editor + response)
        main_split = QSplitter(Qt.Horizontal)
        main_split.addWidget(self.sidebar)
        main_split.addWidget(center)
        main_split.setStretchFactor(0, 0)
        main_split.setStretchFactor(1, 1)
        main_split.setSizes([300, 1060])
        main_split.setHandleWidth(3)
        main_split.setChildrenCollapsible(False)
        self.setCentralWidget(main_split)

        # ── menu + status ────────────────────────────────────────
        self._actions: dict[str, QAction] = {}
        self._menus: dict[str, "object"] = {}
        self._build_menu()
        self._build_status()

        # ── signals ──────────────────────────────────────────────
        self.editor.send_requested.connect(self.on_send)
        self.editor.save_requested.connect(self.on_save)
        self.editor.record_changed.connect(self._on_editor_changed)
        self.sidebar.request_selected.connect(self.open_request)
        self.sidebar.history_selected.connect(self.open_history)
        self.sidebar.new_request_requested.connect(self.new_request_in_collection)
        self.sidebar.import_curl_requested.connect(self.open_import)

        # ── theme (dark only) ────────────────────────────────────
        self.setStyleSheet(DARK)

        translator.language_changed.connect(self._retranslate_menus)
        self._update_env_label()
        self.statusBar().showMessage(t("Ready"), 2500)

    # ── menu / shortcuts ─────────────────────────────────────────────
    def _build_menu(self) -> None:
        mb = self.menuBar()

        # File
        m_file = mb.addMenu(t("&File"))
        self._menus["file"] = m_file

        a_new = QAction(icon_plus(), t("New Request"), self)
        a_new.setShortcut(QKeySequence.New)
        a_new.triggered.connect(self.new_request)
        m_file.addAction(a_new)
        self._actions["new_request"] = a_new

        a_save = QAction(icon_save(), t("Save"), self)
        a_save.setShortcut(QKeySequence.Save)
        a_save.triggered.connect(self.on_save)
        m_file.addAction(a_save)
        self._actions["save"] = a_save

        m_file.addSeparator()

        a_import = QAction(icon_plus(), self._tr_import(), self)
        a_import.setShortcut("Ctrl+I")
        a_import.triggered.connect(self.open_import)
        m_file.addAction(a_import)
        self._actions["import"] = a_import

        a_export = QAction(icon_export(), t("Export Response…"), self)
        a_export.triggered.connect(self._export_response)
        m_file.addAction(a_export)
        self._actions["export"] = a_export

        m_file.addSeparator()
        a_quit = QAction(icon_power(), t("Quit"), self)
        a_quit.setShortcut("Ctrl+Q")
        a_quit.triggered.connect(self.close)
        m_file.addAction(a_quit)
        self._actions["quit"] = a_quit

        # Request
        m_req = mb.addMenu(t("&Request"))
        self._menus["request"] = m_req
        a_send = QAction(icon_send("#7c5cff"), t("Send"), self)
        a_send.setShortcut("Ctrl+Return")
        a_send.triggered.connect(self.on_send)
        m_req.addAction(a_send)
        self._actions["send"] = a_send

        # Environments
        m_env = mb.addMenu(t("&Environments"))
        self._menus["env"] = m_env
        a_envs = QAction(icon_globe(), t("Manage…"), self)
        a_envs.setShortcut("Ctrl+E")
        a_envs.triggered.connect(self.open_environments)
        m_env.addAction(a_envs)
        self._actions["manage_env"] = a_envs

        # View
        m_view = mb.addMenu(t("&View"))
        self._menus["view"] = m_view
        a_clear_hist = QAction(icon_trash(), t("Clear History"), self)
        a_clear_hist.triggered.connect(self.clear_history)
        m_view.addAction(a_clear_hist)
        self._actions["clear_hist"] = a_clear_hist

        a_reset = QAction(t("Reset delete confirmations"), self)
        a_reset.triggered.connect(self._reset_confirmations)
        m_view.addAction(a_reset)
        self._actions["reset_confirms"] = a_reset

        # Help
        m_help = mb.addMenu(t("&Help"))
        self._menus["help"] = m_help

        a_logs = QAction(icon_export(), self._tr_logs(), self)
        a_logs.setShortcut("Ctrl+L")
        a_logs.triggered.connect(self.open_logs)
        m_help.addAction(a_logs)
        self._actions["logs"] = a_logs

        m_help.addSeparator()

        a_about = QAction(icon_info(), t("About"), self)
        a_about.triggered.connect(self._about)
        m_help.addAction(a_about)
        self._actions["about"] = a_about

    def _tr_logs(self) -> str:
        return {"en": "View Logs", "az": "Logları gör", "tr": "Logları Görüntüle"}[translator.language]

    def open_logs(self) -> None:
        log.info("user opened log viewer")
        LogViewer(self).exec()

    def _tr_import(self) -> str:
        return {"en": "Import cURL…", "az": "cURL idxal et…", "tr": "cURL İçe Aktar…"}[translator.language]

    def _retranslate_menus(self, _lang: str | None = None) -> None:
        self._menus["file"].setTitle(t("&File"))
        self._menus["request"].setTitle(t("&Request"))
        self._menus["env"].setTitle(t("&Environments"))
        self._menus["view"].setTitle(t("&View"))
        self._menus["help"].setTitle(t("&Help"))

        self._actions["new_request"].setText(t("New Request"))
        self._actions["save"].setText(t("Save"))
        self._actions["import"].setText(self._tr_import())
        self._actions["export"].setText(t("Export Response…"))
        self._actions["quit"].setText(t("Quit"))
        self._actions["send"].setText(t("Send"))
        self._actions["manage_env"].setText(t("Manage…"))
        self._actions["clear_hist"].setText(t("Clear History"))
        self._actions["reset_confirms"].setText(t("Reset delete confirmations"))
        self._actions["logs"].setText(self._tr_logs())
        self._actions["about"].setText(t("About"))
        # status + env label
        self._update_env_label()

    def _build_status(self) -> None:
        bar = QStatusBar()
        self.env_label = QLabel(t("No environment"))
        self.env_label.setStyleSheet("padding: 2px 8px;")
        bar.addPermanentWidget(self.env_label)
        self.setStatusBar(bar)

    # ── request lifecycle ────────────────────────────────────────────
    def new_request(self) -> None:
        self.current_request = RequestRecord()
        self.editor.load(self.current_request)
        self.response.clear()
        self.statusBar().showMessage(t("New request"), 1500)

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
        self.statusBar().showMessage(t("Opened: {name}", name=rec.name), 1500)

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
            self.statusBar().showMessage(t("Loaded from history"), 1500)
            return

    def _on_editor_changed(self) -> None:
        self.editor.to_record(self.current_request)

    # ── send ─────────────────────────────────────────────────────────
    def on_send(self) -> None:
        """Kick off an HTTP request on a worker thread.

        Guards against double-fire while a request is already in flight
        (the Send button is disabled but the keyboard shortcut isn't).
        Pulls variables from the active environment and hands everything
        to the `workers.submit()` helper."""
        if self._sending:
            log.debug("send ignored — already in flight")
            return
        rec = self.editor.to_record(self.current_request)
        if not rec.url.strip():
            log.warning("send blocked — empty URL")
            show_toast(self, t("URL is required"), "warn")
            return
        env = self.db.get_active_environment()
        variables = (env or {}).get("variables", {}) if env else {}
        log.info("user → send %s %s (env=%s)", rec.method, rec.url, env["name"] if env else "—")

        self._sending = True
        self.editor.set_sending(True)
        self.response.show_loading()
        self.statusBar().showMessage(f"{rec.method} {rec.url}")
        submit(rec, variables, self._on_response_ready)

    def _on_response_ready(self, resp: ResponseData) -> None:
        """Worker callback — paints the response, persists a snapshot to history."""
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
                "body_text": resp.body_text[:200_000],
                "content_type": resp.content_type,
                "size_bytes": resp.size_bytes,
                "final_url": resp.final_url,
            },
        }
        self.db.add_history(rec.method, rec.url, resp.status_code, resp.duration_ms, snapshot)
        self.sidebar._reload_history()
        if resp.ok:
            self.statusBar().showMessage(
                f"{resp.status_code} {resp.reason} • {resp.duration_ms} ms", 4000
            )
        else:
            show_toast(self, resp.error or t("Request failed"), "error")
            self.statusBar().showMessage(t("Request failed"), 4000)

    # ── save ─────────────────────────────────────────────────────────
    def on_save(self) -> None:
        """Persist the current editor state.

        First-time saves prompt for a name + target collection; subsequent
        saves silently overwrite the existing row."""
        rec = self.editor.to_record(self.current_request)
        if rec.id is None:
            dlg = SaveRequestDialog(self.db, default_name=rec.name, parent=self)
            if dlg.exec() != QDialog.Accepted:
                return
            name, collection_id = dlg.selected()
            rec.name = name
            rec.collection_id = collection_id
        self.db.save_request(rec)
        self.current_request = rec
        self.editor.load(rec)
        self.sidebar._reload_tree()
        show_toast(self, t("Saved"), "success")

    # ── import ───────────────────────────────────────────────────────
    def open_import(self) -> None:
        """Open the cURL import dialog and load the parsed result into the editor."""
        log.debug("user opened cURL import dialog")
        dlg = ImportDialog(self)
        if dlg.exec() != QDialog.Accepted or dlg.record is None:
            log.debug("cURL import cancelled / no record")
            return
        log.info("cURL imported into editor: %s %s", dlg.record.method, dlg.record.url)
        self.current_request = dlg.record
        self.editor.load(self.current_request)
        self.response.clear()
        show_toast(self, "cURL ✓", "success")

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
            self.env_label.setText(t("No environment"))
            self.env_label.setStyleSheet("padding: 2px 10px; color: #6b6f88;")

    def clear_history(self) -> None:
        """Wipe history via the modern confirm dialog (with don't-ask-again)."""
        if confirm_delete(self, self.db, "history"):
            self.db.clear_history()
            self.sidebar._reload_history()
            show_toast(self, t("History cleared"), "info")

    def _reset_confirmations(self) -> None:
        """Re-enable all 'are you sure?' prompts the user previously dismissed."""
        reset_confirmations(self.db)
        show_toast(self, t("Confirmations reset"), "success")

    def _export_response(self) -> None:
        body = self.response.body_view.toPlainText()
        if not body:
            show_toast(self, t("No response to export"), "warn")
            return
        path, _ = QFileDialog.getSaveFileName(self, t("Export response"), "response.txt")
        if path:
            Path(path).write_text(body, encoding="utf-8")
            show_toast(self, t("Exported"), "success")

    def _about(self) -> None:
        AboutDialog(self).exec()
