"""Dialogs: Save Request, Environments, About."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDesktopServices, QFont, QPixmap
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
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
from ..i18n import t
from .icons import app_icon, icon_plus, icon_trash
from .widgets import GhostButton, PrimaryButton


GITHUB_URL = "https://github.com/goshgarhasanov/postaz_api_tester"
COFFEE_URL = "https://kofe.al/goshgarhasanov"
DEV_NAME = "goshgarhasanov"
APP_VERSION = "1.0.0"


# ── Save Request ──────────────────────────────────────────────────────────
class SaveRequestDialog(QDialog):
    def __init__(self, db: Database, default_name: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle(t("Save Request"))
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        title = QLabel(t("Save Request"))
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setVerticalSpacing(10)

        self.name = QLineEdit(default_name)
        self.name.selectAll()
        form.addRow(t("Name"), self.name)

        self.collection = QComboBox()
        self.collection.addItem(t("Quick Saves"), None)
        for c in db.list_collections():
            self.collection.addItem(c.name, c.id)
        form.addRow(t("Collection"), self.collection)
        layout.addLayout(form)

        new_row = QHBoxLayout()
        self.new_col_name = QLineEdit()
        self.new_col_name.setPlaceholderText(t("Or create new collection…"))
        new_btn = GhostButton(t("Create"))
        new_btn.clicked.connect(self._create_collection)
        new_row.addWidget(self.new_col_name)
        new_row.addWidget(new_btn)
        layout.addLayout(new_row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = GhostButton(t("Cancel"))
        cancel.clicked.connect(self.reject)
        save = PrimaryButton(t("Save"))
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
            self.name.text().strip() or t("Untitled request"),
            self.collection.currentData(),
        )


# ── Environments ──────────────────────────────────────────────────────────
class EnvironmentDialog(QDialog):
    changed = Signal()

    def __init__(self, db: Database, parent: QWidget | None = None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle(t("Environments"))
        self.setMinimumSize(680, 440)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(22, 22, 22, 22)
        outer.setSpacing(16)

        # left
        left = QVBoxLayout()
        left.setSpacing(8)
        left.addWidget(QLabel(t("Environments")))
        self.list = QListWidget()
        self.list.setFixedWidth(190)
        self.list.currentItemChanged.connect(self._on_select)
        left.addWidget(self.list)
        row = QHBoxLayout()
        btn_new = GhostButton(t("New"))
        btn_new.setIcon(icon_plus("#c9cce0"))
        btn_del = GhostButton(t("Delete"))
        btn_del.setIcon(icon_trash("#c9cce0"))
        btn_new.clicked.connect(self._new_env)
        btn_del.clicked.connect(self._delete_env)
        row.addWidget(btn_new)
        row.addWidget(btn_del)
        left.addLayout(row)
        outer.addLayout(left)

        # right
        right = QVBoxLayout()
        right.setSpacing(10)
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel(t("Name") + ":"))
        self.name_edit = QLineEdit()
        self.name_edit.editingFinished.connect(self._persist_current)
        name_row.addWidget(self.name_edit)
        right.addLayout(name_row)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels([t("Variable"), t("Value")])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.itemChanged.connect(self._on_table_change)
        right.addWidget(self.table, 1)

        self.activate_btn = GhostButton(t("Set as active"))
        self.activate_btn.clicked.connect(self._activate)
        bottom = QHBoxLayout()
        bottom.addWidget(self.activate_btn)
        bottom.addStretch()
        close = PrimaryButton(t("Done"))
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
        return it.data(Qt.UserRole) if it else None

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
        item = self.list.currentItem()
        env["name"] = name
        env["variables"] = self._collect_vars()
        item.setData(Qt.UserRole, env)
        item.setText(("● " if env["is_active"] else "  ") + name)
        self.changed.emit()

    def _new_env(self) -> None:
        name, ok = QInputDialog.getText(self, t("New environment"), t("Name") + ":")
        if ok and name.strip():
            self.db.create_environment(name.strip(), {})
            self._reload()
            self.changed.emit()

    def _delete_env(self) -> None:
        env = self._current_env()
        if not env:
            return
        r = QMessageBox.question(
            self,
            t("Delete"),
            t("Delete environment '{name}'?", name=env["name"]),
            QMessageBox.Yes | QMessageBox.No,
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


# ── About ─────────────────────────────────────────────────────────────────
_ABOUT_BODY = {
    "en": """\
<p style="color:#a4a7c2; font-size:13px; line-height:1.55;">
<b>Postaz</b> is a lightweight, beautiful and fully-offline HTTP API client
built for developers who want the power of Postman without the bloat,
the sign-up wall, or the cloud sync.
</p>
<p style="color:#a4a7c2; font-size:13px; line-height:1.55;">
Every request, every collection, every environment lives on <b>your</b> machine —
in a single SQLite file. No telemetry, no accounts, no friction.
Crafted with Python, PySide6 and a deep love for clean UI.
</p>""",
    "az": """\
<p style="color:#a4a7c2; font-size:13px; line-height:1.55;">
<b>Postaz</b> — yüngül, gözəl və tamamilə oflayn işləyən HTTP API müştərisidir.
Postman-ın gücünü artıq lazımsız əlavələrsiz, qeydiyyat tələbi olmadan və
bulud sinxronizasiyası olmadan istəyən developer-lər üçün hazırlanıb.
</p>
<p style="color:#a4a7c2; font-size:13px; line-height:1.55;">
Bütün sorğular, kolleksiyalar və mühitlər <b>sizin</b> kompüterinizdə —
bir SQLite faylında yaşayır. Heç bir telemetriya, hesab, problem yoxdur.
Python, PySide6 ilə və təmiz interfeysə olan sevgi ilə hazırlanıb.
</p>""",
    "tr": """\
<p style="color:#a4a7c2; font-size:13px; line-height:1.55;">
<b>Postaz</b>, hafif, şık ve tamamen çevrimdışı çalışan bir HTTP API istemcisidir.
Postman'in gücünü gereksiz şişkinlikler, kayıt zorunluluğu ve bulut senkronu
olmadan isteyen geliştiriciler için tasarlandı.
</p>
<p style="color:#a4a7c2; font-size:13px; line-height:1.55;">
Tüm istekler, koleksiyonlar ve ortamlar <b>sizin</b> bilgisayarınızda —
tek bir SQLite dosyasında yaşar. Telemetri yok, hesap yok, sürtünme yok.
Python, PySide6 ve temiz arayüze duyulan sevgi ile hazırlandı.
</p>""",
}

_FEATURE_TITLE = {"en": "What's inside", "az": "Daxilində nə var", "tr": "İçinde neler var"}
_FEATURES = {
    "en": [
        "All HTTP methods · query params · headers · body editor",
        "Bearer, Basic, API-Key authentication presets",
        "Collections, history (last 200 calls), environments with {{vars}}",
        "Dark and light themes · 3 languages (EN/AZ/TR)",
        "JSON syntax highlighting · threaded HTTP · zero blocking",
        "Single SQLite file · zero telemetry · fully offline",
    ],
    "az": [
        "Bütün HTTP metodları · sorğu parametrləri · başlıqlar · gövdə redaktoru",
        "Bearer, Basic, API-Key doğrulama tipləri",
        "Kolleksiyalar, tarixçə (son 200 sorğu), {{dəyişənlər}} ilə mühitlər",
        "Tünd və açıq mövzular · 3 dil (EN/AZ/TR)",
        "JSON sintaksis vurğulanması · paralel HTTP · interfeys donmur",
        "Tək SQLite faylı · sıfır telemetriya · tam oflayn",
    ],
    "tr": [
        "Tüm HTTP metodları · sorgu parametreleri · başlıklar · gövde editörü",
        "Bearer, Basic, API-Key kimlik doğrulama ön ayarları",
        "Koleksiyonlar, geçmiş (son 200 istek), {{değişken}} destekli ortamlar",
        "Koyu ve açık temalar · 3 dil (EN/AZ/TR)",
        "JSON sözdizimi vurgulaması · iş parçacıklı HTTP · arayüz donmaz",
        "Tek SQLite dosyası · sıfır telemetri · tamamen çevrimdışı",
    ],
}
_DEVELOPED_BY = {"en": "Developed by", "az": "Hazırlayıb", "tr": "Geliştiren"}
_OPEN_GITHUB = {"en": "View on GitHub", "az": "GitHub-da bax", "tr": "GitHub'da görüntüle"}
_BUY_COFFEE = {"en": "Buy me a coffee ☕", "az": "Mənə bir qəhvə al ☕", "tr": "Bana bir kahve ısmarla ☕"}
_VERSION = {"en": "Version", "az": "Versiya", "tr": "Sürüm"}
_BUILT_WITH = {
    "en": "Built with Python · PySide6 · SQLite · requests",
    "az": "Python · PySide6 · SQLite · requests ilə qurulub",
    "tr": "Python · PySide6 · SQLite · requests ile geliştirildi",
}


class AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        from ..i18n import translator as _tr  # local import to avoid cycle
        lang = _tr.language
        self.setWindowTitle(t("About") + " — Postaz")
        self.setFixedSize(560, 620)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── header (gradient) ──────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet(
            "QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            "stop:0 #7c5cff, stop:1 #5a3fd9); }"
        )
        header.setFixedHeight(150)
        hl = QVBoxLayout(header)
        hl.setContentsMargins(28, 26, 28, 20)
        hl.setSpacing(6)

        # Big mark + wordmark
        head_row = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(app_icon(72).pixmap(72, 72))
        head_row.addWidget(icon_lbl)
        head_row.addSpacing(14)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        word = QLabel("POSTAZ")
        word.setStyleSheet(
            "color: white; font-size: 34px; font-weight: 900; letter-spacing: 2px;"
        )
        tag = QLabel(t("Local API Tester"))
        tag.setStyleSheet("color: rgba(255,255,255,0.78); font-size: 13px;")
        title_col.addWidget(word)
        title_col.addWidget(tag)
        head_row.addLayout(title_col)
        head_row.addStretch()
        hl.addLayout(head_row)
        outer.addWidget(header)

        # ── body ───────────────────────────────────────────────────────
        body = QFrame()
        body.setStyleSheet("background: #0f1019;")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(28, 22, 28, 22)
        bl.setSpacing(12)

        desc = QLabel(_ABOUT_BODY.get(lang, _ABOUT_BODY["en"]))
        desc.setTextFormat(Qt.RichText)
        desc.setWordWrap(True)
        bl.addWidget(desc)

        feat_title = QLabel(f"✦ {_FEATURE_TITLE.get(lang, _FEATURE_TITLE['en'])}")
        feat_title.setStyleSheet("color:#a89bff; font-weight:600; font-size:12px; letter-spacing:1px;")
        bl.addWidget(feat_title)

        feat_html = "<ul style='color:#c9cce0; font-size:12px; line-height:1.7; margin-left:-18px;'>"
        for f in _FEATURES.get(lang, _FEATURES["en"]):
            feat_html += f"<li>{f}</li>"
        feat_html += "</ul>"
        feat = QLabel(feat_html)
        feat.setTextFormat(Qt.RichText)
        feat.setWordWrap(True)
        bl.addWidget(feat)

        # spacer
        bl.addStretch()

        # developer line
        dev = QLabel(
            f"<span style='color:#8b8fab;'>{_DEVELOPED_BY.get(lang, _DEVELOPED_BY['en'])}</span> "
            f"<b style='color:#e6e8f5;'>{DEV_NAME}</b>"
        )
        dev.setTextFormat(Qt.RichText)
        dev.setAlignment(Qt.AlignCenter)
        bl.addWidget(dev)

        version = QLabel(
            f"<span style='color:#6b6f88; font-size:11px;'>"
            f"{_VERSION.get(lang, _VERSION['en'])} {APP_VERSION} · {_BUILT_WITH.get(lang, _BUILT_WITH['en'])}"
            f"</span>"
        )
        version.setTextFormat(Qt.RichText)
        version.setAlignment(Qt.AlignCenter)
        bl.addWidget(version)

        # buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        gh = GhostButton(_OPEN_GITHUB.get(lang, _OPEN_GITHUB["en"]))
        gh.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))
        coffee = PrimaryButton(_BUY_COFFEE.get(lang, _BUY_COFFEE["en"]))
        coffee.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(COFFEE_URL)))
        close = GhostButton(t("Done"))
        close.clicked.connect(self.accept)
        btn_row.addWidget(gh)
        btn_row.addStretch()
        btn_row.addWidget(coffee)
        btn_row.addWidget(close)
        bl.addLayout(btn_row)

        outer.addWidget(body, 1)
