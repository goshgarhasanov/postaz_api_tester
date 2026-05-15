"""SQLite persistence layer.

Owns every piece of durable state the app cares about: collections, saved
requests, request history, environments and a small key/value settings store.
The class is intentionally thin — it speaks SQL and returns plain dataclasses /
dicts. UI code never touches the connection directly.

Thread-safety: each calling thread receives its **own** sqlite3 connection
through `threading.local`. SQLite itself handles cross-connection isolation
(we run in WAL mode for fast concurrent reads + a single writer)."""
from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .logger import get_logger

log = get_logger(__name__)

DB_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER REFERENCES collections(id) ON DELETE CASCADE,
    position INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER REFERENCES collections(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    method TEXT NOT NULL DEFAULT 'GET',
    url TEXT NOT NULL DEFAULT '',
    headers TEXT DEFAULT '[]',
    params TEXT DEFAULT '[]',
    body TEXT DEFAULT '',
    body_type TEXT DEFAULT 'none',
    auth_type TEXT DEFAULT 'none',
    auth_data TEXT DEFAULT '{}',
    position INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    method TEXT,
    url TEXT,
    status_code INTEGER,
    duration_ms INTEGER,
    snapshot TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS environments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    variables TEXT DEFAULT '{}',
    is_active INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE INDEX IF NOT EXISTS idx_requests_collection ON requests(collection_id);
CREATE INDEX IF NOT EXISTS idx_collections_parent ON collections(parent_id);
CREATE INDEX IF NOT EXISTS idx_history_created ON history(created_at DESC);
"""


@dataclass
class RequestRecord:
    id: Optional[int] = None
    collection_id: Optional[int] = None
    name: str = "Untitled Request"
    method: str = "GET"
    url: str = ""
    headers: list[dict] = field(default_factory=list)
    params: list[dict] = field(default_factory=list)
    body: str = ""
    body_type: str = "none"  # none | json | form | raw | urlencoded
    auth_type: str = "none"
    auth_data: dict = field(default_factory=dict)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "RequestRecord":
        return cls(
            id=row["id"],
            collection_id=row["collection_id"],
            name=row["name"],
            method=row["method"],
            url=row["url"],
            headers=json.loads(row["headers"] or "[]"),
            params=json.loads(row["params"] or "[]"),
            body=row["body"] or "",
            body_type=row["body_type"] or "none",
            auth_type=row["auth_type"] or "none",
            auth_data=json.loads(row["auth_data"] or "{}"),
        )


@dataclass
class CollectionNode:
    id: int
    name: str
    parent_id: Optional[int]
    position: int = 0


class Database:
    """Thread-safe SQLite wrapper. One connection per thread via local storage."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        """Return (and lazily create) a connection bound to the current thread.

        Each Qt worker thread that touches the DB gets its own connection so
        we never share a `sqlite3.Connection` across threads (which is
        unsupported in sqlite3 without `check_same_thread=False`)."""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self.path), check_same_thread=False)
            conn.row_factory = sqlite3.Row              # rows accessed by column name
            conn.execute("PRAGMA foreign_keys = ON")    # enforce cascading deletes
            conn.execute("PRAGMA journal_mode = WAL")   # readers don't block writers
            self._local.conn = conn
        return conn

    def _init_schema(self) -> None:
        """Run the idempotent schema script — safe to call on every startup."""
        with self._conn() as c:
            c.executescript(SCHEMA)
            c.execute(
                "INSERT OR IGNORE INTO meta(key, value) VALUES (?, ?)",
                ("db_version", str(DB_VERSION)),
            )

    # ── settings ──────────────────────────────────────────────────────────
    # Simple key/value store used for things like remembered language and theme.
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        row = self._conn().execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO settings(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    # ── collections ───────────────────────────────────────────────────────
    # Collections are simple named folders. They can nest (`parent_id`) but the
    # sidebar currently renders only a single level — the schema is ready for more.
    def list_collections(self) -> list[CollectionNode]:
        """Return every collection, ordered by position then name."""
        rows = self._conn().execute(
            "SELECT id, name, parent_id, position FROM collections ORDER BY position, name"
        ).fetchall()
        return [CollectionNode(r["id"], r["name"], r["parent_id"], r["position"]) for r in rows]

    def create_collection(self, name: str, parent_id: Optional[int] = None) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO collections(name, parent_id) VALUES (?, ?)",
                (name, parent_id),
            )
            return cur.lastrowid

    def rename_collection(self, collection_id: int, name: str) -> None:
        with self._conn() as c:
            c.execute("UPDATE collections SET name = ? WHERE id = ?", (name, collection_id))

    def delete_collection(self, collection_id: int) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM collections WHERE id = ?", (collection_id,))

    # ── requests ──────────────────────────────────────────────────────────
    # A "request" is one saved HTTP call (method + url + headers + body + auth).
    # Lists/dicts are stored as JSON text so the schema doesn't need migration
    # every time we add a body type or auth scheme.
    def list_requests(self, collection_id: Optional[int] = None) -> list[RequestRecord]:
        """Requests inside one collection (or `None` for root-level "Quick Saves")."""
        if collection_id is None:
            rows = self._conn().execute(
                "SELECT * FROM requests WHERE collection_id IS NULL ORDER BY position, name"
            ).fetchall()
        else:
            rows = self._conn().execute(
                "SELECT * FROM requests WHERE collection_id = ? ORDER BY position, name",
                (collection_id,),
            ).fetchall()
        return [RequestRecord.from_row(r) for r in rows]

    def get_request(self, request_id: int) -> Optional[RequestRecord]:
        row = self._conn().execute(
            "SELECT * FROM requests WHERE id = ?", (request_id,)
        ).fetchone()
        return RequestRecord.from_row(row) if row else None

    def save_request(self, rec: RequestRecord) -> int:
        """Insert when `rec.id is None`, otherwise update in place.

        Mutates `rec.id` on insert so the caller can keep the same dataclass
        instance after saving and trigger further updates without re-fetching."""
        log.info("save request: name=%r method=%s url=%s id=%s", rec.name, rec.method, rec.url, rec.id)
        payload = (
            rec.collection_id,
            rec.name,
            rec.method,
            rec.url,
            json.dumps(rec.headers),
            json.dumps(rec.params),
            rec.body,
            rec.body_type,
            rec.auth_type,
            json.dumps(rec.auth_data),
        )
        with self._conn() as c:
            if rec.id is None:
                cur = c.execute(
                    "INSERT INTO requests(collection_id, name, method, url, headers, params, "
                    "body, body_type, auth_type, auth_data) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    payload,
                )
                rec.id = cur.lastrowid
            else:
                c.execute(
                    "UPDATE requests SET collection_id=?, name=?, method=?, url=?, headers=?, "
                    "params=?, body=?, body_type=?, auth_type=?, auth_data=?, "
                    "updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (*payload, rec.id),
                )
            return rec.id

    def delete_request(self, request_id: int) -> None:
        log.info("delete request id=%d", request_id)
        with self._conn() as c:
            c.execute("DELETE FROM requests WHERE id = ?", (request_id,))

    # ── history ───────────────────────────────────────────────────────────
    # Every executed request leaves a row here with both request + response
    # JSON snapshots. We cap the table at 200 rows by deleting overflow after
    # each insert — keeps the file small and the sidebar list snappy.
    def add_history(
        self,
        method: str,
        url: str,
        status_code: int,
        duration_ms: int,
        snapshot: dict[str, Any],
    ) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO history(method, url, status_code, duration_ms, snapshot) "
                "VALUES (?, ?, ?, ?, ?)",
                (method, url, status_code, duration_ms, json.dumps(snapshot)),
            )
            c.execute(
                "DELETE FROM history WHERE id NOT IN "
                "(SELECT id FROM history ORDER BY created_at DESC LIMIT 200)"
            )

    def list_history(self, limit: int = 100) -> list[dict]:
        rows = self._conn().execute(
            "SELECT id, method, url, status_code, duration_ms, snapshot, created_at "
            "FROM history ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {
                "id": r["id"],
                "method": r["method"],
                "url": r["url"],
                "status_code": r["status_code"],
                "duration_ms": r["duration_ms"],
                "snapshot": json.loads(r["snapshot"] or "{}"),
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    def clear_history(self) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM history")

    # ── environments ──────────────────────────────────────────────────────
    # An environment is a named bag of `{key: value}` variables. Exactly one
    # row carries `is_active=1` at a time and supplies the substitutions for
    # `{{var}}` placeholders inside URLs, headers, body and auth fields.
    def list_environments(self) -> list[dict]:
        rows = self._conn().execute(
            "SELECT id, name, variables, is_active FROM environments ORDER BY name"
        ).fetchall()
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "variables": json.loads(r["variables"] or "{}"),
                "is_active": bool(r["is_active"]),
            }
            for r in rows
        ]

    def create_environment(self, name: str, variables: dict[str, str]) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO environments(name, variables) VALUES (?, ?)",
                (name, json.dumps(variables)),
            )
            return cur.lastrowid

    def update_environment(self, env_id: int, name: str, variables: dict[str, str]) -> None:
        with self._conn() as c:
            c.execute(
                "UPDATE environments SET name = ?, variables = ? WHERE id = ?",
                (name, json.dumps(variables), env_id),
            )

    def delete_environment(self, env_id: int) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM environments WHERE id = ?", (env_id,))

    def set_active_environment(self, env_id: Optional[int]) -> None:
        with self._conn() as c:
            c.execute("UPDATE environments SET is_active = 0")
            if env_id is not None:
                c.execute("UPDATE environments SET is_active = 1 WHERE id = ?", (env_id,))

    def get_active_environment(self) -> Optional[dict]:
        row = self._conn().execute(
            "SELECT id, name, variables FROM environments WHERE is_active = 1 LIMIT 1"
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "variables": json.loads(row["variables"] or "{}"),
        }
