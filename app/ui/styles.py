"""Postaz dark theme — single source of truth for every pixel.

Design system (mental model for future edits):

  Spacing scale     : 4, 8, 12, 16, 20, 24, 32  (multiples of 4)
  Radius scale      : 4 (chip), 6 (button), 8 (input/card), 12 (badge), 14 (pill)
  Brand purple      : #7c5cff   (CTA + focus ring + accents)
  Brand purple soft : #a89bff   (folder icons, decorative text)
  Background scale  : #0a0b13 (deepest, code) → #0f1019 (canvas)
                       → #14151f (chrome) → #1a1b29 (popovers) → #20223a (hover)
  Text scale        : #ffffff (selected) → #e6e8f5 (body) → #c9cce0 (subtle)
                       → #a4a7c2 (label) → #8b8fab (placeholder) → #6b6f88 (muted)
  Border scale      : #1f2030 (faint) → #2a2c40 (default) → #3a3c55 (hover)
  Status colors     : 2xx #5ed29b · 3xx #6fb8ff · 4xx #f4b860 · 5xx #ff6e7c
"""


DARK = """
/* ─── globals ─────────────────────────────────────────────────── */
* {
    font-family: "Segoe UI", "Inter", "SF Pro Text", Arial;
    color: #e6e8f5;
    outline: 0;
}
QWidget { background: #0f1019; }
QMainWindow, QDialog { background: #0f1019; }
QToolTip {
    background: #1a1b29;
    color: #e6e8f5;
    border: 1px solid #2a2c40;
    border-radius: 6px;
    padding: 6px 10px;
}

/* ─── splitter (drag handle visible enough to find) ───────────── */
QSplitter::handle {
    background: #1a1b29;
}
QSplitter::handle:horizontal { width: 3px; }
QSplitter::handle:vertical   { height: 3px; }
QSplitter::handle:hover {
    background: #7c5cff;
}

/* ─── sidebar ─────────────────────────────────────────────────── */
#sidebar {
    background: #14151f;
    border-right: 1px solid #1f2030;
}
#brandWrap {
    background: transparent;
    border-bottom: 1px solid #1f2030;
}
QToolButton#langButton {
    background: #1a1b29;
    border: 1px solid #2a2c40;
    border-radius: 14px;
    padding: 5px 12px;
    color: #c9cce0;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    min-height: 22px;
}
QToolButton#langButton:hover {
    background: #20223a;
    border-color: #7c5cff;
    color: #ffffff;
}
QToolButton#langButton::menu-indicator { width: 0; height: 0; image: none; }

#sidebarTabBar QPushButton {
    background: transparent;
    color: #8b8fab;
    border: none;
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    min-height: 22px;
}
#sidebarTabBar QPushButton:hover { color: #e6e8f5; background: #1c1d2b; }
#sidebarTabBar QPushButton:checked {
    background: #1f2030;
    color: #e6e8f5;
}

QTreeWidget#collectionsTree,
QListWidget#historyList {
    background: transparent;
    border: none;
    outline: 0;
    padding: 6px 8px;
}
QTreeWidget#collectionsTree::item,
QListWidget#historyList::item {
    height: 32px;
    border-radius: 6px;
    padding: 0 8px;
    color: #c9cce0;
    margin: 1px 0;
}
QTreeWidget#collectionsTree::item:hover,
QListWidget#historyList::item:hover { background: #1c1d2b; }
QTreeWidget#collectionsTree::item:selected,
QListWidget#historyList::item:selected {
    background: #262842;
    color: #ffffff;
}
QTreeWidget#collectionsTree::branch { background: transparent; }

/* ─── topbar (URL row) ────────────────────────────────────────── */
#topBar {
    background: #14151f;
    border-bottom: 1px solid #1f2030;
}
#urlBar {
    background: #0f1019;
    border: 1px solid #2a2c40;
    border-radius: 8px;
    padding: 0 14px;
    min-height: 40px;
    font-size: 13px;
    color: #e6e8f5;
    selection-background-color: #7c5cff;
}
#urlBar:focus  { border: 1px solid #7c5cff; }
#urlBar:hover  { border: 1px solid #3a3c55; }

#methodCombo {
    background: #0f1019;
    border: 1px solid #2a2c40;
    border-radius: 8px;
    min-height: 40px;
    padding: 0 14px;
    font-weight: 700;
    color: #e6e8f5;
}
#methodCombo:hover  { border: 1px solid #7c5cff; }
#methodCombo::drop-down { border: none; width: 20px; }
#methodCombo QAbstractItemView {
    background: #1a1b29;
    border: 1px solid #2a2c40;
    border-radius: 6px;
    color: #e6e8f5;
    selection-background-color: #7c5cff;
    padding: 4px;
    outline: 0;
}

/* ─── buttons ─────────────────────────────────────────────────── */
#primaryButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #7c5cff, stop:1 #5a3fd9);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0 22px;
    font-weight: 600;
    font-size: 13px;
    min-height: 40px;
}
#primaryButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #8d70ff, stop:1 #6a4fe6);
}
#primaryButton:pressed { background: #4f37c1; }
#primaryButton:disabled {
    background: #2a2c40;
    color: #6e718a;
}

#ghostButton {
    background: transparent;
    color: #c9cce0;
    border: 1px solid #2a2c40;
    border-radius: 7px;
    padding: 0 16px;
    font-size: 12px;
    font-weight: 500;
    min-height: 36px;
}
#ghostButton:hover {
    background: #1c1d2b;
    border: 1px solid #3a3c55;
    color: #ffffff;
}
#ghostButton:pressed { background: #20223a; }

#iconButton {
    background: transparent;
    border: none;
    border-radius: 6px;
    color: #a4a7c2;
    font-size: 14px;
    padding: 6px;
    min-width: 28px;
    min-height: 28px;
}
#iconButton:hover { background: #1c1d2b; color: #ffffff; }
#iconButton:pressed { background: #20223a; }

/* ─── tabs ────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: none;
    background: #0f1019;
    top: -1px;
}
QTabBar {
    background: transparent;
    qproperty-drawBase: 0;
}
QTabBar::tab {
    background: transparent;
    color: #8b8fab;
    padding: 10px 18px;
    border: none;
    border-bottom: 2px solid transparent;
    margin: 0 2px;
    font-size: 12px;
    font-weight: 500;
    min-width: 60px;
}
QTabBar::tab:hover { color: #e6e8f5; }
QTabBar::tab:selected {
    color: #ffffff;
    border-bottom: 2px solid #7c5cff;
    font-weight: 600;
}

/* ─── tables ──────────────────────────────────────────────────── */
QTableWidget#kvTable {
    background: transparent;
    border: none;
    gridline-color: transparent;
}
QTableWidget#kvTable::item {
    background: transparent;
    border: none;
    padding: 6px 10px;
    color: #c9cce0;
}
QTableWidget#kvTable::item:selected {
    background: #1c1d2b;
    color: #ffffff;
}
QTableWidget#kvTable::item:focus {
    background: #20223a;
    color: #ffffff;
}

QHeaderView::section {
    background: #14151f;
    color: #8b8fab;
    border: none;
    border-bottom: 1px solid #1f2030;
    padding: 10px 12px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.4px;
}

/* ─── code editors ────────────────────────────────────────────── */
QPlainTextEdit, QTextEdit {
    background: #0a0b13;
    border: 1px solid #1f2030;
    border-radius: 8px;
    padding: 12px;
    selection-background-color: #7c5cff;
    font-family: "JetBrains Mono", "Consolas", "Courier New";
    font-size: 12px;
    color: #d8dcff;
}
QPlainTextEdit:hover, QTextEdit:hover { border: 1px solid #2a2c40; }
QPlainTextEdit:focus, QTextEdit:focus { border: 1px solid #7c5cff; }

/* ─── line edits / combos ─────────────────────────────────────── */
QLineEdit {
    background: #0f1019;
    border: 1px solid #2a2c40;
    border-radius: 7px;
    padding: 8px 12px;
    color: #e6e8f5;
    min-height: 20px;
    selection-background-color: #7c5cff;
}
QLineEdit:hover { border: 1px solid #3a3c55; }
QLineEdit:focus { border: 1px solid #7c5cff; }

QComboBox {
    background: #0f1019;
    border: 1px solid #2a2c40;
    border-radius: 7px;
    padding: 6px 12px;
    color: #e6e8f5;
    min-height: 22px;
}
QComboBox:hover { border: 1px solid #3a3c55; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background: #1a1b29;
    border: 1px solid #2a2c40;
    border-radius: 6px;
    color: #e6e8f5;
    selection-background-color: #7c5cff;
    selection-color: white;
    padding: 4px;
    outline: 0;
}

/* ─── checkboxes ──────────────────────────────────────────────── */
QCheckBox {
    color: #c9cce0;
    spacing: 8px;
    background: transparent;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #3a3c55;
    border-radius: 4px;
    background: #0f1019;
}
QCheckBox::indicator:hover {
    border: 1px solid #7c5cff;
    background: #1c1d2b;
}
QCheckBox::indicator:checked {
    background: #7c5cff;
    border: 1px solid #7c5cff;
    image: none;
}
QCheckBox::indicator:checked:hover {
    background: #8d70ff;
    border: 1px solid #8d70ff;
}

/* ─── scrollbars ──────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 12px;
    margin: 4px 2px;
}
QScrollBar::handle:vertical {
    background: #2a2c40;
    border-radius: 4px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover { background: #3a3c55; }
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical { background: none; }

QScrollBar:horizontal {
    background: transparent;
    height: 12px;
    margin: 2px 4px;
}
QScrollBar::handle:horizontal {
    background: #2a2c40;
    border-radius: 4px;
    min-width: 28px;
}
QScrollBar::handle:horizontal:hover { background: #3a3c55; }
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal { background: none; }

/* ─── menu / status / titlebar ────────────────────────────────── */
QMenuBar {
    background: #14151f;
    color: #c9cce0;
    border-bottom: 1px solid #1f2030;
    padding: 4px 8px;
    min-height: 30px;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 6px;
    margin: 2px;
}
QMenuBar::item:selected { background: #1c1d2b; color: #ffffff; }
QMenuBar::item:pressed  { background: #20223a; }

QMenu {
    background: #1a1b29;
    border: 1px solid #2a2c40;
    padding: 6px;
    border-radius: 8px;
    color: #e6e8f5;
}
QMenu::item {
    padding: 8px 24px 8px 14px;
    border-radius: 5px;
    margin: 1px;
}
QMenu::item:selected { background: #7c5cff; color: white; }
QMenu::separator {
    height: 1px;
    background: #2a2c40;
    margin: 4px 8px;
}

QStatusBar {
    background: #14151f;
    color: #8b8fab;
    border-top: 1px solid #1f2030;
    padding: 0 8px;
    min-height: 26px;
}
QStatusBar::item { border: none; }

/* ─── labels ──────────────────────────────────────────────────── */
QLabel { background: transparent; }
"""
