"""Left sidebar — the Postaz brand mark plus two stacked panels.

The "Collections" panel is a tree of folders → saved requests.
The "History" panel is a flat list of the last 200 executed calls.
Both share one search box that filters by case-insensitive substring."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QBrush,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPen,
)
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
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..database import Database, RequestRecord
from ..i18n import LANGUAGE_LABELS, LANGUAGES, set_language, t, translator
from .icons import icon_folder, icon_globe, icon_import, icon_plus
from .logo import Logo
from .widgets import IconButton


def _method_label(method: str) -> str:
    return method.upper()[:6]


# Method → soft brand color used by the sidebar delegate badge.
_METHOD_COLORS = {
    "GET":     ("#1f3a2c", "#5ed29b"),
    "POST":    ("#3d2f1c", "#f4b860"),
    "PUT":     ("#1f3245", "#6fb8ff"),
    "PATCH":   ("#2f2348", "#bda6ff"),
    "DELETE":  ("#3a1f24", "#ff8090"),
    "HEAD":    ("#262842", "#a89bff"),
    "OPTIONS": ("#262842", "#a89bff"),
}


class _RequestItemDelegate(QStyledItemDelegate):
    """Custom painter for sidebar request rows.

    Renders a small coloured method tag + the request name. Folder rows
    (collections) fall back to the default delegate so their bold text +
    icon stay intact."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        payload = index.data(Qt.UserRole)
        if not (payload and isinstance(payload, tuple) and payload[0] == "request"):
            super().paint(painter, option, index)
            return

        method, name = index.data(Qt.UserRole + 1) or ("GET", index.data(Qt.DisplayRole) or "")
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        rect = opt.rect

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # background (hover/selected handled by stylesheet, but we re-paint
        # the rounded fill explicitly so the underlying tree highlight aligns
        # perfectly with our padded content).
        if opt.state & QStyle.State_Selected:
            painter.setBrush(QColor("#25254a"))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect.adjusted(2, 1, -2, -1), 6, 6)
        elif opt.state & QStyle.State_MouseOver:
            painter.setBrush(QColor("#1a1c2e"))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect.adjusted(2, 1, -2, -1), 6, 6)

        # method badge
        bg, fg = _METHOD_COLORS.get(method.upper(), ("#262842", "#bda6ff"))
        badge_w = 52
        badge_h = 18
        bx = rect.x() + 10
        by = rect.y() + (rect.height() - badge_h) / 2
        painter.setBrush(QColor(bg))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(bx, by, badge_w, badge_h), 4, 4)
        font = QFont(option.font)
        font.setPointSizeF(8.5)
        font.setBold(True)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
        painter.setFont(font)
        painter.setPen(QColor(fg))
        painter.drawText(QRectF(bx, by, badge_w, badge_h), Qt.AlignCenter, method.upper())

        # request name
        text_x = bx + badge_w + 10
        text_rect = QRectF(text_x, rect.y(), rect.width() - text_x - 8, rect.height())
        painter.setPen(QColor("#e6e8f5") if opt.state & (QStyle.State_Selected | QStyle.State_MouseOver) else QColor("#b6bad0"))
        font = QFont(option.font)
        font.setPointSizeF(9.5)
        painter.setFont(font)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, name)

        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(max(size.height(), 32))
        return size


class Sidebar(QWidget):
    """The left-hand navigation surface.

    Emits high-level intents (open this request / open this history entry /
    create a new request in this collection) — never mutates the editor
    directly. `MainWindow` glues the signals together."""

    request_selected = Signal(int)        # user double-clicked a saved request
    history_selected = Signal(int)        # user double-clicked a history row
    new_request_requested = Signal(int)   # "New request" was triggered in a collection
    import_curl_requested = Signal()      # toolbar "Import cURL" button clicked

    def __init__(self, db: Database, parent: QWidget | None = None):
        super().__init__(parent)
        self.db = db
        self.setObjectName("sidebar")
        self.setMinimumWidth(270)
        self.setMaximumWidth(420)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ─ Brand header (logo + language picker) ─────────────────────────
        brand_wrap = QFrame()
        brand_wrap.setObjectName("brandWrap")
        bl = QHBoxLayout(brand_wrap)
        bl.setContentsMargins(16, 14, 16, 10)
        bl.setSpacing(8)
        self.logo = Logo(self, height=26)
        bl.addWidget(self.logo)
        bl.addStretch()

        # Always-visible language chip — opens a popup menu with EN/AZ/TR
        self.lang_btn = QToolButton()
        self.lang_btn.setObjectName("langButton")
        self.lang_btn.setCursor(Qt.PointingHandCursor)
        self.lang_btn.setIcon(icon_globe("#a89bff"))
        self.lang_btn.setPopupMode(QToolButton.InstantPopup)
        self.lang_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.lang_btn.setText(translator.language.upper())
        lang_menu = QMenu(self.lang_btn)
        self._lang_actions: dict[str, QAction] = {}
        group = QActionGroup(self)
        group.setExclusive(True)
        for code in LANGUAGES:
            act = QAction(LANGUAGE_LABELS[code], self.lang_btn)
            act.setCheckable(True)
            act.setChecked(code == translator.language)
            act.triggered.connect(lambda _c=False, lc=code: self._switch_language(lc))
            group.addAction(act)
            lang_menu.addAction(act)
            self._lang_actions[code] = act
        self.lang_btn.setMenu(lang_menu)
        bl.addWidget(self.lang_btn)
        outer.addWidget(brand_wrap)

        # ─ Tab bar ───────────────────────────────────────────────────────
        tab_bar = QWidget()
        tab_bar.setObjectName("sidebarTabBar")
        tb_layout = QHBoxLayout(tab_bar)
        tb_layout.setContentsMargins(12, 8, 12, 8)
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

        # Import cURL button — sits right next to the "+" so users can paste a
        # curl command into the sidebar without hunting through the File menu.
        self.btn_import = IconButton("", self._tr_import_tip())
        self.btn_import.setIcon(icon_import("#c9cce0"))
        tb_layout.addWidget(self.btn_import)

        self.btn_add = IconButton("", t("New collection"))
        self.btn_add.setIcon(icon_plus("#c9cce0"))
        self.btn_add.setIconSize(self.btn_add.iconSize())
        tb_layout.addWidget(self.btn_add)
        outer.addWidget(tab_bar)

        # ─ Search ────────────────────────────────────────────────────────
        search_wrap = QFrame()
        sl = QHBoxLayout(search_wrap)
        sl.setContentsMargins(12, 0, 12, 10)
        self.search = QLineEdit()
        self.search.setPlaceholderText(t("Search…"))
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumHeight(34)
        sl.addWidget(self.search)
        outer.addWidget(search_wrap)

        # ─ Stack: tree | history ─────────────────────────────────────────
        self.stack = QStackedWidget()
        outer.addWidget(self.stack, 1)

        self.tree = QTreeWidget()
        self.tree.setObjectName("collectionsTree")
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(16)
        self.tree.setMouseTracking(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setItemDelegate(_RequestItemDelegate(self.tree))
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
        self.btn_import.clicked.connect(self.import_curl_requested.emit)
        self.search.textChanged.connect(self._apply_filter)

        translator.language_changed.connect(self._retranslate)
        self.refresh()

    # ── retranslate ───────────────────────────────────────────────────────
    def _tr_import_tip(self) -> str:
        return {
            "en": "Import cURL  (Ctrl+I)",
            "az": "cURL idxal et  (Ctrl+I)",
            "tr": "cURL içe aktar  (Ctrl+I)",
        }[translator.language]

    def _retranslate(self, _lang: str | None = None) -> None:
        self.btn_collections.setText(t("Collections"))
        self.btn_history.setText(t("History"))
        self.btn_add.setToolTip(t("New collection"))
        self.btn_import.setToolTip(self._tr_import_tip())
        self.search.setPlaceholderText(t("Search…"))
        self.lang_btn.setText(translator.language.upper())
        for code, act in self._lang_actions.items():
            act.setChecked(code == translator.language)
        self._reload_tree()
        self._reload_history()

    def _switch_language(self, code: str) -> None:
        """Apply the chosen language, persist it to the DB, refresh the chip."""
        set_language(code)
        self.db.set_setting("language", code)
        self.lang_btn.setText(code.upper())

    # ── public ────────────────────────────────────────────────────────────
    def refresh(self) -> None:
        self._reload_tree()
        self._reload_history()

    def _switch(self, idx: int) -> None:
        """Smooth fade between Collections and History panels."""
        from .animations import fade_in
        self.stack.setCurrentIndex(idx)
        widget = self.stack.currentWidget()
        if widget:
            fade_in(widget, 180)
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
        # Three pieces of data on the row:
        #   UserRole     — ("request", request_id) marker (used by handlers)
        #   UserRole + 1 — (method, name) — what the delegate paints
        item = QTreeWidgetItem([r.name])
        item.setData(0, Qt.UserRole, ("request", r.id))
        item.setData(0, Qt.UserRole + 1, (r.method, r.name))
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
            item = QListWidgetItem(h["url"])
            # Stored both as the synthetic delegate marker (with history_id
            # so we can route on double-click) AND with method/name for the
            # badge painter.
            item.setData(Qt.UserRole, ("request", int(h["id"])))
            item.setData(Qt.UserRole + 1, (h["method"], h["url"]))
            item.setToolTip(
                t(
                    "Status: {code}\nTime: {ms} ms\nAt: {ts}",
                    code=h["status_code"],
                    ms=h["duration_ms"],
                    ts=h["created_at"],
                )
            )
            self.history_list.addItem(item)
        # Reuse the same delegate so history rows look identical to saved ones.
        if not isinstance(self.history_list.itemDelegate(), _RequestItemDelegate):
            self.history_list.setItemDelegate(_RequestItemDelegate(self.history_list))

    def _on_history_double_click(self, item: QListWidgetItem) -> None:
        payload = item.data(Qt.UserRole)
        if isinstance(payload, tuple) and len(payload) == 2:
            self.history_selected.emit(int(payload[1]))

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
