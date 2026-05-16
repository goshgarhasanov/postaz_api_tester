"""Left sidebar — the Postaz brand mark plus two stacked panels.

The "Collections" panel is a tree of folders → saved requests.
The "History" panel is a flat list of the last 200 executed calls.
Both share one search box that filters by case-insensitive substring."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from PySide6.QtCore import QEvent, QRect, QRectF, Qt, Signal
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QBrush,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPainterPath,
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
from .dialogs import confirm_delete
from .icons import icon_folder, icon_globe, icon_import, icon_plus
from .logo import Logo
from .widgets import IconButton


def _method_label(method: str) -> str:
    return method.upper()[:6]


# Method → soft brand color used by the sidebar delegate badge.
# Matches the Postman desktop client's method colour palette.
_METHOD_COLORS = {
    "GET":     ("#1F3A2F", "#6BBE7B"),
    "POST":    ("#3D2F1C", "#FFB400"),
    "PUT":     ("#243245", "#66B5F5"),
    "PATCH":   ("#2F2348", "#C792EA"),
    "DELETE":  ("#3A1F24", "#F45B69"),
    "HEAD":    ("#1F3838", "#80CBC4"),
    "OPTIONS": ("#1F3838", "#80CBC4"),
}


TRASH_ZONE_W = 32   # px reserved at the right edge for the trash icon


class _SidebarDelegate(QStyledItemDelegate):
    """Custom painter for both collection and request rows.

    Layout for a request row:
        ┌───────────────────────────────────────────────┐
        │ [METHOD]  request name                  🗑    │
        └───────────────────────────────────────────────┘

    Layout for a collection row (folder):
        ┌───────────────────────────────────────────────┐
        │  📁  Collection name                    🗑    │
        └───────────────────────────────────────────────┘

    The trash icon only renders on hover, and only for real (non-Quick-Saves)
    collections / saved requests. Clicking it emits `delete_clicked` with the
    underlying row payload."""

    delete_clicked = Signal(tuple)   # ("collection"|"request"|"history", id)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        payload = index.data(Qt.UserRole)
        if not (payload and isinstance(payload, tuple)):
            super().paint(painter, option, index)
            return
        kind = payload[0]
        if kind in ("request", "history"):
            self._paint_request(painter, option, index, payload)
        elif kind == "collection":
            self._paint_collection(painter, option, index, payload)
        else:
            super().paint(painter, option, index)

    # ── shared bg ────────────────────────────────────────────────────
    def _paint_background(self, painter: QPainter, opt: QStyleOptionViewItem) -> None:
        rect = opt.rect
        if opt.state & QStyle.State_Selected:
            painter.setBrush(QColor("#3A3A3A"))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect.adjusted(2, 1, -2, -1), 6, 6)
        elif opt.state & QStyle.State_MouseOver:
            painter.setBrush(QColor("#2A2A2A"))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect.adjusted(2, 1, -2, -1), 6, 6)

    # ── request row ──────────────────────────────────────────────────
    def _paint_request(self, painter, option, index, payload) -> None:
        method, name = index.data(Qt.UserRole + 1) or ("GET", index.data(Qt.DisplayRole) or "")
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        rect = opt.rect

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        self._paint_background(painter, opt)

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

        # request name — leave room on the right for the trash icon
        text_x = bx + badge_w + 10
        right_inset = TRASH_ZONE_W if (opt.state & QStyle.State_MouseOver) else 6
        text_rect = QRectF(text_x, rect.y(), rect.width() - text_x - right_inset, rect.height())
        text_color = QColor("#FFFFFF") if opt.state & (QStyle.State_Selected | QStyle.State_MouseOver) else QColor("#C7C7C7")
        painter.setPen(text_color)
        font = QFont(option.font)
        font.setPointSizeF(9.5)
        painter.setFont(font)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, name)

        # trash icon on hover
        if opt.state & QStyle.State_MouseOver:
            self._paint_trash(painter, rect)
        painter.restore()

    # ── collection row ───────────────────────────────────────────────
    def _paint_collection(self, painter, option, index, payload) -> None:
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        rect = opt.rect
        col_id = payload[1] if len(payload) > 1 else 0
        is_quick_saves = (col_id == 0)
        name = index.data(Qt.DisplayRole) or ""

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        self._paint_background(painter, opt)

        # folder glyph — orange-tinted rounded rect with a small tab (Postman vibe)
        glyph_size = 16
        gx = rect.x() + 8
        gy = rect.y() + (rect.height() - glyph_size) / 2
        path = QPainterPath()
        path.moveTo(gx, gy + 4)
        path.lineTo(gx + 5, gy + 4)
        path.lineTo(gx + 7, gy + 1)
        path.lineTo(gx + glyph_size, gy + 1)
        path.lineTo(gx + glyph_size, gy + glyph_size)
        path.lineTo(gx, gy + glyph_size)
        path.closeSubpath()
        painter.setBrush(QColor("#3D2418"))
        painter.setPen(QPen(QColor("#FF8557"), 1.3))
        painter.drawPath(path)

        # collection name
        right_inset = TRASH_ZONE_W if (opt.state & QStyle.State_MouseOver and not is_quick_saves) else 6
        text_x = gx + glyph_size + 12
        text_rect = QRectF(text_x, rect.y(), rect.width() - text_x - right_inset, rect.height())
        font = QFont(option.font)
        font.setPointSizeF(10.0)
        font.setBold(True)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0.2)
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF") if opt.state & QStyle.State_MouseOver else QColor("#E1E1E1"))
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, name)

        # trash icon on hover — never on the Quick Saves pseudo-collection
        if (opt.state & QStyle.State_MouseOver) and not is_quick_saves:
            self._paint_trash(painter, rect)
        painter.restore()

    # ── trash glyph ──────────────────────────────────────────────────
    def _paint_trash(self, painter: QPainter, row_rect) -> None:
        # Right-aligned 14x14 trash glyph, drawn at the row's vertical middle.
        size = 14
        x = row_rect.right() - 10 - size
        y = row_rect.y() + (row_rect.height() - size) / 2
        pen = QPen(QColor("#F45B69"))
        pen.setWidthF(1.4)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        # lid
        painter.drawLine(int(x + 1), int(y + 3), int(x + size - 1), int(y + 3))
        # handle
        painter.drawLine(int(x + 4), int(y + 1), int(x + size - 4), int(y + 1))
        painter.drawLine(int(x + 4), int(y + 1), int(x + 4), int(y + 3))
        painter.drawLine(int(x + size - 4), int(y + 1), int(x + size - 4), int(y + 3))
        # body
        body = QPainterPath()
        body.moveTo(x + 2, y + 4)
        body.lineTo(x + 3, y + size - 1)
        body.lineTo(x + size - 3, y + size - 1)
        body.lineTo(x + size - 2, y + 4)
        painter.drawPath(body)
        # ticks
        painter.drawLine(int(x + 5), int(y + 6), int(x + 5), int(y + size - 3))
        painter.drawLine(int(x + size - 5), int(y + 6), int(x + size - 5), int(y + size - 3))

    # ── click handling ───────────────────────────────────────────────
    def editorEvent(self, event, model, option, index) -> bool:
        if event.type() == QEvent.MouseButtonRelease:
            payload = index.data(Qt.UserRole)
            if isinstance(payload, tuple) and len(payload) >= 2:
                kind, ident = payload[0], payload[1]
                if kind == "collection" and ident == 0:
                    return False  # Quick Saves — no trash
                rect = option.rect
                trash_x = rect.right() - TRASH_ZONE_W
                if event.position().x() >= trash_x:
                    self.delete_clicked.emit((kind, int(ident)))
                    return True
        return False

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(max(size.height(), 36))
        return size


# Backwards-compatible alias (was named _RequestItemDelegate in an earlier rev).
_RequestItemDelegate = _SidebarDelegate


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

        # ─ Brand header (logo only — language picker lives in the menu bar) ─
        brand_wrap = QFrame()
        brand_wrap.setObjectName("brandWrap")
        bl = QHBoxLayout(brand_wrap)
        bl.setContentsMargins(16, 14, 16, 10)
        bl.setSpacing(8)
        self.logo = Logo(self, height=26)
        bl.addWidget(self.logo)
        bl.addStretch()
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
        # Text-on-pill style ("curl +") is more discoverable than a bare icon.
        self.btn_import = QPushButton("curl +")
        self.btn_import.setObjectName("curlButton")
        self.btn_import.setCursor(Qt.PointingHandCursor)
        self.btn_import.setToolTip(self._tr_import_tip())
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
        self.tree.setIndentation(14)
        self.tree.setMouseTracking(True)
        self.tree.setUniformRowHeights(True)
        self._tree_delegate = _SidebarDelegate(self.tree)
        self._tree_delegate.delete_clicked.connect(self._on_delete_clicked)
        self.tree.setItemDelegate(self._tree_delegate)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_tree_context)
        self.tree.itemDoubleClicked.connect(self._on_tree_double_click)
        # event filter on the viewport so we can flip the cursor when the
        # mouse enters the trash zone of any row.
        self.tree.viewport().setMouseTracking(True)
        self.tree.viewport().installEventFilter(self)
        self.stack.addWidget(self.tree)

        # History panel = a "Clear all" pill on top + the list of past requests.
        history_panel = QWidget()
        hpl = QVBoxLayout(history_panel)
        hpl.setContentsMargins(0, 0, 0, 0)
        hpl.setSpacing(0)

        clear_row = QHBoxLayout()
        clear_row.setContentsMargins(12, 4, 12, 6)
        clear_row.addStretch()
        self.btn_clear_history = QPushButton(self._tr_clear_history())
        self.btn_clear_history.setObjectName("clearHistoryButton")
        self.btn_clear_history.setCursor(Qt.PointingHandCursor)
        self.btn_clear_history.clicked.connect(self._clear_history)
        clear_row.addWidget(self.btn_clear_history)
        hpl.addLayout(clear_row)

        self.history_list = QListWidget()
        self.history_list.setObjectName("historyList")
        self.history_list.setMouseTracking(True)
        self.history_list.itemDoubleClicked.connect(self._on_history_double_click)
        # Same cursor-flip on the history list's trash zone.
        self.history_list.viewport().setMouseTracking(True)
        self.history_list.viewport().installEventFilter(self)
        hpl.addWidget(self.history_list, 1)

        self.stack.addWidget(history_panel)

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

    def _tr_clear_history(self) -> str:
        return {
            "en": "Clear all",
            "az": "Hamısını sil",
            "tr": "Hepsini sil",
        }[translator.language]

    def _clear_history(self) -> None:
        """Wipe the history table, honouring the suppression setting."""
        if confirm_delete(self, self.db, "history"):
            self.db.clear_history()
            self._reload_history()

    def _retranslate(self, _lang: str | None = None) -> None:
        self.btn_collections.setText(t("Collections"))
        self.btn_history.setText(t("History"))
        self.btn_add.setToolTip(t("New collection"))
        self.btn_import.setToolTip(self._tr_import_tip())
        if hasattr(self, "btn_clear_history"):
            self.btn_clear_history.setText(self._tr_clear_history())
        self.search.setPlaceholderText(t("Search…"))
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
        """Toggle between the Collections tree and the History list."""
        self.stack.setCurrentIndex(idx)
        if idx == 1:
            self._reload_history()

    # ── tree ──────────────────────────────────────────────────────────────
    def _reload_tree(self) -> None:
        self.tree.clear()
        collections = self.db.list_collections()
        cmap: dict[int, QTreeWidgetItem] = {}

        # Quick Saves pseudo-collection at the top — same delegate paints it,
        # but the trash icon is suppressed by id==0.
        loose = QTreeWidgetItem([t("Quick Saves")])
        loose.setData(0, Qt.UserRole, ("collection", 0))
        self.tree.addTopLevelItem(loose)

        for col in collections:
            item = QTreeWidgetItem([col.name])
            item.setData(0, Qt.UserRole, ("collection", col.id))
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
        if confirm_delete(self, self.db, "collection"):
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
        if confirm_delete(self, self.db, "request"):
            self.db.delete_request(rid)
            self._reload_tree()

    # ── history ───────────────────────────────────────────────────────────
    def _reload_history(self) -> None:
        self.history_list.clear()
        for h in self.db.list_history(100):
            item = QListWidgetItem(h["url"])
            # Tagged as "history" (not "request") so the delegate's trash
            # click routes to history deletion, not request deletion.
            item.setData(Qt.UserRole, ("history", int(h["id"])))
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
        if not isinstance(self.history_list.itemDelegate(), _SidebarDelegate):
            d = _SidebarDelegate(self.history_list)
            d.delete_clicked.connect(self._on_delete_clicked)
            self.history_list.setItemDelegate(d)

    def _on_history_double_click(self, item: QListWidgetItem) -> None:
        payload = item.data(Qt.UserRole)
        if isinstance(payload, tuple) and len(payload) == 2:
            self.history_selected.emit(int(payload[1]))

    # ── cursor flip when hovering the trash zone of any row ──────────────
    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseMove:
            view = None
            if source is self.tree.viewport():
                view = self.tree
            elif source is self.history_list.viewport():
                view = self.history_list
            if view is not None:
                self._cursor_for_pos(view, event.position().toPoint())
                return False
        elif event.type() == QEvent.Leave:
            if source is self.tree.viewport():
                self.tree.viewport().unsetCursor()
            elif source is self.history_list.viewport():
                self.history_list.viewport().unsetCursor()
        return super().eventFilter(source, event)

    def _cursor_for_pos(self, view, pos) -> None:
        """Show a pointing-hand cursor when the mouse sits in a row's trash zone."""
        index = view.indexAt(pos)
        viewport = view.viewport()
        if not index.isValid():
            viewport.unsetCursor()
            return
        payload = index.data(Qt.UserRole)
        if not (isinstance(payload, tuple) and len(payload) == 2):
            viewport.unsetCursor()
            return
        kind, ident = payload[0], payload[1]
        # Quick Saves (id == 0) has no trash icon — keep default cursor.
        if kind == "collection" and ident == 0:
            viewport.unsetCursor()
            return
        rect = view.visualRect(index)
        trash_left = rect.right() - TRASH_ZONE_W
        if pos.x() >= trash_left:
            viewport.setCursor(Qt.PointingHandCursor)
        else:
            viewport.unsetCursor()

    # ── unified delete dispatcher (one per delegate click) ────────────────
    def _on_delete_clicked(self, payload: tuple) -> None:
        """Routes a trash-icon click to the right deletion handler."""
        if not isinstance(payload, tuple) or len(payload) != 2:
            return
        kind, ident = payload
        if kind == "collection":
            self._delete_collection(int(ident))
        elif kind == "request":
            self._delete_request(int(ident))
        elif kind == "history":
            self._delete_history_entry(int(ident))

    def _delete_history_entry(self, history_id: int) -> None:
        """Remove a single history row after a confirmation prompt."""
        if confirm_delete(self, self.db, "history"):
            with self.db._conn() as c:                       # noqa — internal helper is fine here
                c.execute("DELETE FROM history WHERE id = ?", (history_id,))
            self._reload_history()

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
