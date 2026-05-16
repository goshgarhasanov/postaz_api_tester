"""Postaz theme — modelled on the Postman desktop client's dark palette.

Brand colour     : #FF6C37  (Postman orange — used for CTAs, focus rings, accents)
Brand hover      : #FF8557
Brand pressed    : #E55A2B

Background scale : #1A1A1A (deepest, code editors)
                   #1E1E1E (main canvas)
                   #212121 (chrome / topbar / sidebar)
                   #2A2A2A (popovers, inputs)
                   #303030 (hover surface)
                   #3A3A3A (active / selected surface)

Text scale       : #FFFFFF (selected / heading)
                   #E1E1E1 (body)
                   #C7C7C7 (secondary)
                   #A0A0A0 (label / muted)
                   #6B6B6B (placeholder / disabled)

Border scale     : #2E2E2E (default)
                   #3A3A3A (hover / divider)

Status colors    : 2xx #6BBE7B  ·  3xx #66B5F5  ·  4xx #FFB400  ·  5xx #F45B69
Method colors    : GET #6BBE7B · POST #FFB400 · PUT #66B5F5 · PATCH #C792EA ·
                   DELETE #F45B69 · HEAD/OPTIONS #80CBC4
"""


DARK = """
/* ─── globals ─────────────────────────────────────────────────── */
* {
    font-family: "Segoe UI", "Inter", "SF Pro Text", Arial;
    color: #E1E1E1;
    outline: 0;
}
QWidget { background: #1E1E1E; }
QMainWindow, QDialog { background: #1E1E1E; }
QToolTip {
    background: #2A2A2A;
    color: #E1E1E1;
    border: 1px solid #3A3A3A;
    border-radius: 6px;
    padding: 6px 10px;
}

/* ─── splitter ────────────────────────────────────────────────── */
QSplitter::handle { background: #2A2A2A; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical   { height: 1px; }
QSplitter::handle:hover { background: #FF6C37; }

/* ─── sidebar ─────────────────────────────────────────────────── */
#sidebar {
    background: #212121;
    border-right: 1px solid #2E2E2E;
}
#brandWrap {
    background: transparent;
}
QToolButton#langButton {
    background: #2A2A2A;
    border: 1px solid #3A3A3A;
    border-radius: 14px;
    padding: 4px 10px;
    color: #E1E1E1;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    min-height: 22px;
}
QToolButton#langButton:hover {
    background: #303030;
    border-color: #FF6C37;
    color: #FFFFFF;
}
QToolButton#langButton::menu-indicator { width: 0; height: 0; image: none; }

QPushButton#curlButton {
    background: rgba(255, 108, 55, 0.10);
    color: #FF8557;
    border: 1px solid rgba(255, 108, 55, 0.32);
    border-radius: 14px;
    padding: 4px 12px;
    font-family: "JetBrains Mono", "Consolas", "Courier New";
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    min-height: 22px;
}
QPushButton#curlButton:hover {
    background: rgba(255, 108, 55, 0.22);
    border-color: #FF6C37;
    color: #FFFFFF;
}
QPushButton#curlButton:pressed { background: rgba(255, 108, 55, 0.32); }

QPushButton#clearHistoryButton {
    background: transparent;
    color: #A0A0A0;
    border: 1px solid #2E2E2E;
    border-radius: 12px;
    padding: 3px 12px;
    font-size: 11px;
    font-weight: 600;
    min-height: 20px;
}
QPushButton#clearHistoryButton:hover {
    background: rgba(244, 91, 105, 0.10);
    border-color: rgba(244, 91, 105, 0.40);
    color: #F45B69;
}
QPushButton#clearHistoryButton:pressed {
    background: rgba(244, 91, 105, 0.18);
}

#sidebarTabBar QPushButton {
    background: transparent;
    color: #A0A0A0;
    border: none;
    padding: 8px 14px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
    min-height: 22px;
}
#sidebarTabBar QPushButton:hover { color: #FFFFFF; }
#sidebarTabBar QPushButton:checked {
    background: rgba(255, 108, 55, 0.14);
    color: #FFFFFF;
}

QTreeWidget#collectionsTree,
QListWidget#historyList {
    background: transparent;
    border: none;
    outline: 0;
    padding: 6px 8px;
    font-size: 12.5px;
    show-decoration-selected: 1;
}
QTreeWidget#collectionsTree::item,
QListWidget#historyList::item {
    min-height: 30px;
    padding: 6px 10px;
    color: #C7C7C7;
    border-radius: 6px;
    border: 0;
    margin: 1px 0;
}
QTreeWidget#collectionsTree::item:hover,
QListWidget#historyList::item:hover {
    background: #2A2A2A;
    color: #FFFFFF;
}
QTreeWidget#collectionsTree::item:selected,
QListWidget#historyList::item:selected {
    background: #3A3A3A;
    color: #FFFFFF;
}
QTreeWidget#collectionsTree::branch { background: transparent; }
QTreeWidget#collectionsTree::branch:hover { background: transparent; }
QTreeWidget#collectionsTree::branch:selected { background: transparent; }

/* ─── topbar (URL row) ────────────────────────────────────────── */
#topBar {
    background: #212121;
    border-bottom: 1px solid #2E2E2E;
}
#urlBar {
    background: #2A2A2A;
    border: 1px solid #2E2E2E;
    border-radius: 6px;
    padding: 0 14px;
    min-height: 40px;
    font-size: 13px;
    color: #E1E1E1;
    selection-background-color: #FF6C37;
}
#urlBar:focus  { border: 1px solid #FF6C37; background: #303030; }
#urlBar:hover  { border: 1px solid #3A3A3A; }

#methodCombo {
    background: #2A2A2A;
    border: 1px solid #2E2E2E;
    border-radius: 6px;
    min-height: 40px;
    padding: 0 16px;
    font-weight: 800;
    font-size: 12px;
    letter-spacing: 1px;
    color: #FFB400;
}
#methodCombo:hover  { border: 1px solid #FF6C37; background: #303030; }
#methodCombo:focus  { border: 1px solid #FF6C37; }
#methodCombo::drop-down { border: none; width: 22px; }
#methodCombo QAbstractItemView {
    background: #2A2A2A;
    border: 1px solid #3A3A3A;
    border-radius: 6px;
    color: #E1E1E1;
    selection-background-color: #FF6C37;
    selection-color: white;
    padding: 6px;
    outline: 0;
}
#methodCombo QAbstractItemView::item {
    min-height: 28px;
    padding: 4px 12px;
    border-radius: 5px;
    font-weight: 700;
}

/* ─── buttons ─────────────────────────────────────────────────── */
#primaryButton {
    background: #FF6C37;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0 24px;
    font-weight: 700;
    font-size: 13px;
    min-height: 40px;
}
#primaryButton:hover  { background: #FF8557; }
#primaryButton:pressed { background: #E55A2B; }
#primaryButton:disabled {
    background: #3A3A3A;
    color: #6B6B6B;
}

#ghostButton {
    background: transparent;
    color: #E1E1E1;
    border: 1px solid #3A3A3A;
    border-radius: 6px;
    padding: 0 16px;
    font-size: 12px;
    font-weight: 600;
    min-height: 36px;
}
#ghostButton:hover {
    background: #2A2A2A;
    border-color: #FF6C37;
    color: #FFFFFF;
}
#ghostButton:pressed { background: #303030; }

#iconButton {
    background: transparent;
    border: none;
    border-radius: 6px;
    color: #A0A0A0;
    font-size: 14px;
    padding: 6px;
    min-width: 28px;
    min-height: 28px;
}
#iconButton:hover { background: #2A2A2A; color: #FFFFFF; }
#iconButton:pressed { background: #303030; }

/* ─── tabs ────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: none;
    background: #1E1E1E;
    top: 0px;
}
QTabBar {
    background: transparent;
    qproperty-drawBase: 0;
    border-bottom: 1px solid #2E2E2E;
}
QTabBar::tab {
    background: transparent;
    color: #A0A0A0;
    padding: 11px 20px;
    border: none;
    border-bottom: 2px solid transparent;
    margin: 0 2px 0 0;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.3px;
    min-width: 70px;
}
QTabBar::tab:hover { color: #E1E1E1; }
QTabBar::tab:selected {
    color: #FFFFFF;
    border-bottom: 2px solid #FF6C37;
}

/* ─── tables ──────────────────────────────────────────────────── */
QTableWidget#kvTable {
    background: transparent;
    border: none;
    gridline-color: transparent;
    font-size: 12.5px;
}
QTableWidget#kvTable::item {
    background: transparent;
    border: none;
    padding: 8px 12px;
    color: #C7C7C7;
}
QTableWidget#kvTable::item:hover { background: rgba(255, 255, 255, 0.025); }
QTableWidget#kvTable::item:selected {
    background: rgba(255, 108, 55, 0.10);
    color: #FFFFFF;
}
QTableWidget#kvTable::item:focus {
    background: rgba(255, 108, 55, 0.18);
    color: #FFFFFF;
}

QHeaderView::section {
    background: #212121;
    color: #A0A0A0;
    border: none;
    border-bottom: 1px solid #2E2E2E;
    padding: 12px 14px;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.8px;
}

/* ─── code editors ────────────────────────────────────────────── */
QPlainTextEdit, QTextEdit {
    background: #1A1A1A;
    border: 1px solid #2E2E2E;
    border-radius: 6px;
    padding: 12px;
    selection-background-color: #FF6C37;
    font-family: "JetBrains Mono", "Cascadia Code", "Consolas", "Courier New";
    font-size: 12.5px;
    color: #E1E1E1;
}
QPlainTextEdit:hover, QTextEdit:hover { border: 1px solid #3A3A3A; }
QPlainTextEdit:focus, QTextEdit:focus { border: 1px solid #FF6C37; }

/* ─── line edits / combos ─────────────────────────────────────── */
QLineEdit {
    background: #2A2A2A;
    border: 1px solid #2E2E2E;
    border-radius: 6px;
    padding: 9px 12px;
    color: #E1E1E1;
    min-height: 20px;
    font-size: 12.5px;
    selection-background-color: #FF6C37;
}
QLineEdit:hover { border: 1px solid #3A3A3A; }
QLineEdit:focus { border: 1px solid #FF6C37; background: #303030; }

QComboBox {
    background: #2A2A2A;
    border: 1px solid #2E2E2E;
    border-radius: 6px;
    padding: 7px 12px;
    color: #E1E1E1;
    min-height: 22px;
}
QComboBox:hover { border: 1px solid #3A3A3A; }
QComboBox:focus { border: 1px solid #FF6C37; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background: #2A2A2A;
    border: 1px solid #3A3A3A;
    border-radius: 6px;
    color: #E1E1E1;
    selection-background-color: #FF6C37;
    selection-color: white;
    padding: 6px;
    outline: 0;
}
QComboBox QAbstractItemView::item { min-height: 28px; padding: 4px 12px; border-radius: 5px; }

/* ─── checkboxes ──────────────────────────────────────────────── */
QCheckBox {
    color: #C7C7C7;
    spacing: 8px;
    background: transparent;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #3A3A3A;
    border-radius: 4px;
    background: #2A2A2A;
}
QCheckBox::indicator:hover {
    border: 1px solid #FF6C37;
    background: #303030;
}
QCheckBox::indicator:checked {
    background: #FF6C37;
    border: 1px solid #FF6C37;
    image: none;
}
QCheckBox::indicator:checked:hover {
    background: #FF8557;
    border: 1px solid #FF8557;
}

/* ─── scrollbars ──────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 12px;
    margin: 4px 2px;
}
QScrollBar::handle:vertical {
    background: #3A3A3A;
    border-radius: 4px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover { background: #4A4A4A; }
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
    background: #3A3A3A;
    border-radius: 4px;
    min-width: 28px;
}
QScrollBar::handle:horizontal:hover { background: #4A4A4A; }
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal { background: none; }

/* ─── menu / status / titlebar ────────────────────────────────── */
QMenuBar {
    background: #212121;
    color: #C7C7C7;
    border-bottom: 1px solid #2E2E2E;
    padding: 4px 8px;
    min-height: 30px;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 6px;
    margin: 2px;
}
QMenuBar::item:selected { background: #2A2A2A; color: #FFFFFF; }
QMenuBar::item:pressed  { background: #303030; }

QMenu {
    background: #2A2A2A;
    border: 1px solid #3A3A3A;
    padding: 6px;
    border-radius: 8px;
    color: #E1E1E1;
}
QMenu::item {
    padding: 8px 24px 8px 14px;
    border-radius: 5px;
    margin: 1px;
}
QMenu::item:selected { background: #FF6C37; color: white; }
QMenu::separator {
    height: 1px;
    background: #3A3A3A;
    margin: 4px 8px;
}

QStatusBar {
    background: #212121;
    color: #A0A0A0;
    border-top: 1px solid #2E2E2E;
    padding: 0 8px;
    min-height: 26px;
}
QStatusBar::item { border: none; }

/* ─── labels ──────────────────────────────────────────────────── */
QLabel { background: transparent; }

/* ─── confirm-delete dialog (frameless card) ──────────────────── */
QFrame#confirmCard {
    background: #2A2A2A;
    border: none;
    border-radius: 14px;
}
QPushButton#confirmCancel {
    background: rgba(255, 255, 255, 0.04);
    color: #E1E1E1;
    border: none;
    border-radius: 8px;
    padding: 0 20px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton#confirmCancel:hover  { background: rgba(255, 255, 255, 0.08); color: #FFFFFF; }
QPushButton#confirmCancel:pressed { background: rgba(255, 255, 255, 0.12); }

QPushButton#confirmDanger {
    background: #F45B69;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 0 20px;
    font-weight: 700;
    font-size: 13px;
}
QPushButton#confirmDanger:hover  { background: #F77785; }
QPushButton#confirmDanger:pressed { background: #DC4555; }

/* ─── console drawer ──────────────────────────────────────────── */
#consolePanel {
    background: #1A1A1A;
    border-top: 1px solid #2E2E2E;
}
#consoleHeader {
    background: #212121;
    border-bottom: 1px solid #2E2E2E;
}
#consoleTitle {
    color: #FF8557;
    font-family: "JetBrains Mono", "Consolas";
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.8px;
}
#consoleCounter {
    color: #A0A0A0;
    background: rgba(255, 255, 255, 0.04);
    border-radius: 8px;
    padding: 1px 8px;
    font-size: 11px;
    font-weight: 700;
}
QTableWidget#consoleTable {
    background: #1A1A1A;
    border: none;
    gridline-color: transparent;
    font-size: 12px;
}
QTableWidget#consoleTable::item {
    background: transparent;
    border: none;
    padding: 4px 10px;
}
QTableWidget#consoleTable::item:hover  { background: #2A2A2A; }
QTableWidget#consoleTable::item:selected {
    background: #3A3A3A;
    color: #FFFFFF;
}

/* ─── status-codes dialog ─────────────────────────────────────── */
QScrollArea#statusScroll { background: transparent; border: none; }
"""
