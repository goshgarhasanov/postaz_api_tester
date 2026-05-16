"""HTTP status code reference dialog.

A searchable, colour-grouped list of every status code defined by RFC 9110
plus the few non-standard ones developers see in the wild. Opened from
Help → HTTP Status Codes (or Ctrl+/)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..i18n import translator
from .widgets import GhostButton


# ── reference data (RFC 9110 + a few common extras) ──────────────────────
# Format: code → (name, EN, AZ, TR)
STATUS_CODES: dict[int, tuple[str, dict[str, str]]] = {
    100: ("Continue",                         {"en": "The server has received the request headers and the client should proceed to send the request body.",
                                                "az": "Server sorğunun başlıqlarını alıb; müştəri gövdəni göndərməyə davam etməlidir.",
                                                "tr": "Sunucu istek başlıklarını aldı; istemci gövdeyi göndermeye devam etmeli."}),
    101: ("Switching Protocols",              {"en": "The server is switching protocols as requested (e.g. upgrading to WebSocket).",
                                                "az": "Server tələb edildiyi kimi protokolu dəyişir (məs. WebSocket-ə keçid).",
                                                "tr": "Sunucu istenen protokole geçiyor (örn. WebSocket'e yükseltme)."}),
    102: ("Processing",                       {"en": "Server has accepted the request but processing isn't yet complete.",
                                                "az": "Server sorğunu qəbul etdi, lakin emal hələ bitməyib.",
                                                "tr": "Sunucu isteği aldı ama işlem henüz tamamlanmadı."}),

    200: ("OK",                               {"en": "Standard successful response. Body contains the requested resource.",
                                                "az": "Standart uğurlu cavab. Gövdə tələb olunan resursu ehtiva edir.",
                                                "tr": "Standart başarılı yanıt. Gövde istenen kaynağı içerir."}),
    201: ("Created",                          {"en": "The request was successful and a new resource was created.",
                                                "az": "Sorğu uğurla yerinə yetirildi və yeni resurs yaradıldı.",
                                                "tr": "İstek başarılı oldu ve yeni bir kaynak oluşturuldu."}),
    202: ("Accepted",                         {"en": "The request has been accepted for processing, but processing isn't complete.",
                                                "az": "Sorğu emala qəbul edildi, lakin emal hələ bitməyib.",
                                                "tr": "İstek işleme alındı ama işlem tamamlanmadı."}),
    204: ("No Content",                       {"en": "Successful — but there is no body to return.",
                                                "az": "Uğurlu — qaytarılacaq gövdə yoxdur.",
                                                "tr": "Başarılı — döndürülecek gövde yok."}),
    206: ("Partial Content",                  {"en": "Successful response to a Range request.",
                                                "az": "Range sorğusuna uğurlu cavab.",
                                                "tr": "Range isteğine başarılı yanıt."}),

    301: ("Moved Permanently",                {"en": "The resource has moved to a new URL permanently — follow the Location header.",
                                                "az": "Resurs həmişəlik yeni URL-ə köçürülüb — Location başlığını izləyin.",
                                                "tr": "Kaynak kalıcı olarak yeni URL'e taşındı — Location başlığını izleyin."}),
    302: ("Found",                            {"en": "Temporary redirect — the client should fetch the resource at the new URL but keep using the original for future requests.",
                                                "az": "Müvəqqəti yönləndirmə — müştəri yeni URL-dən almalı, lakin gələcək sorğular üçün orijinalı saxlamalıdır.",
                                                "tr": "Geçici yönlendirme — istemci yeni URL'i çekmeli ama gelecekteki istekler için orijinali tutmalı."}),
    304: ("Not Modified",                     {"en": "The cached copy is still valid — server returns no body.",
                                                "az": "Önbəllək hələ etibarlıdır — server gövdə qaytarmır.",
                                                "tr": "Önbellek hâlâ geçerli — sunucu gövde döndürmez."}),
    307: ("Temporary Redirect",               {"en": "Like 302, but the request method must not change.",
                                                "az": "302 kimi, lakin sorğu metodu dəyişməməlidir.",
                                                "tr": "302 gibi, ama istek metodu değişmemeli."}),
    308: ("Permanent Redirect",               {"en": "Like 301, but the request method must not change.",
                                                "az": "301 kimi, lakin sorğu metodu dəyişməməlidir.",
                                                "tr": "301 gibi, ama istek metodu değişmemeli."}),

    400: ("Bad Request",                      {"en": "The request was malformed — the server couldn't understand it.",
                                                "az": "Sorğu səhv formatlıdır — server onu anlaya bilmədi.",
                                                "tr": "İstek hatalı biçimlendirildi — sunucu anlayamadı."}),
    401: ("Unauthorized",                     {"en": "Authentication is required and has failed or not yet been provided.",
                                                "az": "Doğrulama tələb olunur və o uğursuz olub və ya verilməyib.",
                                                "tr": "Kimlik doğrulama gerekli; başarısız oldu ya da sağlanmadı."}),
    403: ("Forbidden",                        {"en": "The server understood the request but refuses to authorise it.",
                                                "az": "Server sorğunu başa düşdü, lakin icazə verməkdən imtina edir.",
                                                "tr": "Sunucu isteği anladı ama yetkilendirmeyi reddediyor."}),
    404: ("Not Found",                        {"en": "The requested resource doesn't exist on the server.",
                                                "az": "Tələb olunan resurs serverdə mövcud deyil.",
                                                "tr": "İstenen kaynak sunucuda yok."}),
    405: ("Method Not Allowed",               {"en": "The HTTP method isn't supported for this URL.",
                                                "az": "Bu URL üçün HTTP metodu dəstəklənmir.",
                                                "tr": "Bu URL için HTTP metodu desteklenmiyor."}),
    408: ("Request Timeout",                  {"en": "The client took too long to send a complete request.",
                                                "az": "Müştəri tam sorğu göndərmək üçün çox uzun çəkdi.",
                                                "tr": "İstemci tam istek göndermek için çok uzun sürdü."}),
    409: ("Conflict",                         {"en": "The request conflicts with the current state of the resource.",
                                                "az": "Sorğu resursun cari vəziyyəti ilə ziddiyyət təşkil edir.",
                                                "tr": "İstek, kaynağın mevcut durumuyla çakışıyor."}),
    410: ("Gone",                             {"en": "The resource was here once but isn't anymore and won't come back.",
                                                "az": "Resurs bir vaxtlar burada idi, lakin artıq yoxdur və geri qayıtmayacaq.",
                                                "tr": "Kaynak bir zamanlar buradaydı ama artık yok ve geri gelmeyecek."}),
    413: ("Payload Too Large",                {"en": "The request body is larger than the server is willing to process.",
                                                "az": "Sorğu gövdəsi serverin emal edə biləcəyindən böyükdür.",
                                                "tr": "İstek gövdesi sunucunun işleyebileceğinden büyük."}),
    415: ("Unsupported Media Type",           {"en": "The Content-Type of the body isn't supported.",
                                                "az": "Gövdənin Content-Type dəyəri dəstəklənmir.",
                                                "tr": "Gövdenin Content-Type değeri desteklenmiyor."}),
    418: ("I'm a teapot",                     {"en": "RFC 2324 — short and stout. A joke status code that occasionally shows up in the wild.",
                                                "az": "RFC 2324 — qısa və kök. Vaxtaşırı görünən zarafat status kodu.",
                                                "tr": "RFC 2324 — kısa ve toplu. Zaman zaman ortaya çıkan şaka durum kodu."}),
    422: ("Unprocessable Entity",             {"en": "The body is syntactically correct but semantically wrong (e.g. validation failed).",
                                                "az": "Gövdə sintaktik cəhətdən doğrudur, lakin semantik cəhətdən səhvdir (məs. validasiya uğursuz oldu).",
                                                "tr": "Gövde sözdizimsel olarak doğru ama anlamsal olarak yanlış (örn. doğrulama başarısız)."}),
    429: ("Too Many Requests",                {"en": "Rate limit exceeded — slow down or back off.",
                                                "az": "Sürət limiti aşıldı — yavaşlayın və ya geri çəkilin.",
                                                "tr": "Hız limiti aşıldı — yavaşlayın veya geri çekilin."}),

    500: ("Internal Server Error",            {"en": "A generic catch-all server-side error. The server logs probably have details.",
                                                "az": "Ümumi server tərəfi xətası. Serverin loqları çox güman ki, detalları ehtiva edir.",
                                                "tr": "Genel sunucu tarafı hatası. Sunucu logları muhtemelen detayları içerir."}),
    501: ("Not Implemented",                  {"en": "The server doesn't know how to handle the request method.",
                                                "az": "Server sorğu metodunu necə emal edəcəyini bilmir.",
                                                "tr": "Sunucu istek metodunu nasıl işleyeceğini bilmiyor."}),
    502: ("Bad Gateway",                      {"en": "An upstream server (proxy / gateway) returned an invalid response.",
                                                "az": "Yuxarı server (proxy / şlüz) etibarsız cavab qaytardı.",
                                                "tr": "Yukarı akış sunucusu (proxy / ağ geçidi) geçersiz yanıt döndürdü."}),
    503: ("Service Unavailable",              {"en": "Server is temporarily overloaded or under maintenance.",
                                                "az": "Server müvəqqəti olaraq həddindən artıq yüklənib və ya texniki xidmətdədir.",
                                                "tr": "Sunucu geçici olarak aşırı yüklü veya bakımda."}),
    504: ("Gateway Timeout",                  {"en": "An upstream server didn't respond fast enough.",
                                                "az": "Yuxarı server kifayət qədər tez cavab vermədi.",
                                                "tr": "Yukarı akış sunucusu yeterince hızlı yanıt vermedi."}),
}


# Class buckets for grouping in the docs UI.
_CLASSES = [
    (1, "1xx — Informational", "#7c9eff", "#243245"),
    (2, "2xx — Success",       "#5ed29b", "#1e3a2f"),
    (3, "3xx — Redirection",   "#6fb8ff", "#243245"),
    (4, "4xx — Client Error",  "#f4b860", "#3d2f1c"),
    (5, "5xx — Server Error",  "#ff6e7c", "#3a1f24"),
]


class StatusCodesDialog(QDialog):
    """Modal reference with search + colour-grouped sections."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(self._tr_title())
        self.setMinimumSize(720, 680)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 22, 24, 20)
        outer.setSpacing(14)

        # heading
        head = QLabel(self._tr_title())
        head.setStyleSheet("font-size: 18px; font-weight: 700; color: #ffffff;")
        outer.addWidget(head)
        sub = QLabel(self._tr_sub())
        sub.setStyleSheet("color: #8b8fab; font-size: 12px;")
        sub.setWordWrap(True)
        outer.addWidget(sub)

        # search
        self.search = QLineEdit()
        self.search.setPlaceholderText(self._tr_search())
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._apply_filter)
        outer.addWidget(self.search)

        # scrollable content
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("statusScroll")
        self.scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        self.inner_layout = QVBoxLayout(inner)
        self.inner_layout.setContentsMargins(0, 0, 0, 0)
        self.inner_layout.setSpacing(20)

        self._rows: list[tuple[int, QWidget]] = []
        self._build_sections()
        self.inner_layout.addStretch()
        self.scroll.setWidget(inner)
        outer.addWidget(self.scroll, 1)

        # close button
        bar = QHBoxLayout()
        bar.addStretch()
        close = GhostButton(self._tr_close())
        close.clicked.connect(self.accept)
        bar.addWidget(close)
        outer.addLayout(bar)

    # ── translations ─────────────────────────────────────────────────
    def _tr_title(self) -> str:
        return {"en": "HTTP Status Codes",
                "az": "HTTP Status Kodları",
                "tr": "HTTP Durum Kodları"}[translator.language]

    def _tr_sub(self) -> str:
        return {"en": "A quick reference for every status code you'll see in the wild.",
                "az": "Real dünyada görəcəyiniz hər status kodu üçün sürətli bələdçi.",
                "tr": "Karşılaşacağınız her durum kodu için hızlı bir başvuru."}[translator.language]

    def _tr_search(self) -> str:
        return {"en": "Search by code or name…",
                "az": "Kod və ya ad ilə axtar…",
                "tr": "Kod veya adla ara…"}[translator.language]

    def _tr_close(self) -> str:
        return {"en": "Close", "az": "Bağla", "tr": "Kapat"}[translator.language]

    # ── build ────────────────────────────────────────────────────────
    def _build_sections(self) -> None:
        lang = translator.language
        for bucket, label, fg, bg in _CLASSES:
            section_label = QLabel(label)
            section_label.setStyleSheet(
                f"color: {fg}; font-size: 11px; font-weight: 800; letter-spacing: 1.2px;"
                "text-transform: uppercase; padding: 6px 0 2px 4px;"
            )
            section_label.setProperty("section", True)
            self.inner_layout.addWidget(section_label)
            self._rows.append((bucket, section_label))   # track for filter visibility

            for code, (name, descriptions) in sorted(STATUS_CODES.items()):
                if code // 100 != bucket:
                    continue
                row = self._make_row(code, name, descriptions.get(lang, descriptions["en"]), fg, bg)
                self.inner_layout.addWidget(row)
                self._rows.append((code, row))

    def _make_row(self, code: int, name: str, description: str, fg: str, bg: str) -> QFrame:
        row = QFrame()
        row.setObjectName("statusCodeRow")
        row.setStyleSheet(
            "QFrame#statusCodeRow { background: #14151f; border-radius: 10px; }"
            "QFrame#statusCodeRow:hover { background: #1a1b29; }"
        )
        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 12, 16, 12)
        layout.setSpacing(14)

        # coloured code pill
        code_pill = QLabel(str(code))
        code_pill.setFixedSize(60, 32)
        code_pill.setAlignment(Qt.AlignCenter)
        code_pill.setStyleSheet(
            f"background: {bg}; color: {fg};"
            "border-radius: 8px; font-weight: 800; font-size: 13px;"
            "letter-spacing: 0.5px;"
        )
        layout.addWidget(code_pill, 0, Qt.AlignVCenter)

        # name + description column
        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        title = QLabel(name)
        title.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 600;")
        text_col.addWidget(title)
        desc = QLabel(description)
        desc.setStyleSheet("color: #9aa0bd; font-size: 12px;")
        desc.setWordWrap(True)
        text_col.addWidget(desc)
        layout.addLayout(text_col, 1)

        return row

    # ── search filter ────────────────────────────────────────────────
    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        section_visible = {bucket: False for bucket, *_ in _CLASSES}

        # First pass — show / hide row widgets, remember which sections had hits.
        for key, w in self._rows:
            if isinstance(w, QLabel) and w.property("section"):
                continue
            visible = True
            if needle:
                code_str = str(key)
                # look up name + description for the row
                name, descriptions = STATUS_CODES.get(key, ("", {}))
                desc = descriptions.get(translator.language, descriptions.get("en", ""))
                hay = " ".join([code_str, name.lower(), desc.lower()])
                visible = needle in hay
            w.setVisible(visible)
            if visible:
                section_visible[key // 100] = True

        # Second pass — hide section headers that have no visible children.
        for bucket, w in self._rows:
            if isinstance(w, QLabel) and w.property("section"):
                w.setVisible(section_visible.get(bucket, False) or not needle)
