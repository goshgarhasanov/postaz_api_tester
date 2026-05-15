"""Modern dark + light themes via QSS."""
from __future__ import annotations


DARK = """
* {
    font-family: "Segoe UI", "Inter", "SF Pro Text", Arial;
    color: #e6e8f5;
}
QWidget {
    background: #0f1019;
}
QMainWindow, QDialog { background: #0f1019; }

QSplitter::handle { background: #14151f; width: 1px; height: 1px; }
QSplitter::handle:hover { background: #7c5cff; }

/* ── Sidebar ─────────────────────────────────────────────────────── */
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
    padding: 4px 10px 4px 6px;
    color: #c9cce0;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
}
QToolButton#langButton:hover {
    background: #20223a;
    border: 1px solid #7c5cff;
    color: #ffffff;
}
QToolButton#langButton::menu-indicator { width: 0; height: 0; image: none; }
#sidebarHeader {
    background: transparent;
    color: #a4a7c2;
    font-size: 11px;
    letter-spacing: 1px;
    padding: 14px 16px 6px 16px;
}
#sidebarTabBar QPushButton {
    background: transparent;
    color: #8b8fab;
    border: none;
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 12px;
}
#sidebarTabBar QPushButton:hover { color: #e6e8f5; background: #1c1d2b; }
#sidebarTabBar QPushButton:checked {
    background: #1f2030;
    color: #e6e8f5;
}

QTreeWidget#collectionsTree, QListWidget#historyList {
    background: transparent;
    border: none;
    outline: 0;
    padding: 4px 6px;
}
QTreeWidget#collectionsTree::item, QListWidget#historyList::item {
    height: 30px;
    border-radius: 6px;
    padding: 0 8px;
    color: #c9cce0;
}
QTreeWidget#collectionsTree::item:hover, QListWidget#historyList::item:hover {
    background: #1c1d2b;
}
QTreeWidget#collectionsTree::item:selected, QListWidget#historyList::item:selected {
    background: #262842;
    color: #ffffff;
}
QTreeWidget#collectionsTree::branch { background: transparent; }

/* ── Topbar / Request URL row ────────────────────────────────────── */
#topBar {
    background: #14151f;
    border-bottom: 1px solid #1f2030;
}
#urlBar {
    background: #0f1019;
    border: 1px solid #2a2c40;
    border-radius: 8px;
    padding: 0 12px;
    min-height: 38px;
    font-size: 13px;
    color: #e6e8f5;
}
#urlBar:focus {
    border: 1px solid #7c5cff;
}
#methodCombo {
    background: #0f1019;
    border: 1px solid #2a2c40;
    border-radius: 8px;
    min-height: 38px;
    padding: 0 14px;
    font-weight: 600;
    color: #e6e8f5;
}
#methodCombo:hover { border: 1px solid #7c5cff; }
#methodCombo::drop-down { border: none; width: 18px; }
#methodCombo QAbstractItemView {
    background: #1a1b29;
    border: 1px solid #2a2c40;
    color: #e6e8f5;
    selection-background-color: #7c5cff;
    padding: 4px;
}

/* ── Buttons ─────────────────────────────────────────────────────── */
#primaryButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #7c5cff, stop:1 #5a3fd9);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0 22px;
    font-weight: 600;
    font-size: 13px;
}
#primaryButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #8d70ff, stop:1 #6a4fe6);
}
#primaryButton:pressed { background: #5a3fd9; }
#primaryButton:disabled {
    background: #2a2c40;
    color: #6e718a;
}
#ghostButton {
    background: transparent;
    color: #c9cce0;
    border: 1px solid #2a2c40;
    border-radius: 7px;
    padding: 0 14px;
    font-size: 12px;
}
#ghostButton:hover {
    background: #1c1d2b;
    border: 1px solid #3a3c55;
    color: #ffffff;
}
#iconButton {
    background: transparent;
    border: none;
    border-radius: 6px;
    color: #a4a7c2;
    font-size: 14px;
    padding: 4px;
}
#iconButton:hover { background: #1c1d2b; color: #ffffff; }

/* ── Tabs ────────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: none;
    background: #0f1019;
    top: -1px;
}
QTabBar {
    background: transparent;
}
QTabBar::tab {
    background: transparent;
    color: #8b8fab;
    padding: 9px 16px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 4px;
    font-size: 12px;
}
QTabBar::tab:hover { color: #e6e8f5; }
QTabBar::tab:selected {
    color: #e6e8f5;
    border-bottom: 2px solid #7c5cff;
    font-weight: 600;
}

/* ── Tables ──────────────────────────────────────────────────────── */
QTableWidget#kvTable {
    background: transparent;
    border: none;
    gridline-color: transparent;
}
QTableWidget#kvTable::item {
    background: transparent;
    border: none;
    padding: 4px 8px;
    color: #c9cce0;
}
QTableWidget#kvTable::item:selected {
    background: #1c1d2b;
    color: #ffffff;
}
QHeaderView::section {
    background: #14151f;
    color: #8b8fab;
    border: none;
    border-bottom: 1px solid #1f2030;
    padding: 8px 10px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.4px;
}

/* ── Text edits / code areas ────────────────────────────────────── */
QPlainTextEdit, QTextEdit {
    background: #0a0b13;
    border: 1px solid #1f2030;
    border-radius: 8px;
    padding: 10px;
    selection-background-color: #7c5cff;
    font-family: "JetBrains Mono", "Consolas", "Courier New";
    font-size: 12px;
    color: #d8dcff;
}
QPlainTextEdit:focus, QTextEdit:focus {
    border: 1px solid #7c5cff;
}

QLineEdit {
    background: #0f1019;
    border: 1px solid #2a2c40;
    border-radius: 7px;
    padding: 7px 10px;
    color: #e6e8f5;
}
QLineEdit:focus { border: 1px solid #7c5cff; }

QComboBox {
    background: #0f1019;
    border: 1px solid #2a2c40;
    border-radius: 7px;
    padding: 6px 10px;
    color: #e6e8f5;
}
QComboBox:hover { border: 1px solid #3a3c55; }
QComboBox::drop-down { border: none; width: 18px; }
QComboBox QAbstractItemView {
    background: #1a1b29;
    border: 1px solid #2a2c40;
    color: #e6e8f5;
    selection-background-color: #7c5cff;
    padding: 4px;
}

QCheckBox {
    color: #c9cce0;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #3a3c55;
    border-radius: 4px;
    background: #0f1019;
}
QCheckBox::indicator:hover { border: 1px solid #7c5cff; }
QCheckBox::indicator:checked {
    background: #7c5cff;
    border: 1px solid #7c5cff;
    image: none;
}

/* ── Scrollbars ──────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 4px 2px;
}
QScrollBar::handle:vertical {
    background: #2a2c40;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #3a3c55; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px 4px;
}
QScrollBar::handle:horizontal {
    background: #2a2c40;
    border-radius: 4px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover { background: #3a3c55; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }

/* ── Menu ────────────────────────────────────────────────────────── */
QMenuBar {
    background: #14151f;
    color: #c9cce0;
    border-bottom: 1px solid #1f2030;
    padding: 4px;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 5px;
}
QMenuBar::item:selected { background: #1c1d2b; }
QMenu {
    background: #1a1b29;
    border: 1px solid #2a2c40;
    padding: 6px;
    border-radius: 8px;
    color: #e6e8f5;
}
QMenu::item {
    padding: 7px 22px 7px 14px;
    border-radius: 5px;
}
QMenu::item:selected { background: #7c5cff; color: white; }
QMenu::separator {
    height: 1px;
    background: #2a2c40;
    margin: 4px 6px;
}

QStatusBar {
    background: #14151f;
    color: #8b8fab;
    border-top: 1px solid #1f2030;
}

QToolTip {
    background: #1a1b29;
    color: #e6e8f5;
    border: 1px solid #2a2c40;
    border-radius: 5px;
    padding: 4px 8px;
}

/* ── Custom labels ───────────────────────────────────────────────── */
.sectionLabel {
    color: #8b8fab;
    font-size: 11px;
    letter-spacing: 1.2px;
    font-weight: 600;
}
"""


