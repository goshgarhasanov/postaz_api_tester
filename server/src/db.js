// SQLite persistence for Postaz — serverless, file-based, zero-config.
// Schema mirrors the original desktop app: collections, requests, history,
// environments and a key/value settings table.
import Database from "better-sqlite3";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { mkdirSync } from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA_DIR = join(__dirname, "..", "data");
mkdirSync(DATA_DIR, { recursive: true });

const db = new Database(join(DATA_DIR, "postaz.db"));
db.pragma("journal_mode = WAL");

db.exec(`
CREATE TABLE IF NOT EXISTS collections (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  name       TEXT NOT NULL,
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS requests (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  collection_id INTEGER,
  name          TEXT NOT NULL DEFAULT 'Untitled',
  method        TEXT NOT NULL DEFAULT 'GET',
  url           TEXT NOT NULL DEFAULT '',
  headers       TEXT NOT NULL DEFAULT '[]',
  params        TEXT NOT NULL DEFAULT '[]',
  body          TEXT NOT NULL DEFAULT '',
  body_type     TEXT NOT NULL DEFAULT 'none',
  auth_type     TEXT NOT NULL DEFAULT 'none',
  auth_data     TEXT NOT NULL DEFAULT '{}',
  updated_at    INTEGER NOT NULL,
  FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS history (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  method      TEXT NOT NULL,
  url         TEXT NOT NULL,
  status_code INTEGER,
  duration_ms INTEGER,
  size_bytes  INTEGER,
  snapshot    TEXT NOT NULL DEFAULT '{}',
  created_at  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS environments (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  name      TEXT NOT NULL,
  variables TEXT NOT NULL DEFAULT '{}',
  active    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS settings (
  key   TEXT PRIMARY KEY,
  value TEXT
);
`);

export const now = () => Date.now();

// JSON helpers — columns above store JSON as TEXT.
export const parse = (s, fallback) => {
  try { return JSON.parse(s); } catch { return fallback; }
};

export default db;
