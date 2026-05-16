# Changelog

All notable changes to **Postaz** are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/) and the
project adheres to [Semantic Versioning](https://semver.org/).

## [2.0.1] — 2026-05-16

### Fixed
- **Installer crash** at the "Creating shortcuts…" step. The previous
  installer tried to drop the desktop shortcut into
  `C:\Users\Public\Desktop` which requires admin rights and clashed with
  the per-user install. Now writes to the current user's Desktop via
  `{autodesktop}` (no admin prompt, no `0x80070005`).
- Dropped the obsolete `WizardResizable` and `OnlyBelowVersion=6.1`
  directives that Inno Setup 6 flagged with warnings.

## [2.0.0] — 2026-05-16

> Major visual + feature overhaul. Postaz now looks and feels like a
> first-class Postman alternative.

### Added
- **Postman theme** — full repaint in Postman's dark grey + orange (#FF6C37)
  brand palette. New method colours, status badges, JSON highlighter,
  spinner, drop shadows.
- **Postman-style Console** — two-pane drawer with an entry table on top
  and a Request / Response detail viewer at the bottom. Captures every
  field (headers, params, body, auth, full response).
- **Status bar Console toggle** — clickable "›_ Console" pill at the
  bottom-left, mirroring Postman's UX. Stays in sync with View → Console.
- **HTTP Status Codes reference** dialog — 31 codes documented with
  colour-grouped sections, live search, EN/AZ/TR descriptions (Ctrl+/).
- **Live log viewer** — Help → View Logs (Ctrl+L) tails the rotating
  postaz.log with colour-highlighted level tags.
- **Modern Toggle Switch** (`ToggleSwitch`) — iOS-style animated pill,
  replaces every QCheckBox in headers / params / confirm dialog.
- **Modern Confirm Dialog** — frameless card, red trash glyph, drop
  shadow, "Don't ask me again" toggle with per-kind suppression.
- **Sidebar trash buttons** — every collection / request / history row
  gets a hover-only trash icon with pointing-hand cursor in its zone.
  Quick Saves is exempted.
- **"curl +" pill** in the sidebar toolbar — paste a curl command into
  the dialog and it auto-imports.
- **Mock API server** (`dev/mock_api.py`) — stdlib-only REST playground
  with GET/POST/PUT/PATCH/DELETE, /echo, /protected, /slow, /status/{code}.
- **Language picker** moved to the top-right corner widget of the
  menu bar (was previously in the sidebar header).
- **Per-row method badges** in the collection tree and history list,
  via a custom QStyledItemDelegate.
- **Reset delete confirmations** menu item under View.
- **Pretty JSON printer** in the Console detail viewer.
- **Custom-painted icon set** (`icons.py`) — 17 vector glyphs, no
  external assets.
- **Brand assets** — Postaz logo widget (`Logo`) and app icon, both
  using the orange gradient.

### Changed
- Window title is now **Postaz** (was *Local API Tester*).
- App data dir renamed to `Postaz/` (Windows `%APPDATA%/Postaz`,
  macOS `~/Library/Application Support/Postaz`, Linux
  `~/.local/share/Postaz`).
- DB file is `postaz.db` (was `app.db`).
- README expanded into a tri-lingual (EN / AZ / TR) document.
- All padding / margins reworked on a consistent 4 / 8 / 12 / 16 / 20
  spacing grid; visible borders softened to `#2E2E2E / #3A3A3A`.

### Removed
- **Light theme** — Postaz is dark-only now. Toggle Theme menu item is gone.
- Duplicate Language menu (the corner picker replaces it).

### Fixed
- cURL import: Chrome (Windows) "Copy as cURL (cmd)" with caret line
  continuations and `^"` escapes now parses correctly.
- cURL auto-detect on paste (`Ctrl+V` inside the import dialog) +
  250 ms debounced text-change fallback.
- `dlg.Accepted` AttributeError on PySide6 ≥ 6.11 — switched to
  `QDialog.Accepted` class-level enum reference.
- `urlencoded` body now sets `Content-Type` and accepts both
  `key=value&...` strings and JSON arrays.

## [1.0.0] — 2026-05-15

Initial release.

- Request builder (method, URL, params, headers, body, auth).
- Collections, history, environments with `{{var}}` substitution.
- SQLite persistence under the OS-native app-data dir.
- Threaded HTTP via `QThreadPool` — UI never blocks.
- Dark + Light themes.
- English / Azerbaijani / Turkish UI strings.
