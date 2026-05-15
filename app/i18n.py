"""Internationalization: AZ / EN / TR with native-speaker grammar.

Usage:
    from .i18n import t, set_language, translator

    label.setText(t("Save"))
    translator.language_changed.connect(self._retranslate)
"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal


LANGUAGES = ("en", "az", "tr")
LANGUAGE_LABELS = {
    "en": "English",
    "az": "Azərbaycan",
    "tr": "Türkçe",
}


# Keys are the canonical English strings — that doubles as the EN value.
# AZ and TR are native, professional translations.
_DICT: dict[str, dict[str, str]] = {
    # ── App / window titles ──────────────────────────────────────
    "Postaz — Local API Tester":       {"az": "Postaz — Lokal API Tester", "tr": "Postaz — Yerel API Test Aracı"},
    "Postaz":                          {"az": "Postaz", "tr": "Postaz"},
    "Local API Tester":                {"az": "Lokal API Tester", "tr": "Yerel API Test Aracı"},

    # ── Menus ────────────────────────────────────────────────────
    "&File":                           {"az": "&Fayl", "tr": "&Dosya"},
    "&Request":                        {"az": "&Sorğu", "tr": "&İstek"},
    "&Environments":                   {"az": "&Mühitlər", "tr": "&Ortamlar"},
    "&View":                           {"az": "&Görünüş", "tr": "&Görünüm"},
    "&Language":                       {"az": "&Dil", "tr": "&Dil"},
    "&Help":                           {"az": "&Kömək", "tr": "&Yardım"},

    "New Request":                     {"az": "Yeni Sorğu", "tr": "Yeni İstek"},
    "Save":                            {"az": "Yadda saxla", "tr": "Kaydet"},
    "Export Response…":                {"az": "Cavabı ixrac et…", "tr": "Yanıtı Dışa Aktar…"},
    "Quit":                            {"az": "Çıxış", "tr": "Çıkış"},
    "Send":                            {"az": "Göndər", "tr": "Gönder"},
    "Manage…":                         {"az": "İdarə et…", "tr": "Yönet…"},
    "Toggle Theme":                    {"az": "Mövzunu dəyiş", "tr": "Temayı Değiştir"},
    "Clear History":                   {"az": "Tarixçəni təmizlə", "tr": "Geçmişi Temizle"},
    "About":                           {"az": "Haqqında", "tr": "Hakkında"},

    # ── Sidebar ──────────────────────────────────────────────────
    "Collections":                     {"az": "Kolleksiyalar", "tr": "Koleksiyonlar"},
    "History":                         {"az": "Tarixçə", "tr": "Geçmiş"},
    "Search…":                         {"az": "Axtar…", "tr": "Ara…"},
    "Quick Saves":                     {"az": "Sürətli yaddaş", "tr": "Hızlı Kayıtlar"},
    "New collection":                  {"az": "Yeni kolleksiya", "tr": "Yeni koleksiyon"},
    "New Collection":                  {"az": "Yeni Kolleksiya", "tr": "Yeni Koleksiyon"},
    "Collection name:":                {"az": "Kolleksiya adı:", "tr": "Koleksiyon adı:"},
    "Rename collection":               {"az": "Kolleksiyanın adını dəyiş", "tr": "Koleksiyonu yeniden adlandır"},
    "Delete collection":               {"az": "Kolleksiyanı sil", "tr": "Koleksiyonu sil"},
    "Delete this collection and all its requests?":
        {"az": "Bu kolleksiya və daxilindəki bütün sorğular silinsin?",
         "tr": "Bu koleksiyon ve içindeki tüm istekler silinsin mi?"},
    "Rename":                          {"az": "Adını dəyiş", "tr": "Yeniden adlandır"},
    "Name:":                           {"az": "Ad:", "tr": "Ad:"},
    "Open":                            {"az": "Aç", "tr": "Aç"},
    "Delete":                          {"az": "Sil", "tr": "Sil"},
    "Delete request":                  {"az": "Sorğunu sil", "tr": "İsteği sil"},
    "Delete this request?":            {"az": "Bu sorğu silinsin?", "tr": "Bu istek silinsin mi?"},

    # ── Request editor ───────────────────────────────────────────
    "Params":                          {"az": "Parametrlər", "tr": "Parametreler"},
    "Headers":                         {"az": "Başlıqlar", "tr": "Başlıklar"},
    "Body":                            {"az": "Gövdə", "tr": "Gövde"},
    "Auth":                            {"az": "Doğrulama", "tr": "Kimlik Doğrulama"},
    "Body type:":                      {"az": "Gövdə tipi:", "tr": "Gövde tipi:"},
    "Auth type:":                      {"az": "Doğrulama tipi:", "tr": "Kimlik doğrulama tipi:"},
    "Format JSON":                     {"az": "JSON-u formatla", "tr": "JSON'u Biçimlendir"},
    "Untitled request":                {"az": "Adsız sorğu", "tr": "Adsız istek"},
    "Untitled":                        {"az": "Adsız", "tr": "Adsız"},
    "Sending…":                        {"az": "Göndərilir…", "tr": "Gönderiliyor…"},
    "Sending request…":                {"az": "Sorğu göndərilir…", "tr": "İstek gönderiliyor…"},
    "Token":                           {"az": "Token", "tr": "Token"},
    "Username":                        {"az": "İstifadəçi adı", "tr": "Kullanıcı adı"},
    "Password":                        {"az": "Şifrə", "tr": "Parola"},
    "Header":                          {"az": "Başlıq", "tr": "Başlık"},
    "Value":                           {"az": "Dəyər", "tr": "Değer"},
    "This request will not include any authorization.":
        {"az": "Bu sorğuya heç bir doğrulama daxil edilməyəcək.",
         "tr": "Bu isteğe herhangi bir kimlik doğrulama dahil edilmeyecek."},
    "Token (supports {{var}})":
        {"az": "Token ({{dəyişən}} dəstəklənir)",
         "tr": "Token ({{değişken}} desteklenir)"},
    "Header name (e.g. X-API-Key)":
        {"az": "Başlığın adı (məs. X-API-Key)",
         "tr": "Başlık adı (örn. X-API-Key)"},
    "Key":                             {"az": "Açar", "tr": "Anahtar"},
    "Description":                     {"az": "Təsvir", "tr": "Açıklama"},
    "https://api.example.com/v1/users  —  use {{baseUrl}} for vars":
        {"az": "https://api.example.com/v1/users  —  dəyişən üçün {{baseUrl}}",
         "tr": "https://api.example.com/v1/users  —  değişken için {{baseUrl}}"},

    # ── Response viewer ──────────────────────────────────────────
    "Raw":                             {"az": "Xam", "tr": "Ham"},
    "Send a request to see the response here.":
        {"az": "Cavabı burada görmək üçün sorğu göndərin.",
         "tr": "Yanıtı burada görmek için bir istek gönderin."},
    "Response body will appear here.":
        {"az": "Cavabın gövdəsi burada görünəcək.",
         "tr": "Yanıt gövdesi burada görünecek."},

    # ── Save dialog ──────────────────────────────────────────────
    "Save Request":                    {"az": "Sorğunu Yadda Saxla", "tr": "İsteği Kaydet"},
    "Name":                            {"az": "Ad", "tr": "Ad"},
    "Collection":                      {"az": "Kolleksiya", "tr": "Koleksiyon"},
    "Or create new collection…":       {"az": "Və ya yeni kolleksiya yarat…", "tr": "Veya yeni koleksiyon oluştur…"},
    "Create":                          {"az": "Yarat", "tr": "Oluştur"},
    "Cancel":                          {"az": "Ləğv et", "tr": "İptal"},

    # ── Environments dialog ──────────────────────────────────────
    "Environments":                    {"az": "Mühitlər", "tr": "Ortamlar"},
    "New":                             {"az": "Yeni", "tr": "Yeni"},
    "New environment":                 {"az": "Yeni mühit", "tr": "Yeni ortam"},
    "Set as active":                   {"az": "Aktiv et", "tr": "Aktif yap"},
    "Done":                            {"az": "Hazır", "tr": "Tamam"},
    "Variable":                        {"az": "Dəyişən", "tr": "Değişken"},
    "Delete environment '{name}'?":
        {"az": "'{name}' adlı mühit silinsin?", "tr": "'{name}' adlı ortam silinsin mi?"},
    "Delete":                          {"az": "Sil", "tr": "Sil"},

    # ── Status bar / toasts ──────────────────────────────────────
    "Ready":                           {"az": "Hazır", "tr": "Hazır"},
    "Saved":                           {"az": "Yadda saxlanıldı", "tr": "Kaydedildi"},
    "URL is required":                 {"az": "URL daxil edilməlidir", "tr": "URL gerekli"},
    "No response to export":           {"az": "İxrac edəcək cavab yoxdur", "tr": "Dışa aktarılacak yanıt yok"},
    "Exported":                        {"az": "İxrac edildi", "tr": "Dışa aktarıldı"},
    "Export response":                 {"az": "Cavabı ixrac et", "tr": "Yanıtı dışa aktar"},
    "History cleared":                 {"az": "Tarixçə təmizləndi", "tr": "Geçmiş temizlendi"},
    "New request":                     {"az": "Yeni sorğu", "tr": "Yeni istek"},
    "Opened: {name}":                  {"az": "Açıldı: {name}", "tr": "Açıldı: {name}"},
    "Loaded from history":             {"az": "Tarixçədən yükləndi", "tr": "Geçmişten yüklendi"},
    "Request failed":                  {"az": "Sorğu uğursuz oldu", "tr": "İstek başarısız"},
    "No environment":                  {"az": "Mühit yoxdur", "tr": "Ortam yok"},
    "Clear":                           {"az": "Təmizlə", "tr": "Temizle"},
    "Clear all request history?":      {"az": "Bütün sorğu tarixçəsi silinsin?",
                                        "tr": "Tüm istek geçmişi silinsin mi?"},

    # ── Misc ─────────────────────────────────────────────────────
    "Status: {code}\nTime: {ms} ms\nAt: {ts}":
        {"az": "Status: {code}\nVaxt: {ms} ms\nTarix: {ts}",
         "tr": "Durum: {code}\nSüre: {ms} ms\nTarih: {ts}"},
    "Yes":                             {"az": "Bəli", "tr": "Evet"},
    "No":                              {"az": "Xeyr", "tr": "Hayır"},
}


class _Translator(QObject):
    """Singleton-style translator with a Qt signal for live retranslation."""

    language_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._lang = "en"

    @property
    def language(self) -> str:
        return self._lang

    def set_language(self, lang: str) -> None:
        if lang not in LANGUAGES:
            lang = "en"
        if lang == self._lang:
            return
        self._lang = lang
        self.language_changed.emit(lang)

    def t(self, key: str, **fmt) -> str:
        if self._lang == "en":
            out = key
        else:
            entry = _DICT.get(key)
            out = entry.get(self._lang, key) if entry else key
        if fmt:
            try:
                out = out.format(**fmt)
            except (KeyError, IndexError):
                pass
        return out


translator = _Translator()


def t(key: str, **fmt) -> str:
    """Shorthand for translator.t()."""
    return translator.t(key, **fmt)


def set_language(lang: str) -> None:
    translator.set_language(lang)
