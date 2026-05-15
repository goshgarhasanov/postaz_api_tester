"""Request builder: method/url/send + Params/Headers/Body/Auth tabs."""
from __future__ import annotations

import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..database import RequestRecord
from .widgets import GhostButton, KeyValueTable, PrimaryButton, Spinner

METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


class RequestEditor(QWidget):
    send_requested = Signal()
    save_requested = Signal()
    record_changed = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._suspend = False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── top bar (method + url + send) ──────────────────────────
        top = QFrame()
        top.setObjectName("topBar")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(16, 12, 16, 12)
        top_layout.setSpacing(10)

        self.method = QComboBox()
        self.method.setObjectName("methodCombo")
        self.method.addItems(METHODS)
        self.method.setMinimumWidth(120)

        self.url = QLineEdit()
        self.url.setObjectName("urlBar")
        self.url.setPlaceholderText("https://api.example.com/v1/users  —  use {{baseUrl}} for vars")
        self.url.returnPressed.connect(self.send_requested.emit)

        self.btn_send = PrimaryButton("Send")
        self.btn_send.setFixedWidth(110)
        self.btn_send.clicked.connect(self.send_requested.emit)

        self.btn_save = GhostButton("Save")
        self.btn_save.clicked.connect(self.save_requested.emit)

        self.inflight_spinner = Spinner(self, size=16, color="#7c5cff")

        top_layout.addWidget(self.method)
        top_layout.addWidget(self.url, 1)
        top_layout.addWidget(self.inflight_spinner)
        top_layout.addWidget(self.btn_save)
        top_layout.addWidget(self.btn_send)
        outer.addWidget(top)

        # ── name row ───────────────────────────────────────────────
        name_row = QFrame()
        name_row.setObjectName("topBar")
        nl = QHBoxLayout(name_row)
        nl.setContentsMargins(16, 0, 16, 10)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Untitled request")
        self.name_edit.setStyleSheet(
            "QLineEdit { background: transparent; border: none; padding: 2px 0; "
            "font-size: 14px; font-weight: 600; color: #e6e8f5; }"
            "QLineEdit:focus { border-bottom: 1px solid #7c5cff; }"
        )
        nl.addWidget(self.name_edit)
        outer.addWidget(name_row)

        # ── tabs ───────────────────────────────────────────────────
        self.tabs = QTabWidget()
        outer.addWidget(self.tabs, 1)

        # Params
        self.params_table = KeyValueTable()
        self.tabs.addTab(self._wrap_table(self.params_table), "Params")

        # Headers
        self.headers_table = KeyValueTable()
        self.tabs.addTab(self._wrap_table(self.headers_table), "Headers")

        # Body
        body_widget = QWidget()
        bl = QVBoxLayout(body_widget)
        bl.setContentsMargins(16, 12, 16, 12)
        bl.setSpacing(8)
        body_top = QHBoxLayout()
        self.body_type = QComboBox()
        self.body_type.addItems(["none", "json", "raw", "urlencoded"])
        body_top.addWidget(QLabel("Body type:"))
        body_top.addWidget(self.body_type)
        body_top.addStretch()
        self.btn_format_json = GhostButton("Format JSON")
        self.btn_format_json.clicked.connect(self._format_json)
        body_top.addWidget(self.btn_format_json)
        bl.addLayout(body_top)

        self.body_editor = QPlainTextEdit()
        self.body_editor.setPlaceholderText("{\n  \"key\": \"value\"\n}")
        self.body_editor.setFont(QFont("Consolas", 11))
        bl.addWidget(self.body_editor, 1)
        self.tabs.addTab(body_widget, "Body")

        # Auth
        auth_widget = QWidget()
        al = QVBoxLayout(auth_widget)
        al.setContentsMargins(16, 12, 16, 12)
        al.setSpacing(10)
        auth_top = QHBoxLayout()
        self.auth_type = QComboBox()
        self.auth_type.addItems(["none", "bearer", "basic", "apikey"])
        auth_top.addWidget(QLabel("Auth type:"))
        auth_top.addWidget(self.auth_type)
        auth_top.addStretch()
        al.addLayout(auth_top)

        self.auth_stack = QStackedWidget()
        # none
        self.auth_stack.addWidget(self._auth_none_widget())
        # bearer
        self.auth_bearer_token = QLineEdit()
        self.auth_bearer_token.setPlaceholderText("Token (supports {{var}})")
        self.auth_stack.addWidget(self._form_widget([("Token", self.auth_bearer_token)]))
        # basic
        self.auth_basic_user = QLineEdit()
        self.auth_basic_user.setPlaceholderText("Username")
        self.auth_basic_pass = QLineEdit()
        self.auth_basic_pass.setPlaceholderText("Password")
        self.auth_basic_pass.setEchoMode(QLineEdit.Password)
        self.auth_stack.addWidget(
            self._form_widget(
                [("Username", self.auth_basic_user), ("Password", self.auth_basic_pass)]
            )
        )
        # apikey
        self.auth_apikey_name = QLineEdit()
        self.auth_apikey_name.setPlaceholderText("Header name (e.g. X-API-Key)")
        self.auth_apikey_value = QLineEdit()
        self.auth_apikey_value.setPlaceholderText("Value")
        self.auth_stack.addWidget(
            self._form_widget(
                [("Header", self.auth_apikey_name), ("Value", self.auth_apikey_value)]
            )
        )
        al.addWidget(self.auth_stack)
        al.addStretch()
        self.tabs.addTab(auth_widget, "Auth")

        # ── wiring ─────────────────────────────────────────────────
        self.method.currentTextChanged.connect(self._emit_changed)
        self.url.textChanged.connect(self._emit_changed)
        self.name_edit.textChanged.connect(self._emit_changed)
        self.body_type.currentTextChanged.connect(self._emit_changed)
        self.body_editor.textChanged.connect(self._emit_changed)
        self.auth_type.currentTextChanged.connect(self._on_auth_changed)
        for w in (
            self.auth_bearer_token,
            self.auth_basic_user,
            self.auth_basic_pass,
            self.auth_apikey_name,
            self.auth_apikey_value,
        ):
            w.textChanged.connect(self._emit_changed)
        self.params_table.changed.connect(self._emit_changed)
        self.headers_table.changed.connect(self._emit_changed)

        # initial blank state
        self.load(RequestRecord())

    # ── helpers ──────────────────────────────────────────────────────
    def _wrap_table(self, table: KeyValueTable) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(16, 12, 16, 12)
        l.addWidget(table)
        return w

    def _auth_none_widget(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        lbl = QLabel("This request will not include any authorization.")
        lbl.setStyleSheet("color: #8b8fab; font-size: 12px;")
        l.addWidget(lbl)
        l.addStretch()
        return w

    def _form_widget(self, fields: list[tuple[str, QWidget]]) -> QWidget:
        w = QWidget()
        l = QFormLayout(w)
        l.setVerticalSpacing(10)
        l.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        for label, widget in fields:
            l.addRow(label, widget)
        return w

    def _on_auth_changed(self, _t: str) -> None:
        idx = {"none": 0, "bearer": 1, "basic": 2, "apikey": 3}.get(self.auth_type.currentText(), 0)
        self.auth_stack.setCurrentIndex(idx)
        self._emit_changed()

    def _emit_changed(self) -> None:
        if not self._suspend:
            self.record_changed.emit()

    def _format_json(self) -> None:
        text = self.body_editor.toPlainText().strip()
        if not text:
            return
        try:
            parsed = json.loads(text)
            self.body_editor.setPlainText(json.dumps(parsed, indent=2, ensure_ascii=False))
            self.body_type.setCurrentText("json")
        except json.JSONDecodeError:
            # silent — user will get red border in future; for now just bail
            pass

    # ── load / dump ──────────────────────────────────────────────────
    def load(self, rec: RequestRecord) -> None:
        self._suspend = True
        try:
            self.name_edit.setText(rec.name)
            self.method.setCurrentText(rec.method or "GET")
            self.url.setText(rec.url)
            self.body_type.setCurrentText(rec.body_type or "none")
            self.body_editor.setPlainText(rec.body or "")
            self.params_table.set_rows(rec.params or [])
            self.headers_table.set_rows(rec.headers or [])
            self.auth_type.setCurrentText(rec.auth_type or "none")
            self._on_auth_changed("")
            data = rec.auth_data or {}
            self.auth_bearer_token.setText(data.get("token", ""))
            self.auth_basic_user.setText(data.get("username", ""))
            self.auth_basic_pass.setText(data.get("password", ""))
            self.auth_apikey_name.setText(data.get("key", ""))
            self.auth_apikey_value.setText(data.get("value", ""))
        finally:
            self._suspend = False

    def to_record(self, base: RequestRecord | None = None) -> RequestRecord:
        rec = base or RequestRecord()
        rec.name = self.name_edit.text().strip() or "Untitled request"
        rec.method = self.method.currentText()
        rec.url = self.url.text().strip()
        rec.body_type = self.body_type.currentText()
        rec.body = self.body_editor.toPlainText()
        rec.params = self.params_table.get_rows()
        rec.headers = self.headers_table.get_rows()
        rec.auth_type = self.auth_type.currentText()
        rec.auth_data = {
            "token": self.auth_bearer_token.text(),
            "username": self.auth_basic_user.text(),
            "password": self.auth_basic_pass.text(),
            "key": self.auth_apikey_name.text(),
            "value": self.auth_apikey_value.text(),
        }
        return rec

    def set_sending(self, sending: bool) -> None:
        self.btn_send.setEnabled(not sending)
        self.btn_send.setText("Sending…" if sending else "Send")
        if sending:
            self.inflight_spinner.start()
        else:
            self.inflight_spinner.stop()
