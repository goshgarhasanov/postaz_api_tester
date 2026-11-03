// Collections + the requests saved inside them.
import { Router } from "express";
import db, { now, parse } from "../db.js";

const router = Router();

const rowToRequest = (r) => ({
  id: r.id,
  collectionId: r.collection_id,
  name: r.name,
  method: r.method,
  url: r.url,
  headers: parse(r.headers, []),
  params: parse(r.params, []),
  body: r.body,
  bodyType: r.body_type,
  authType: r.auth_type,
  authData: parse(r.auth_data, {}),
  updatedAt: r.updated_at,
});

// ── collections ──────────────────────────────────────────────────────
router.get("/", (_req, res) => {
  const cols = db.prepare("SELECT * FROM collections ORDER BY name COLLATE NOCASE").all();
  const reqStmt = db.prepare("SELECT * FROM requests WHERE collection_id = ? ORDER BY updated_at DESC");
  res.json(
    cols.map((c) => ({
      id: c.id,
      name: c.name,
      createdAt: c.created_at,
      requests: reqStmt.all(c.id).map(rowToRequest),
    }))
  );
});

router.post("/", (req, res) => {
  const name = (req.body?.name || "New Collection").trim();
  const info = db.prepare("INSERT INTO collections (name, created_at) VALUES (?, ?)").run(name, now());
  res.json({ id: info.lastInsertRowid, name, createdAt: now(), requests: [] });
});

router.patch("/:id", (req, res) => {
  const name = (req.body?.name || "").trim();
  if (name) db.prepare("UPDATE collections SET name = ? WHERE id = ?").run(name, req.params.id);
  res.json({ ok: true });
});

router.delete("/:id", (req, res) => {
  db.prepare("DELETE FROM requests WHERE collection_id = ?").run(req.params.id);
  db.prepare("DELETE FROM collections WHERE id = ?").run(req.params.id);
  res.json({ ok: true });
});

// ── requests ─────────────────────────────────────────────────────────
router.post("/requests", (req, res) => {
  const b = req.body || {};
  const info = db
    .prepare(
      `INSERT INTO requests
        (collection_id, name, method, url, headers, params, body, body_type, auth_type, auth_data, updated_at)
       VALUES (@collection_id,@name,@method,@url,@headers,@params,@body,@body_type,@auth_type,@auth_data,@updated_at)`
    )
    .run({
      collection_id: b.collectionId ?? null,
      name: b.name || "Untitled",
      method: b.method || "GET",
      url: b.url || "",
      headers: JSON.stringify(b.headers || []),
      params: JSON.stringify(b.params || []),
      body: b.body || "",
      body_type: b.bodyType || "none",
      auth_type: b.authType || "none",
      auth_data: JSON.stringify(b.authData || {}),
      updated_at: now(),
    });
  res.json(rowToRequest(db.prepare("SELECT * FROM requests WHERE id = ?").get(info.lastInsertRowid)));
});

router.put("/requests/:id", (req, res) => {
  const b = req.body || {};
  db.prepare(
    `UPDATE requests SET
       collection_id=@collection_id, name=@name, method=@method, url=@url,
       headers=@headers, params=@params, body=@body, body_type=@body_type,
       auth_type=@auth_type, auth_data=@auth_data, updated_at=@updated_at
     WHERE id=@id`
  ).run({
    id: req.params.id,
    collection_id: b.collectionId ?? null,
    name: b.name || "Untitled",
    method: b.method || "GET",
    url: b.url || "",
    headers: JSON.stringify(b.headers || []),
    params: JSON.stringify(b.params || []),
    body: b.body || "",
    body_type: b.bodyType || "none",
    auth_type: b.authType || "none",
    auth_data: JSON.stringify(b.authData || {}),
    updated_at: now(),
  });
  res.json(rowToRequest(db.prepare("SELECT * FROM requests WHERE id = ?").get(req.params.id)));
});

router.delete("/requests/:id", (req, res) => {
  db.prepare("DELETE FROM requests WHERE id = ?").run(req.params.id);
  res.json({ ok: true });
});

export default router;
