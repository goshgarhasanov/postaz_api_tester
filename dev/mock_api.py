"""Dummy REST API for testing Postaz against real network round-trips.

Runs on http://localhost:8787 with an in-memory store of `users` and `posts`.
Every request is logged to stdout so you can correlate what Postaz sent
with what landed on the wire.

Endpoints
─────────
  GET    /                 → server info + endpoint listing
  GET    /health           → {"status": "ok"}
  GET    /echo?…           → echoes method, headers, params, body  (any verb)

  GET    /users            → list all users
  GET    /users/{id}       → one user                              (404 if missing)
  POST   /users            → create user from JSON body            (201)
  PUT    /users/{id}       → full replace                          (200 / 404)
  PATCH  /users/{id}       → partial update                        (200 / 404)
  DELETE /users/{id}       → remove                                (204 / 404)

  GET    /posts            → demo nested resource
  GET    /posts/{id}       → one post
  POST   /posts            → create

  GET    /protected        → 401 unless Authorization header present
  GET    /slow?ms=2000     → sleeps `ms` milliseconds before responding
  GET    /status/{code}    → returns the requested status code

Run
───
    python dev/mock_api.py [--port 8787]

Only the standard library is used — no Flask/FastAPI install required.
"""
from __future__ import annotations

import argparse
import json
import re
import threading
import time
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse


# ── in-memory store ──────────────────────────────────────────────────────
class Store:
    """Tiny thread-safe id-keyed table. Replaces a real DB for testing."""

    def __init__(self, seed: list[dict[str, Any]]):
        self._lock = threading.Lock()
        self._items = {it["id"]: dict(it) for it in seed}
        self._next_id = max(self._items, default=0) + 1

    def list(self) -> list[dict]:
        with self._lock:
            return [dict(v) for v in self._items.values()]

    def get(self, item_id: int) -> dict | None:
        with self._lock:
            v = self._items.get(item_id)
            return dict(v) if v else None

    def create(self, data: dict) -> dict:
        with self._lock:
            new_id = self._next_id
            self._next_id += 1
            data = {**data, "id": new_id, "createdAt": _now()}
            self._items[new_id] = data
            return dict(data)

    def replace(self, item_id: int, data: dict) -> dict | None:
        with self._lock:
            if item_id not in self._items:
                return None
            data = {**data, "id": item_id, "updatedAt": _now()}
            self._items[item_id] = data
            return dict(data)

    def patch(self, item_id: int, data: dict) -> dict | None:
        with self._lock:
            cur = self._items.get(item_id)
            if cur is None:
                return None
            cur.update(data)
            cur["id"] = item_id
            cur["updatedAt"] = _now()
            return dict(cur)

    def delete(self, item_id: int) -> bool:
        with self._lock:
            return self._items.pop(item_id, None) is not None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


USERS = Store([
    {"id": 1, "name": "Ada Lovelace",     "email": "ada@example.com",     "role": "engineer"},
    {"id": 2, "name": "Alan Turing",      "email": "alan@example.com",    "role": "cryptanalyst"},
    {"id": 3, "name": "Grace Hopper",     "email": "grace@example.com",   "role": "admiral"},
    {"id": 4, "name": "Linus Torvalds",   "email": "linus@example.com",   "role": "engineer"},
])

POSTS = Store([
    {"id": 1, "userId": 1, "title": "Engines of difference", "body": "A note on calculating engines."},
    {"id": 2, "userId": 2, "title": "On computable numbers", "body": "Decidability is hard."},
    {"id": 3, "userId": 3, "title": "Debugging the Mark II", "body": "First literal bug."},
])


# ── request handler ──────────────────────────────────────────────────────
class _Handler(BaseHTTPRequestHandler):
    server_version = "PostazMock/1.0"

    # silence default access log; we print our own coloured line
    def log_message(self, _fmt, *_args):
        pass

    # ── routing table ────────────────────────────────────────────────
    def _routes(self) -> list[tuple[str, str, Callable]]:
        return [
            ("GET",    r"^/$",                 self.root),
            ("GET",    r"^/health$",           self.health),
            ("ANY",    r"^/echo$",             self.echo),

            ("GET",    r"^/users$",            lambda **_: self.json(200, USERS.list())),
            ("POST",   r"^/users$",            self.create_user),
            ("GET",    r"^/users/(\d+)$",      self.get_user),
            ("PUT",    r"^/users/(\d+)$",      self.put_user),
            ("PATCH",  r"^/users/(\d+)$",      self.patch_user),
            ("DELETE", r"^/users/(\d+)$",      self.delete_user),

            ("GET",    r"^/posts$",            lambda **_: self.json(200, POSTS.list())),
            ("GET",    r"^/posts/(\d+)$",      self.get_post),
            ("POST",   r"^/posts$",            self.create_post),

            ("GET",    r"^/protected$",        self.protected),
            ("GET",    r"^/slow$",             self.slow),
            ("GET",    r"^/status/(\d+)$",     self.status_code),
        ]

    # ── dispatch ─────────────────────────────────────────────────────
    def _dispatch(self, method: str) -> None:
        parsed = urlparse(self.path)
        path = parsed.path or "/"
        for verb, pattern, handler in self._routes():
            if verb not in (method, "ANY"):
                continue
            m = re.match(pattern, path)
            if m is None:
                continue
            self._log_line(method, self.path)
            try:
                handler(*m.groups())
            except Exception as e:                                      # safety net
                self.json(500, {"error": f"server crash: {e}"})
            return
        self._log_line(method, self.path, missed=True)
        self.json(404, {"error": "not found", "path": path})

    # Wire every HTTP verb to the same dispatcher
    def do_GET(self):    self._dispatch("GET")
    def do_POST(self):   self._dispatch("POST")
    def do_PUT(self):    self._dispatch("PUT")
    def do_PATCH(self):  self._dispatch("PATCH")
    def do_DELETE(self): self._dispatch("DELETE")
    def do_OPTIONS(self):
        # CORS pre-flight — Postaz is a desktop client but this also lets
        # browsers and other tools hit the API painlessly.
        self.send_response(204)
        self._cors()
        self.end_headers()

    # ── handlers ─────────────────────────────────────────────────────
    def root(self, *_):
        self.json(200, {
            "name": "Postaz mock API",
            "version": "1.0",
            "now": _now(),
            "endpoints": [
                "GET    /health",
                "ANY    /echo",
                "GET    /users",
                "POST   /users",
                "GET    /users/{id}",
                "PUT    /users/{id}",
                "PATCH  /users/{id}",
                "DELETE /users/{id}",
                "GET    /posts",
                "POST   /posts",
                "GET    /posts/{id}",
                "GET    /protected",
                "GET    /slow?ms=N",
                "GET    /status/{code}",
            ],
        })

    def health(self, *_):
        self.json(200, {"status": "ok", "uptime": _now()})

    def echo(self, *_):
        body = self._read_body()
        try:
            body_json: Any = json.loads(body) if body else None
        except Exception:
            body_json = None
        parsed = urlparse(self.path)
        self.json(200, {
            "method": self.command,
            "path": parsed.path,
            "query": {k: v[0] if len(v) == 1 else v for k, v in parse_qs(parsed.query).items()},
            "headers": {k: v for k, v in self.headers.items()},
            "body_text": body.decode("utf-8", errors="replace") if body else "",
            "body_json": body_json,
            "received_at": _now(),
        })

    # ── users ────────────────────────────────────────────────────────
    def get_user(self, uid: str):
        u = USERS.get(int(uid))
        self.json(200, u) if u else self.json(404, {"error": "user not found", "id": int(uid)})

    def create_user(self, *_):
        data = self._read_json()
        if not isinstance(data, dict):
            return self.json(400, {"error": "expected a JSON object body"})
        new = USERS.create(data)
        self.json(201, new)

    def put_user(self, uid: str):
        data = self._read_json()
        if not isinstance(data, dict):
            return self.json(400, {"error": "expected a JSON object body"})
        updated = USERS.replace(int(uid), data)
        self.json(200, updated) if updated else self.json(404, {"error": "user not found"})

    def patch_user(self, uid: str):
        data = self._read_json()
        if not isinstance(data, dict):
            return self.json(400, {"error": "expected a JSON object body"})
        updated = USERS.patch(int(uid), data)
        self.json(200, updated) if updated else self.json(404, {"error": "user not found"})

    def delete_user(self, uid: str):
        if USERS.delete(int(uid)):
            self.send_response(204)
            self._cors()
            self.end_headers()
        else:
            self.json(404, {"error": "user not found"})

    # ── posts ────────────────────────────────────────────────────────
    def get_post(self, pid: str):
        p = POSTS.get(int(pid))
        self.json(200, p) if p else self.json(404, {"error": "post not found"})

    def create_post(self, *_):
        data = self._read_json()
        if not isinstance(data, dict):
            return self.json(400, {"error": "expected a JSON object body"})
        self.json(201, POSTS.create(data))

    # ── extras ───────────────────────────────────────────────────────
    def protected(self, *_):
        if "Authorization" not in self.headers:
            return self.json(401, {"error": "missing Authorization header"})
        self.json(200, {"message": "you are in", "auth": self.headers["Authorization"]})

    def slow(self, *_):
        ms = 1000
        qs = parse_qs(urlparse(self.path).query)
        if "ms" in qs:
            try:
                ms = max(0, min(int(qs["ms"][0]), 10_000))
            except ValueError:
                pass
        time.sleep(ms / 1000)
        self.json(200, {"slept_ms": ms, "at": _now()})

    def status_code(self, code: str):
        try:
            code_int = int(code)
        except ValueError:
            return self.json(400, {"error": "invalid status code"})
        if not 100 <= code_int <= 599:
            return self.json(400, {"error": "status code out of range"})
        try:
            reason = HTTPStatus(code_int).phrase
        except ValueError:
            reason = ""
        self.json(code_int, {"code": code_int, "reason": reason})

    # ── helpers ──────────────────────────────────────────────────────
    def _read_body(self) -> bytes:
        n = int(self.headers.get("Content-Length", "0") or "0")
        return self.rfile.read(n) if n else b""

    def _read_json(self) -> Any:
        raw = self._read_body()
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _log_line(self, method: str, path: str, missed: bool = False) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        verb = f"{method:<6}"
        marker = " ✗" if missed else " ·"
        print(f"  {ts}{marker} {verb}  {path}")


# ── entry point ──────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(description="Postaz mock REST API")
    parser.add_argument("--port", "-p", type=int, default=8787)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), _Handler)
    addr = f"http://{args.host}:{args.port}"
    print()
    print(f"  Postaz mock API listening on  {addr}")
    print(f"  Try:  curl {addr}/users")
    print(f"        curl -X POST {addr}/users -H 'Content-Type: application/json' -d '{{\"name\":\"Ada\"}}'")
    print(f"        curl {addr}/echo?hello=world")
    print(f"  Stop with Ctrl+C")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  shutting down")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
