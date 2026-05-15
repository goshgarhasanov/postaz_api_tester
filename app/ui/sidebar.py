"""Left sidebar: collections tree + history list, tabbed."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QFont, QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..database import Database, RequestRecord
from .widgets import IconButton


METHOD_COLORS = {
    "GET": "#3aa86b",
    "POST": "#e9a83f",
    "PUT": "#3c8df0",
    "PATCH": "#a06bff",
    "DELETE": "#e8556e",
    "HEAD": "#7c5cff",
    "OPTIONS": "#7c5cff",
}


def _method_label(method: str) -> str:
    return method.upper()[:6]


def _format_timestamp(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", ""))
        return dt.strftime("%H:%M")
    except Exception:
        return ts[:5]


class Sidebar(QWidget):
    request_selected = Signal(int)         # request_id
    history_selected = Signal(int)         # history_id
    new_request_requested = Signal(int)    # collection_id (or 0)

    def __init__(self, db: Database, parent: QWidget | None = None):
        super().__init__(parent)
        self.db = db
        self.setObjectName("sidebar")
        self.setMinimumWidth(260)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ─ Header ────────────────────────────────────────────────────────
        header = QLabel("LOCAL API TESTER")
        header.setObjectName("sidebarHeader")
        outer.addWidget(header)

        # ─ Tab bar ───────────────────────────────────────────────────────
        tab_bar = QWidget()
        tab_bar.setObjectName("sidebarTabBar")
        tb_layout = QHBoxLayout(tab_bar)
        tb_layout.setContentsMargins(12, 4, 12, 8)
        tb_layout.setSpacing(6)

        self.btn_collections = QPushButton("Collections")
        self.btn_history = QPushButton("History")
        for b in (self.btn_collections, self.btn_history):
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
        self.btn_collections.setChecked(True)
        group = QButtonGroup(self)
        group.setExclusive(True)
        group.addButton(self.btn_collections, 0)
        group.addButton(self.btn_history, 1)
        tb_layout.addWidget(self.btn_collections)
        tb_layout.addWidget(self.btn_history)
        tb_layout.addStretch()

        self.btn_add = IconButton("＋", "New collection")
        tb_layout.addWidget(self.btn_add)
        outer.addWidget(tab_bar)

        # ─ Search ────────────────────────────────────────────────────────
        search_wrap = QFrame()
        sl = QHBoxLayout(search_wrap)
        sl.setContentsMargins(12, 0, 12, 8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search…")
        sl.addWidget(self.search)
        outer.addWidget(search_wrap)

        # ─ Stack: tree | history ─────────────────────────────────────────
        self.stack = QStackedWidget()
        outer.addWidget(self.stack, 1)

        self.tree = QTreeWidget()
        self.tree.setObjectName("collectionsTree")
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_tree_context)
        self.tree.itemDoubleClicked.connect(self._on_tree_double_click)
        self.stack.addWidget(self.tree)

        self.history_list = QListWidget()
        self.history_list.setObjectName("historyList")
        self.history_list.itemDoubleClicked.connect(self._on_history_double_click)
        self.stack.addWidget(self.history_list)

        # ─ Wire ──────────────────────────────────────────────────────────
        self.btn_collections.clicked.connect(lambda: self._switch(0))
        self.btn_history.clicked.connect(lambda: self._switch(1))
        self.btn_add.clicked.connect(self._create_collection_dialog)
        self.search.textChanged.connect(self._apply_filter)

        self.refresh()

    # ── public ────────────────────────────────────────────────────────────
    def refresh(self) -> None:
        self._reload_tree()
        self._reload_history()

    def _switch(self, idx: int) -> None:
        self.stack.setCurrentIndex(idx)
        if idx == 1:
            self._reload_history()

    # ── tree ──────────────────────────────────────────────────────────────
    def _reload_tree(self) -> None:
        self.tree.clear()
        collections = self.db.list_collections()
        cmap: dict[int, QTreeWidgetItem] = {}

        # build placeholder for un-collected (root) requests
        loose = QTreeWidgetItem(["Quick Saves"])
        loose.setData(0, Qt.UserRole, ("collection", 0))
        f = loose.font(0)
        f.setBold(True)
        loose.setFont(0, f)
        self.tree.addTopLevelItem(loose)

        # first pass: create all nodes
        for col in collections:
            item = QTreeWidgetItem([col.name])
            item.setData(0, Qt.UserRole, ("collection", col.id))
            ff = item.font(0)
            ff.setBold(True)
            item.setFont(0, ff)
            cmap[col.id] = item

        # second pass: attach to parents
        for col in collections:
            item = cmap[col.id]
            if col.parent_id and col.parent_id in cmap:
                cmap[col.parent_id].addChild(item)
            else:
                self.tree.addTopLevelItem(item)

        # add requests under their collections
        loose_requests = self.db.list_requests(None)
        for r in loose_requests:
            self._add_request_item(loose, r)

        for col in collections:
            for r in self.db.list_requests(col.id):
                self._add_request_item(cmap[col.id], r)

        self.tree.expandAll()

    def _add_request_item(self, parent: QTreeWidgetItem, r: RequestRecord) -> None:
        item = QTreeWidgetItem([f"  {r.name}"])
        item.setData(0, Qt.UserRole, ("request", r.id))
        item.setToolTip(0, f"{r.method}  {r.url}")
        # prefix with colored method tag via rich text? QTreeWidget items
        # don't support HTML directly; fall back to plain text with method.
        item.setText(0, f"{_method_label(r.method):<5}  {r.name}")
        parent.addChild(item)

    def _on_tree_double_click(self, item: QTreeWidgetItem, _col: int) -> None:
        payload = item.data(0, Qt.UserRole)
        if not payload:
            return
        kind, ident = payload
        if kind == "request":
            self.request_selected.emit(ident)

    def _on_tree_context(self, pos) -> None:
        item = self.tree.itemAt(pos)
        menu = QMenu(self)
        if item is None:
            act_new_col = menu.addAction("New collection")
            act_new_col.triggered.connect(self._create_collection_dialog)
        else:
            payload = item.data(0, Qt.UserRole)
            kind, ident = payload if payload else ("", 0)
            if kind == "collection":
                menu.addAction("New request").triggered.connect(
                    lambda: self.new_request_requested.emit(ident or 0)
                )
                if ident:
                    menu.addSeparator()
                    menu.addAction("Rename collection").triggered.connect(
                        lambda: self._rename_collection(ident)
                    )
                    menu.addAction("Delete collection").triggered.connect(
                        lambda: self._delete_collection(ident)
                    )
            elif kind == "request":
                menu.addAction("Open").triggered.connect(
                    lambda: self.request_selected.emit(ident)
                )
                menu.addSeparator()
                menu.addAction("Rename").triggered.connect(lambda: self._rename_request(ident))
                menu.addAction("Delete").triggered.connect(lambda: self._delete_request(ident))
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _create_collection_dialog(self) -> None:
        name, ok = QInputDialog.getText(self, "New Collection", "Collection name:")
        if ok and name.strip():
            self.db.create_collection(name.strip())
            self._reload_tree()

    def _rename_collection(self, cid: int) -> None:
        cols = {c.id: c for c in self.db.list_collections()}
        cur = cols.get(cid)
        if not cur:
            return
        name, ok = QInputDialog.getText(self, "Rename", "Name:", text=cur.name)
        if ok and name.strip():
            self.db.rename_collection(cid, name.strip())
            self._reload_tree()

    def _delete_collection(self, cid: int) -> None:
        r = QMessageBox.question(
            self,
            "Delete collection",
            "Delete this collection and all its requests?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if r == QMessageBox.Yes:
            self.db.delete_collection(cid)
            self._reload_tree()

    def _rename_request(self, rid: int) -> None:
        rec = self.db.get_request(rid)
        if not rec:
            return
        name, ok = QInputDialog.getText(self, "Rename", "Name:", text=rec.name)
        if ok and name.strip():
            rec.name = name.strip()
            self.db.save_request(rec)
            self._reload_tree()

    def _delete_request(self, rid: int) -> None:
        r = QMessageBox.question(
            self,
            "Delete request",
            "Delete this request?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if r == QMessageBox.Yes:
            self.db.delete_request(rid)
            self._reload_tree()

    # ── history ───────────────────────────────────────────────────────────
    def _reload_history(self) -> None:
        self.history_list.clear()
        for h in self.db.list_history(100):
            label = f"{_method_label(h['method']):<5}  {h['url']}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, h["id"])
            item.setToolTip(
                f"Status: {h['status_code']}\n"
                f"Time: {h['duration_ms']} ms\n"
                f"At: {h['created_at']}"
            )
            self.history_list.addItem(item)

    def _on_history_double_click(self, item: QListWidgetItem) -> None:
        hid = item.data(Qt.UserRole)
        if hid is not None:
            self.history_selected.emit(int(hid))

    # ── filter ────────────────────────────────────────────────────────────
    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()

        def filter_tree_item(item: QTreeWidgetItem) -> bool:
            visible_children = False
            for i in range(item.childCount()):
                if filter_tree_item(item.child(i)):
                    visible_children = True
            own = needle in item.text(0).lower()
            show = visible_children or own or not needle
            item.setHidden(not show)
            return show

        for i in range(self.tree.topLevelItemCount()):
            filter_tree_item(self.tree.topLevelItem(i))

        for r in range(self.history_list.count()):
            it = self.history_list.item(r)
            it.setHidden(bool(needle) and needle not in it.text().lower())
