"""Dialogs: save request, environment manager."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..database import Database
from .widgets import GhostButton, PrimaryButton


class SaveRequestDialog(QDialog):
    def __init__(self, db: Database, default_name: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Save Request")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Save Request")
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setVerticalSpacing(10)

        self.name = QLineEdit(default_name)
        self.name.selectAll()
        form.addRow("Name", self.name)

        self.collection = QComboBox()
        self.collection.addItem("Quick Saves", None)
        for c in db.list_collections():
            self.collection.addItem(c.name, c.id)
        form.addRow("Collection", self.collection)

        layout.addLayout(form)

        # New-collection row
        new_row = QHBoxLayout()
        self.new_col_name = QLineEdit()
        self.new_col_name.setPlaceholderText("Or create new collection…")
        new_btn = GhostButton("Create")
        new_btn.clicked.connect(self._create_collection)
        new_row.addWidget(self.new_col_name)
        new_row.addWidget(new_btn)
        layout.addLayout(new_row)

        # buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = GhostButton("Cancel")
        cancel.clicked.connect(self.reject)
        save = PrimaryButton("Save")
        save.clicked.connect(self.accept)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

    def _create_collection(self) -> None:
        name = self.new_col_name.text().strip()
        if not name:
            return
        cid = self.db.create_collection(name)
        self.collection.addItem(name, cid)
        self.collection.setCurrentIndex(self.collection.count() - 1)
        self.new_col_name.clear()

    def selected(self) -> tuple[str, Optional[int]]:
        return (
            self.name.text().strip() or "Untitled request",
            self.collection.currentData(),
        )


class EnvironmentDialog(QDialog):
    """Manage environments and their variables."""

    changed = Signal()

    def __init__(self, db: Database, parent: QWidget | None = None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Environments")
        self.setMinimumSize(640, 420)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(14)

        # ── left: environment list ──────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(8)
        left.addWidget(QLabel("Environments"))
        self.list = QListWidget()
        self.list.setFixedWidth(180)
        self.list.currentItemChanged.connect(self._on_select)
        left.addWidget(self.list)
        row = QHBoxLayout()
        btn_new = GhostButton("New")
        btn_del = GhostButton("Delete")
        btn_new.clicked.connect(self._new_env)
        btn_del.clicked.connect(self._delete_env)
        row.addWidget(btn_new)
        row.addWidget(btn_del)
        left.addLayout(row)
        outer.addLayout(left)

        # ── right: editor ───────────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(10)
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.editingFinished.connect(self._persist_current)
        name_row.addWidget(self.name_edit)
        right.addLayout(name_row)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Variable", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.itemChanged.connect(self._on_table_change)
        right.addWidget(self.table, 1)

        self.activate_btn = GhostButton("Set as active")
        self.activate_btn.clicked.connect(self._activate)
        bottom = QHBoxLayout()
        bottom.addWidget(self.activate_btn)
        bottom.addStretch()
        close = PrimaryButton("Done")
        close.clicked.connect(self.accept)
        bottom.addWidget(close)
        right.addLayout(bottom)
        outer.addLayout(right, 1)

        self._loading = False
        self._reload()

    def _reload(self) -> None:
        self.list.clear()
        for env in self.db.list_environments():
            item = QListWidgetItem(("● " if env["is_active"] else "  ") + env["name"])
            item.setData(Qt.UserRole, env)
            self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)
        else:
            self._clear_editor()

    def _clear_editor(self) -> None:
        self._loading = True
        self.name_edit.clear()
        self.table.setRowCount(0)
        self._add_blank_row()
        self._loading = False

    def _add_blank_row(self) -> None:
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem(""))
        self.table.setItem(r, 1, QTableWidgetItem(""))

    def _on_select(self, current: QListWidgetItem | None, _prev) -> None:
        if not current:
            return
        env = current.data(Qt.UserRole)
        self._loading = True
        self.name_edit.setText(env["name"])
        self.table.setRowCount(0)
        for k, v in env["variables"].items():
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(k)))
            self.table.setItem(r, 1, QTableWidgetItem(str(v)))
        self._add_blank_row()
        self._loading = False

    def _on_table_change(self, _it) -> None:
        if self._loading:
            return
        # ensure trailing empty row
        last = self.table.rowCount() - 1
        if last < 0:
            self._add_blank_row()
        else:
            k_item = self.table.item(last, 0)
            if k_item and k_item.text().strip():
                self._add_blank_row()
        self._persist_current()

    def _current_env(self) -> Optional[dict]:
        it = self.list.currentItem()
        if not it:
            return None
        return it.data(Qt.UserRole)

    def _collect_vars(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for r in range(self.table.rowCount()):
            k = (self.table.item(r, 0).text() if self.table.item(r, 0) else "").strip()
            v = self.table.item(r, 1).text() if self.table.item(r, 1) else ""
            if k:
                out[k] = v
        return out

    def _persist_current(self) -> None:
        env = self._current_env()
        if not env:
            return
        name = self.name_edit.text().strip() or env["name"]
        self.db.update_environment(env["id"], name, self._collect_vars())
        # refresh tag in list
        item = self.list.currentItem()
        env["name"] = name
        env["variables"] = self._collect_vars()
        item.setData(Qt.UserRole, env)
        item.setText(("● " if env["is_active"] else "  ") + name)
        self.changed.emit()

    def _new_env(self) -> None:
        name, ok = QInputDialog.getText(self, "New environment", "Name:")
        if ok and name.strip():
            self.db.create_environment(name.strip(), {})
            self._reload()
            self.changed.emit()

    def _delete_env(self) -> None:
        env = self._current_env()
        if not env:
            return
        r = QMessageBox.question(
            self, "Delete", f"Delete environment '{env['name']}'?", QMessageBox.Yes | QMessageBox.No
        )
        if r == QMessageBox.Yes:
            self.db.delete_environment(env["id"])
            self._reload()
            self.changed.emit()

    def _activate(self) -> None:
        env = self._current_env()
        if not env:
            return
        self.db.set_active_environment(env["id"])
        self._reload()
        self.changed.emit()
