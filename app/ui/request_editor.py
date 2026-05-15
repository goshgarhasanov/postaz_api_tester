"""Request builder.

Composed of three vertical strips:
  1. Method dropdown · URL bar · Save · Send buttons
  2. Editable request name (acts as a "title")
  3. A tab-folder with Params / Headers / Body / Auth editors

Emits two intents — `send_requested` and `save_requested` — plus a
`record_changed` signal that the parent uses to keep the in-memory
`RequestRecord` mirror in sync with the visible fields."""
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
from ..i18n import t, translator
from .icons import icon_save, icon_send
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
        top_layout.setContentsMargins(20, 14, 20, 12)
        top_layout.setSpacing(12)

        self.method = QComboBox()
        self.method.setObjectName("methodCombo")
        self.method.addItems(METHODS)
        self.method.setMinimumWidth(120)

        self.url = QLineEdit()
        self.url.setObjectName("urlBar")
        self.url.setPlaceholderText(t("https://api.example.com/v1/users  —  use {{baseUrl}} for vars"))
        self.url.returnPressed.connect(self.send_requested.emit)

        self.btn_send = PrimaryButton(t("Send"))
        self.btn_send.setIcon(icon_send("#ffffff"))
        self.btn_send.setFixedWidth(120)
        self.btn_send.clicked.connect(self.send_requested.emit)

        self.btn_save = GhostButton(t("Save"))
        self.btn_save.setIcon(icon_save("#c9cce0"))
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
        nl.setContentsMargins(20, 4, 20, 12)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(t("Untitled request"))
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

        self.params_table = KeyValueTable()
        self.tabs.addTab(self._wrap_table(self.params_table), t("Params"))

        self.headers_table = KeyValueTable()
        self.tabs.addTab(self._wrap_table(self.headers_table), t("Headers"))

        # Body
        body_widget = QWidget()
        bl = QVBoxLayout(body_widget)
        bl.setContentsMargins(20, 16, 20, 20)
        bl.setSpacing(10)
        body_top = QHBoxLayout()
        self.body_type_label = QLabel(t("Body type:"))
        self.body_type = QComboBox()
        self.body_type.addItems(["none", "json", "raw", "urlencoded"])
        body_top.addWidget(self.body_type_label)
        body_top.addWidget(self.body_type)
        body_top.addStretch()
        self.btn_format_json = GhostButton(t("Format JSON"))
        self.btn_format_json.clicked.connect(self._format_json)
        body_top.addWidget(self.btn_format_json)
        bl.addLayout(body_top)

        self.body_editor = QPlainTextEdit()
        self.body_editor.setPlaceholderText("{\n  \"key\": \"value\"\n}")
        self.body_editor.setFont(QFont("Consolas", 11))
        bl.addWidget(self.body_editor, 1)
        self.tabs.addTab(body_widget, t("Body"))

        # Auth
        auth_widget = QWidget()
        al = QVBoxLayout(auth_widget)
        al.setContentsMargins(20, 16, 20, 20)
        al.setSpacing(12)
        auth_top = QHBoxLayout()
        self.auth_type_label = QLabel(t("Auth type:"))
        self.auth_type = QComboBox()
        self.auth_type.addItems(["none", "bearer", "basic", "apikey"])
        auth_top.addWidget(self.auth_type_label)
        auth_top.addWidget(self.auth_type)
        auth_top.addStretch()
        al.addLayout(auth_top)

        self.auth_stack = QStackedWidget()
        # none
        self.auth_none_label = QLabel(t("This request will not include any authorization."))
        self.auth_none_label.setStyleSheet("color: #8b8fab; font-size: 12px;")
        none_w = QWidget()
        none_l = QVBoxLayout(none_w)
        none_l.addWidget(self.auth_none_label)
        none_l.addStretch()
        self.auth_stack.addWidget(none_w)

        self.auth_bearer_token = QLineEdit()
        self.auth_bearer_token.setPlaceholderText(t("Token (supports {{var}})"))
        self.bearer_form = self._form_widget([(t("Token"), self.auth_bearer_token)])
        self.auth_stack.addWidget(self.bearer_form)

        self.auth_basic_user = QLineEdit()
        self.auth_basic_user.setPlaceholderText(t("Username"))
        self.auth_basic_pass = QLineEdit()
        self.auth_basic_pass.setPlaceholderText(t("Password"))
        self.auth_basic_pass.setEchoMode(QLineEdit.Password)
        self.basic_form = self._form_widget(
            [(t("Username"), self.auth_basic_user), (t("Password"), self.auth_basic_pass)]
        )
        self.auth_stack.addWidget(self.basic_form)

        self.auth_apikey_name = QLineEdit()
        self.auth_apikey_name.setPlaceholderText(t("Header name (e.g. X-API-Key)"))
        self.auth_apikey_value = QLineEdit()
        self.auth_apikey_value.setPlaceholderText(t("Value"))
        self.apikey_form = self._form_widget(
            [(t("Header"), self.auth_apikey_name), (t("Value"), self.auth_apikey_value)]
        )
        self.auth_stack.addWidget(self.apikey_form)

        al.addWidget(self.auth_stack)
        al.addStretch()
        self.tabs.addTab(auth_widget, t("Auth"))

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

        translator.language_changed.connect(self._retranslate)
        self.load(RequestRecord())

    # ── helpers ──────────────────────────────────────────────────────
    def _wrap_table(self, table: KeyValueTable) -> QWidget:
        """Padded wrapper so the table doesn't kiss the tab edges."""
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 20)
        l.addWidget(table)
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
        """Pretty-print the body if it's valid JSON; silently no-op otherwise.

        Switches the body type combo to "json" on success so the right
        Content-Type ends up on the wire."""
        text = self.body_editor.toPlainText().strip()
        if not text:
            return
        try:
            parsed = json.loads(text)
            self.body_editor.setPlainText(json.dumps(parsed, indent=2, ensure_ascii=False))
            self.body_type.setCurrentText("json")
        except json.JSONDecodeError:
            pass

    def _retranslate(self, _lang: str | None = None) -> None:
        self.url.setPlaceholderText(t("https://api.example.com/v1/users  —  use {{baseUrl}} for vars"))
        self.btn_send.setText(t("Send"))
        self.btn_save.setText(t("Save"))
        self.name_edit.setPlaceholderText(t("Untitled request"))
        self.tabs.setTabText(0, t("Params"))
        self.tabs.setTabText(1, t("Headers"))
        self.tabs.setTabText(2, t("Body"))
        self.tabs.setTabText(3, t("Auth"))
        self.body_type_label.setText(t("Body type:"))
        self.auth_type_label.setText(t("Auth type:"))
        self.btn_format_json.setText(t("Format JSON"))
        self.auth_none_label.setText(t("This request will not include any authorization."))
        self.auth_bearer_token.setPlaceholderText(t("Token (supports {{var}})"))
        self.auth_basic_user.setPlaceholderText(t("Username"))
        self.auth_basic_pass.setPlaceholderText(t("Password"))
        self.auth_apikey_name.setPlaceholderText(t("Header name (e.g. X-API-Key)"))
        self.auth_apikey_value.setPlaceholderText(t("Value"))
        # update form row labels
        for form, fields in (
            (self.bearer_form, [(t("Token"),)]),
            (self.basic_form, [(t("Username"),), (t("Password"),)]),
            (self.apikey_form, [(t("Header"),), (t("Value"),)]),
        ):
            layout = form.layout()
            if isinstance(layout, QFormLayout):
                for i, (label,) in enumerate(fields):
                    lbl = layout.itemAt(i, QFormLayout.LabelRole)
                    if lbl and lbl.widget():
                        lbl.widget().setText(label)

    # ── load / dump ──────────────────────────────────────────────────
    def load(self, rec: RequestRecord) -> None:
        """Populate every field from a record without firing `record_changed`.

        `_suspend = True` mutes the change-signal during programmatic writes
        so we don't ricochet — the parent already knows about this record."""
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
        """Read every visible field back into a `RequestRecord`.

        If `base` is supplied (the saved record we opened from disk), the
        same instance is mutated in place — that preserves its `id` and
        `collection_id` so the next save is an UPDATE, not an INSERT."""
        rec = base or RequestRecord()
        rec.name = self.name_edit.text().strip() or t("Untitled request")
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
        self.btn_send.setText(t("Sending…") if sending else t("Send"))
        if sending:
            self.inflight_spinner.start()
        else:
            self.inflight_spinner.stop()
