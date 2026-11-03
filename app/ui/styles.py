"""Postaz theme — a refreshed, modern dark palette.

A deeper, cooler, layered background scale gives the UI real depth; larger
corner radii, roomier padding and a gradient call-to-action modernise the
feel. Object names are unchanged so every widget keeps its styling.

Brand colour     : #FF6C37  (orange — CTAs, focus rings, accents)
Brand hover      : #FF8557
Brand pressed    : #E55A2B

Background scale : #121318 (deepest, code editors)
                   #16171C (main canvas)
                   #1B1C22 (chrome / topbar / sidebar / status)
                   #22242B (popovers, inputs)
                   #2B2D35 (hover surface)
                   #34363F (active / selected surface)

Text scale       : #FFFFFF (selected / heading)
                   #E7E8EC (body)
                   #C4C6CE (secondary)
                   #9A9CA6 (label / muted)
                   #63656F (placeholder / disabled)

Border scale     : #26272E (default)
                   #34363F (hover / divider)

Status colors    : 2xx #5FD38A  ·  3xx #5BAEF5  ·  4xx #FFC24D  ·  5xx #FF6B78
Method colors    : GET #5FD38A · POST #FFC24D · PUT #5BAEF5 · PATCH #C792EA ·
                   DELETE #FF6B78 · HEAD/OPTIONS #80CBC4
"""


DARK = """
/* ─── globals ─────────────────────────────────────────────────── */
* {
    font-family: "Inter", "Segoe UI", "SF Pro Text", Arial;
    color: #E7E8EC;
    outline: 0;
}
QWidget { background: #16171C; }
QMainWindow, QDialog { background: #16171C; }
QToolTip {
    background: #22242B;
    color: #E7E8EC;
    border: 1px solid #34363F;
    border-radius: 8px;
    padding: 7px 11px;
}

/* ─── splitter ────────────────────────────────────────────────── */
QSplitter::handle { background: #16171C; }
QSplitter::handle:horizontal { width: 2px; }
QSplitter::handle:vertical   { height: 2px; }
QSplitter::handle:hover { background: #FF6C37; }

/* ─── sidebar ─────────────────────────────────────────────────── */
#sidebar {
    background: #1B1C22;
    border-right: 1px solid #26272E;
}
#brandWrap {
    background: transparent;
}
QToolButton#langButton {
    background: #22242B;
    border: 1px solid #34363F;
    border-radius: 15px;
    padding: 5px 12px;
    color: #E7E8EC;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    min-height: 22px;
}
QToolButton#langButton:hover {
    background: #2B2D35;
    border-color: #FF6C37;
    color: #FFFFFF;
}
QToolButton#langButton::menu-indicator { width: 0; height: 0; image: none; }

QPushButton#curlButton {
    background: rgba(255, 108, 55, 0.12);
    color: #FF8557;
    border: 1px solid rgba(255, 108, 55, 0.34);
    border-radius: 15px;
    padding: 5px 14px;
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
    color: #9A9CA6;
    border: 1px solid #26272E;
    border-radius: 13px;
    padding: 4px 14px;
    font-size: 11px;
    font-weight: 600;
    min-height: 20px;
}
QPushButton#clearHistoryButton:hover {
    background: rgba(255, 107, 120, 0.12);
    border-color: rgba(255, 107, 120, 0.42);
    color: #FF6B78;
}
QPushButton#clearHistoryButton:pressed {
    background: rgba(255, 107, 120, 0.20);
}

#sidebarTabBar QPushButton {
    background: transparent;
    color: #9A9CA6;
    border: none;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 11.5px;
    font-weight: 600;
    min-height: 22px;
}
#sidebarTabBar QPushButton:hover { color: #FFFFFF; background: #22242B; }
#sidebarTabBar QPushButton:checked {
    background: rgba(255, 108, 55, 0.16);
    color: #FF8557;
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
    min-height: 32px;
    padding: 7px 11px;
    color: #C4C6CE;
    border-radius: 8px;
    border: 0;
    margin: 1px 0;
}
QTreeWidget#collectionsTree::item:hover,
QListWidget#historyList::item:hover {
    background: #22242B;
    color: #FFFFFF;
}
QTreeWidget#collectionsTree::item:selected,
QListWidget#historyList::item:selected {
    background: rgba(255, 108, 55, 0.16);
    color: #FFFFFF;
}
QTreeWidget#collectionsTree::branch { background: transparent; }
QTreeWidget#collectionsTree::branch:hover { background: transparent; }
QTreeWidget#collectionsTree::branch:selected { background: transparent; }

/* ─── topbar (URL row) ────────────────────────────────────────── */
#topBar {
    background: #1B1C22;
    border-bottom: 1px solid #26272E;
}
#urlBar {
    background: #22242B;
    border: 1px solid #26272E;
    border-radius: 9px;
    padding: 0 15px;
    min-height: 42px;
    font-size: 13px;
    color: #E7E8EC;
    selection-background-color: #FF6C37;
}
#urlBar:focus  { border: 1px solid #FF6C37; background: #2B2D35; }
#urlBar:hover  { border: 1px solid #34363F; }

#methodCombo {
    background: #22242B;
    border: 1px solid #26272E;
    border-radius: 9px;
    min-height: 42px;
    padding: 0 16px;
    font-weight: 800;
    font-size: 12px;
    letter-spacing: 1px;
    color: #FFC24D;
}
#methodCombo:hover  { border: 1px solid #FF6C37; background: #2B2D35; }
#methodCombo:focus  { border: 1px solid #FF6C37; }
#methodCombo::drop-down { border: none; width: 22px; }
#methodCombo QAbstractItemView {
    background: #22242B;
    border: 1px solid #34363F;
    border-radius: 9px;
    color: #E7E8EC;
    selection-background-color: #FF6C37;
    selection-color: white;
    padding: 6px;
    outline: 0;
}
#methodCombo QAbstractItemView::item {
    min-height: 30px;
    padding: 4px 12px;
    border-radius: 7px;
    font-weight: 700;
}

/* ─── buttons ─────────────────────────────────────────────────── */
#primaryButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FF8557, stop:1 #FF6C37);
    color: white;
    border: none;
    border-radius: 9px;
    padding: 0 26px;
    font-weight: 700;
    font-size: 13px;
    min-height: 42px;
}
#primaryButton:hover  {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FF9A73, stop:1 #FF7A45);
}
#primaryButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #F06A3C, stop:1 #E55A2B);
}
#primaryButton:disabled {
    background: #2B2D35;
    color: #63656F;
}

#ghostButton {
    background: transparent;
    color: #E7E8EC;
    border: 1px solid #34363F;
    border-radius: 9px;
    padding: 0 18px;
    font-size: 12px;
    font-weight: 600;
    min-height: 38px;
}
#ghostButton:hover {
    background: #22242B;
    border-color: #FF6C37;
    color: #FFFFFF;
}
#ghostButton:pressed { background: #2B2D35; }

#iconButton {
    background: transparent;
    border: none;
    border-radius: 8px;
    color: #9A9CA6;
    font-size: 14px;
    padding: 6px;
    min-width: 30px;
    min-height: 30px;
}
#iconButton:hover { background: #22242B; color: #FFFFFF; }
#iconButton:pressed { background: #2B2D35; }

/* ─── tabs ────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: none;
    background: #16171C;
    top: 0px;
}
QTabBar {
    background: transparent;
    qproperty-drawBase: 0;
    border-bottom: 1px solid #26272E;
}
QTabBar::tab {
    background: transparent;
    color: #9A9CA6;
    padding: 11px 18px;
    border: none;
    border-bottom: 2px solid transparent;
    margin: 0 4px 0 0;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.3px;
    min-width: 66px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}
QTabBar::tab:hover { color: #E7E8EC; background: #1B1C22; }
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
    color: #C4C6CE;
}
QTableWidget#kvTable::item:hover { background: rgba(255, 255, 255, 0.03); }
QTableWidget#kvTable::item:selected {
    background: rgba(255, 108, 55, 0.12);
    color: #FFFFFF;
}
QTableWidget#kvTable::item:focus {
    background: rgba(255, 108, 55, 0.20);
    color: #FFFFFF;
}

QHeaderView::section {
    background: #1B1C22;
    color: #9A9CA6;
    border: none;
    border-bottom: 1px solid #26272E;
    padding: 12px 14px;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.8px;
}

/* ─── code editors ────────────────────────────────────────────── */
QPlainTextEdit, QTextEdit {
    background: #121318;
    border: 1px solid #26272E;
    border-radius: 9px;
    padding: 12px;
    selection-background-color: #FF6C37;
    font-family: "JetBrains Mono", "Cascadia Code", "Consolas", "Courier New";
    font-size: 12.5px;
    color: #E7E8EC;
}
QPlainTextEdit:hover, QTextEdit:hover { border: 1px solid #34363F; }
QPlainTextEdit:focus, QTextEdit:focus { border: 1px solid #FF6C37; }

/* ─── line edits / combos ─────────────────────────────────────── */
QLineEdit {
    background: #22242B;
    border: 1px solid #26272E;
    border-radius: 9px;
    padding: 9px 13px;
    color: #E7E8EC;
    min-height: 20px;
    font-size: 12.5px;
    selection-background-color: #FF6C37;
}
QLineEdit:hover { border: 1px solid #34363F; }
QLineEdit:focus { border: 1px solid #FF6C37; background: #2B2D35; }

QComboBox {
    background: #22242B;
    border: 1px solid #26272E;
    border-radius: 9px;
    padding: 7px 13px;
    color: #E7E8EC;
    min-height: 22px;
}
QComboBox:hover { border: 1px solid #34363F; }
QComboBox:focus { border: 1px solid #FF6C37; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background: #22242B;
    border: 1px solid #34363F;
    border-radius: 9px;
    color: #E7E8EC;
    selection-background-color: #FF6C37;
    selection-color: white;
    padding: 6px;
    outline: 0;
}
QComboBox QAbstractItemView::item { min-height: 30px; padding: 4px 12px; border-radius: 7px; }

/* ─── checkboxes ──────────────────────────────────────────────── */
QCheckBox {
    color: #C4C6CE;
    spacing: 8px;
    background: transparent;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #34363F;
    border-radius: 5px;
    background: #22242B;
}
QCheckBox::indicator:hover {
    border: 1px solid #FF6C37;
    background: #2B2D35;
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
    width: 10px;
    margin: 4px 2px;
}
QScrollBar::handle:vertical {
    background: #34363F;
    border-radius: 5px;
    min-height: 32px;
}
QScrollBar::handle:vertical:hover { background: #45474F; }
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical { background: none; }

QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px 4px;
}
QScrollBar::handle:horizontal {
    background: #34363F;
    border-radius: 5px;
    min-width: 32px;
}
QScrollBar::handle:horizontal:hover { background: #45474F; }
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal { background: none; }

/* ─── menu / status / titlebar ────────────────────────────────── */
QMenuBar {
    background: #1B1C22;
    color: #C4C6CE;
    border-bottom: 1px solid #26272E;
    padding: 4px 8px;
    min-height: 30px;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 8px;
    margin: 2px;
}
QMenuBar::item:selected { background: #22242B; color: #FFFFFF; }
QMenuBar::item:pressed  { background: #2B2D35; }

QMenu {
    background: #22242B;
    border: 1px solid #34363F;
    padding: 6px;
    border-radius: 10px;
    color: #E7E8EC;
}
QMenu::item {
    padding: 8px 24px 8px 14px;
    border-radius: 7px;
    margin: 1px;
}
QMenu::item:selected { background: #FF6C37; color: white; }
QMenu::separator {
    height: 1px;
    background: #34363F;
    margin: 4px 8px;
}

QStatusBar {
    background: #1B1C22;
    color: #9A9CA6;
    border-top: 1px solid #26272E;
    padding: 0 8px;
    min-height: 28px;
}
QStatusBar::item { border: none; }

/* ─── labels ──────────────────────────────────────────────────── */
QLabel { background: transparent; }

/* ─── confirm-delete dialog (frameless card) ──────────────────── */
QFrame#confirmCard {
    background: #22242B;
    border: 1px solid #34363F;
    border-radius: 16px;
}
QPushButton#confirmCancel {
    background: rgba(255, 255, 255, 0.05);
    color: #E7E8EC;
    border: none;
    border-radius: 9px;
    padding: 0 20px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton#confirmCancel:hover  { background: rgba(255, 255, 255, 0.09); color: #FFFFFF; }
QPushButton#confirmCancel:pressed { background: rgba(255, 255, 255, 0.13); }

QPushButton#confirmDanger {
    background: #FF6B78;
    color: #FFFFFF;
    border: none;
    border-radius: 9px;
    padding: 0 20px;
    font-weight: 700;
    font-size: 13px;
}
QPushButton#confirmDanger:hover  { background: #FF8591; }
QPushButton#confirmDanger:pressed { background: #E8505E; }

/* ─── console drawer ──────────────────────────────────────────── */
#consolePanel {
    background: #121318;
    border-top: 1px solid #26272E;
}
#consoleHeader {
    background: #1B1C22;
    border-bottom: 1px solid #26272E;
}
#consoleTitle {
    color: #FF8557;
    font-family: "JetBrains Mono", "Consolas";
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.8px;
}
#consoleCounter {
    color: #9A9CA6;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 9px;
    padding: 1px 9px;
    font-size: 11px;
    font-weight: 700;
}
QTableWidget#consoleTable {
    background: #121318;
    border: none;
    gridline-color: transparent;
    font-size: 12px;
}
QTableWidget#consoleTable::item {
    background: transparent;
    border: none;
    padding: 4px 10px;
}
QTableWidget#consoleTable::item:hover  { background: #22242B; }
QTableWidget#consoleTable::item:selected {
    background: #34363F;
    color: #FFFFFF;
}

/* ─── status-codes dialog ─────────────────────────────────────── */
QScrollArea#statusScroll { background: transparent; border: none; }

/* ─── status-bar Console pill ─────────────────────────────────── */
QPushButton#statusConsoleButton {
    background: transparent;
    color: #9A9CA6;
    border: none;
    border-radius: 7px;
    padding: 3px 13px;
    font-family: "JetBrains Mono", "Consolas";
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.6px;
}
QPushButton#statusConsoleButton:hover {
    background: #22242B;
    color: #FFFFFF;
}
QPushButton#statusConsoleButton:checked {
    background: rgba(255, 108, 55, 0.18);
    color: #FF8557;
}
QPushButton#statusConsoleButton:checked:hover {
    background: rgba(255, 108, 55, 0.28);
}
"""
