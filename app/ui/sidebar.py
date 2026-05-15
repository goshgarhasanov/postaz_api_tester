"""Left sidebar — the Postaz brand mark plus two stacked panels.

The "Collections" panel is a tree of folders → saved requests.
The "History" panel is a flat list of the last 200 executed calls.
Both share one search box that filters by case-insensitive substring."""
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
from ..i18n import t, translator
from .icons import icon_folder, icon_plus
from .logo import Logo
from .widgets import IconButton


def _method_label(method: str) -> str:
    return method.upper()[:6]


class Sidebar(QWidget):
    """The left-hand navigation surface.

    Emits high-level intents (open this request / open this history entry /
    create a new request in this collection) — never mutates the editor
    directly. `MainWindow` glues the signals together."""

    request_selected = Signal(int)        # user double-clicked a saved request
    history_selected = Signal(int)        # user double-clicked a history row
    new_request_requested = Signal(int)   # "New request" was triggered in a collection

    def __init__(self, db: Database, parent: QWidget | None = None):
        super().__init__(parent)
        self.db = db
        self.setObjectName("sidebar")
        self.setMinimumWidth(260)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ─ Brand header ──────────────────────────────────────────────────
        brand_wrap = QFrame()
        brand_wrap.setObjectName("brandWrap")
        bl = QHBoxLayout(brand_wrap)
        bl.setContentsMargins(16, 14, 16, 8)
        self.logo = Logo(self, height=26)
        bl.addWidget(self.logo)
        bl.addStretch()
        outer.addWidget(brand_wrap)

        # ─ Tab bar ───────────────────────────────────────────────────────
        tab_bar = QWidget()
        tab_bar.setObjectName("sidebarTabBar")
        tb_layout = QHBoxLayout(tab_bar)
        tb_layout.setContentsMargins(12, 4, 12, 8)
        tb_layout.setSpacing(6)

        self.btn_collections = QPushButton(t("Collections"))
        self.btn_history = QPushButton(t("History"))
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

        self.btn_add = IconButton("", t("New collection"))
        self.btn_add.setIcon(icon_plus("#c9cce0"))
        self.btn_add.setIconSize(self.btn_add.iconSize())
        tb_layout.addWidget(self.btn_add)
        outer.addWidget(tab_bar)

        # ─ Search ────────────────────────────────────────────────────────
        search_wrap = QFrame()
        sl = QHBoxLayout(search_wrap)
        sl.setContentsMargins(12, 0, 12, 8)
        self.search = QLineEdit()
        self.search.setPlaceholderText(t("Search…"))
        self.search.setClearButtonEnabled(True)
        sl.addWidget(self.search)
        outer.addWidget(search_wrap)

        # ─ Stack: tree | history ─────────────────────────────────────────
        self.stack = QStackedWidget()
        outer.addWidget(self.stack, 1)

        self.tree = QTreeWidget()
        self.tree.setObjectName("collectionsTree")
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)
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

        translator.language_changed.connect(self._retranslate)
        self.refresh()

    # ── retranslate ───────────────────────────────────────────────────────
    def _retranslate(self, _lang: str | None = None) -> None:
        self.btn_collections.setText(t("Collections"))
        self.btn_history.setText(t("History"))
        self.btn_add.setToolTip(t("New collection"))
        self.search.setPlaceholderText(t("Search…"))
        self._reload_tree()
        self._reload_history()

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

        folder_icon = icon_folder("#a89bff")

        # placeholder for root-level requests
        loose = QTreeWidgetItem([t("Quick Saves")])
        loose.setData(0, Qt.UserRole, ("collection", 0))
        loose.setIcon(0, folder_icon)
        f = loose.font(0)
        f.setBold(True)
        loose.setFont(0, f)
        self.tree.addTopLevelItem(loose)

        for col in collections:
            item = QTreeWidgetItem([col.name])
            item.setData(0, Qt.UserRole, ("collection", col.id))
            item.setIcon(0, folder_icon)
            ff = item.font(0)
            ff.setBold(True)
            item.setFont(0, ff)
            cmap[col.id] = item

        for col in collections:
            item = cmap[col.id]
            if col.parent_id and col.parent_id in cmap:
                cmap[col.parent_id].addChild(item)
            else:
                self.tree.addTopLevelItem(item)

        for r in self.db.list_requests(None):
            self._add_request_item(loose, r)

        for col in collections:
            for r in self.db.list_requests(col.id):
                self._add_request_item(cmap[col.id], r)

        self.tree.expandAll()

    def _add_request_item(self, parent: QTreeWidgetItem, r: RequestRecord) -> None:
        item = QTreeWidgetItem([f"{_method_label(r.method):<5}  {r.name}"])
        item.setData(0, Qt.UserRole, ("request", r.id))
        item.setToolTip(0, f"{r.method}  {r.url}")
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
            menu.addAction(t("New collection")).triggered.connect(self._create_collection_dialog)
        else:
            payload = item.data(0, Qt.UserRole)
            kind, ident = payload if payload else ("", 0)
            if kind == "collection":
                menu.addAction(t("New Request")).triggered.connect(
                    lambda: self.new_request_requested.emit(ident or 0)
                )
                if ident:
                    menu.addSeparator()
                    menu.addAction(t("Rename collection")).triggered.connect(
                        lambda: self._rename_collection(ident)
                    )
                    menu.addAction(t("Delete collection")).triggered.connect(
                        lambda: self._delete_collection(ident)
                    )
            elif kind == "request":
                menu.addAction(t("Open")).triggered.connect(
                    lambda: self.request_selected.emit(ident)
                )
                menu.addSeparator()
                menu.addAction(t("Rename")).triggered.connect(lambda: self._rename_request(ident))
                menu.addAction(t("Delete")).triggered.connect(lambda: self._delete_request(ident))
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _create_collection_dialog(self) -> None:
        name, ok = QInputDialog.getText(self, t("New Collection"), t("Collection name:"))
        if ok and name.strip():
            self.db.create_collection(name.strip())
            self._reload_tree()

    def _rename_collection(self, cid: int) -> None:
        cols = {c.id: c for c in self.db.list_collections()}
        cur = cols.get(cid)
        if not cur:
            return
        name, ok = QInputDialog.getText(self, t("Rename"), t("Name:"), text=cur.name)
        if ok and name.strip():
            self.db.rename_collection(cid, name.strip())
            self._reload_tree()

    def _delete_collection(self, cid: int) -> None:
        r = QMessageBox.question(
            self,
            t("Delete collection"),
            t("Delete this collection and all its requests?"),
            QMessageBox.Yes | QMessageBox.No,
        )
        if r == QMessageBox.Yes:
            self.db.delete_collection(cid)
            self._reload_tree()

    def _rename_request(self, rid: int) -> None:
        rec = self.db.get_request(rid)
        if not rec:
            return
        name, ok = QInputDialog.getText(self, t("Rename"), t("Name:"), text=rec.name)
        if ok and name.strip():
            rec.name = name.strip()
            self.db.save_request(rec)
            self._reload_tree()

    def _delete_request(self, rid: int) -> None:
        r = QMessageBox.question(
            self, t("Delete request"), t("Delete this request?"), QMessageBox.Yes | QMessageBox.No
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
                t(
                    "Status: {code}\nTime: {ms} ms\nAt: {ts}",
                    code=h["status_code"],
                    ms=h["duration_ms"],
                    ts=h["created_at"],
                )
            )
            self.history_list.addItem(item)

    def _on_history_double_click(self, item: QListWidgetItem) -> None:
        hid = item.data(Qt.UserRole)
        if hid is not None:
            self.history_selected.emit(int(hid))

    # ── filter ────────────────────────────────────────────────────────────
    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()

        def walk(item: QTreeWidgetItem) -> bool:
            visible_children = False
            for i in range(item.childCount()):
                if walk(item.child(i)):
                    visible_children = True
            own = needle in item.text(0).lower()
            show = visible_children or own or not needle
            item.setHidden(not show)
            return show

        for i in range(self.tree.topLevelItemCount()):
            walk(self.tree.topLevelItem(i))

        for r in range(self.history_list.count()):
            it = self.history_list.item(r)
            it.setHidden(bool(needle) and needle not in it.text().lower())
