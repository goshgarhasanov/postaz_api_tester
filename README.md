<div align="center">

# 🚀 Local API Tester

### A blazing-fast, beautiful Postman alternative — built with Python & Qt

<br>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.6%2B-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://doc.qt.io/qtforpython-6/)
[![SQLite](https://img.shields.io/badge/SQLite-Embedded-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-7c5cff?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-2a2c40?style=for-the-badge)]()

<br>

**Send HTTP requests. Organize collections. Test APIs. All locally, all offline, all yours.**

<br>

[Features](#-features) • [Screenshots](#-screenshots) • [Install](#-installation) • [Usage](#-usage) • [Shortcuts](#%EF%B8%8F-keyboard-shortcuts) • [Architecture](#-architecture)

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%" valign="top">

### 🔥 Powerful Request Builder
- **All HTTP verbs** — `GET` `POST` `PUT` `PATCH` `DELETE` `HEAD` `OPTIONS`
- **Query params** with enable/disable toggle per row
- **Custom headers** editor (table with check-boxes)
- **Body types** — JSON, raw, url-encoded, none
- **Format JSON** one-click pretty-printer
- **Auth presets** — Bearer · Basic · API Key · None

</td>
<td width="50%" valign="top">

### 🎨 Premium UI/UX
- **Dark + Light** themes — `Ctrl+T` to toggle
- **Smooth animations** — fades, spinners, overlay loaders
- **JSON syntax highlighting** in response body
- **Color-coded status badges** — green 2xx, blue 3xx, orange 4xx, red 5xx
- **Toast notifications** — non-intrusive feedback
- **Drop shadows + glow** on primary actions

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 📚 Collections & Workspaces
- **Tree-organized** collections in the sidebar
- **Quick saves** for one-off requests
- **Rename / delete** via context menu
- **Live filter** — search across all requests
- **Per-collection** organization

</td>
<td width="50%" valign="top">

### 🌍 Environments & Variables
- **Multiple environments** — dev, staging, prod
- **`{{variable}}` substitution** anywhere — URLs, headers, body, auth
- **Active-env indicator** in the status bar
- **Per-env variable editor** with live persistence

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 📜 History & Replay
- **Last 200 requests** auto-saved
- **One-click replay** — open any past call
- **Includes the full response snapshot**
- **Searchable** via the sidebar filter
- **Clear all** with one menu action

</td>
<td width="50%" valign="top">

### ⚡ Performance & Safety
- **Threaded HTTP** via `QThreadPool` — UI **never** freezes
- **WAL-mode SQLite** for fast, durable writes
- **Foreign-key cascades** keep data clean
- **Capped history** — auto-trims to 200
- **Zero telemetry** — your data stays on your machine

</td>
</tr>
</table>

---

## 📸 Screenshots

> Add screenshots after running the app — drop `.png` files into `docs/` and reference them here.

```
┌──────────────────┬──────────────────────────────────────────────┐
│  Collections     │  GET   ▾  {{baseUrl}}/users/42        [Send] │
│  ▾ My API        ├──────────────────────────────────────────────┤
│    GET   /users  │  Params  Headers  Body  Auth                 │
│    POST  /login  │  ─────────────────────────────────────────   │
│  History         │  ☑ Authorization  Bearer {{token}}           │
│    200  /users   │  ☑ Accept         application/json           │
│    401  /login   ├──────────────────────────────────────────────┤
│                  │  200 OK  •  ⏱ 142 ms  •  ⇣ 1.2 KB            │
│                  │  Body  Headers  Raw                          │
│                  │  {                                           │
│                  │    "id": 42,                                 │
│                  │    "name": "Ada Lovelace"                    │
│                  │  }                                           │
└──────────────────┴──────────────────────────────────────────────┘
```

---

## 🚀 Installation

### Prerequisites
- **Python 3.10+** ([download](https://www.python.org/downloads/))

### Quick start (Windows / PowerShell)

```powershell
git clone https://github.com/<your-user>/local-api-tester.git
cd local-api-tester
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

### macOS / Linux

```bash
git clone https://github.com/<your-user>/local-api-tester.git
cd local-api-tester
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Where is my data stored?

| OS       | Path                                                |
| -------- | --------------------------------------------------- |
| Windows  | `%APPDATA%\LocalAPITester\app.db`                   |
| macOS    | `~/Library/Application Support/LocalAPITester/app.db` |
| Linux    | `~/.local/share/LocalAPITester/app.db`              |

---

## 💡 Usage

### 1️⃣ Send your first request
- Type a URL into the URL bar — e.g. `https://httpbin.org/get`
- Press **`Ctrl+Enter`** or click **Send**
- Watch the response render with status badge, timing, and pretty-printed JSON

### 2️⃣ Save to a collection
- Click **Save** → choose an existing collection or create a new one
- The request appears in the sidebar, ready to re-open anytime

### 3️⃣ Use environment variables
- `Ctrl+E` → **New** → name it `dev`
- Add variables like `baseUrl` = `https://api.example.com/v1`
- Click **Set as active**
- Use `{{baseUrl}}/users` in any request — the variable is substituted at send time

### 4️⃣ Replay from history
- Switch the sidebar tab to **History**
- Double-click any past request to load it back into the editor (with its response)

---

## ⌨️ Keyboard Shortcuts

| Action              | Shortcut       |
| ------------------- | -------------- |
| Send request        | `Ctrl + Enter` |
| Save request        | `Ctrl + S`     |
| New request         | `Ctrl + N`     |
| Manage environments | `Ctrl + E`     |
| Toggle dark / light | `Ctrl + T`     |
| Quit                | `Ctrl + Q`     |

---

## 🏗️ Architecture

```
api-tester/
├── main.py                    🟢 Entry point — bootstraps QApplication & DB
├── requirements.txt
└── app/
    ├── database.py            🗄️  SQLite layer, thread-safe, WAL mode
    ├── http_client.py         🌐 requests-powered HTTP execution
    ├── env_resolver.py        🔁 {{var}} substitution engine
    ├── workers.py             🧵 QRunnable HTTP worker (non-blocking)
    └── ui/
        ├── main_window.py     🪟 Top-level shell, menus, splitters, theming
        ├── sidebar.py         📚 Collections tree + history list
        ├── request_editor.py  ✏️  Method/URL/Send + Params/Headers/Body/Auth
        ├── response_viewer.py 📥 Status + body + headers + raw
        ├── dialogs.py         💬 Save dialog & environment manager
        ├── widgets.py         🧩 Spinner, Toast, StatusBadge, KVTable, LoaderOverlay
        ├── animations.py      ✨ Fade, slide, pulse helpers
        └── styles.py          🎨 Dark + Light QSS themes
```

### Tech stack
- **[PySide6](https://doc.qt.io/qtforpython-6/)** — Qt6 bindings for Python (LGPL)
- **[requests](https://docs.python-requests.org/)** — battle-tested HTTP client
- **[SQLite](https://www.sqlite.org/)** — embedded, zero-config persistence

### Design principles
- **No blocking on the UI thread** — every HTTP call runs in `QThreadPool`
- **Modular widgets** — each panel is self-contained and reusable
- **Stateless workers** — request records flow through, no shared mutable state
- **Theme via QSS** — no hard-coded colors in widget code

---

## 🗺️ Roadmap

- [ ] cURL import / export
- [ ] OpenAPI / Swagger import
- [ ] Response diff between runs
- [ ] WebSocket testing
- [ ] gRPC support
- [ ] Pre-request scripts (Python sandbox)
- [ ] Team collections sync (optional cloud)
- [ ] Drag-and-drop reorder in sidebar

---

## 🤝 Contributing

PRs welcome! For larger changes please open an issue first to discuss the approach.

```bash
git checkout -b feat/your-feature
# hack hack hack
git commit -m "feat: add cURL import"
git push origin feat/your-feature
```

---

## 📜 License

MIT — see [LICENSE](LICENSE).

<br>

<div align="center">

**Built with ❤️ — because sometimes you just want Postman without the bloat.**

⭐ **If you find this useful, please star the repo!**

</div>
