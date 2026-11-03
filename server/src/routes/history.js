// Request history — a rolling log of every send.
import { Router } from "express";
import db, { now, parse } from "../db.js";

const router = Router();

router.get("/", (_req, res) => {
  const rows = db.prepare("SELECT * FROM history ORDER BY created_at DESC LIMIT 200").all();
  res.json(
    rows.map((h) => ({
      id: h.id,
      method: h.method,
      url: h.url,
      statusCode: h.status_code,
      durationMs: h.duration_ms,
      sizeBytes: h.size_bytes,
      snapshot: parse(h.snapshot, {}),
      createdAt: h.created_at,
    }))
  );
});

router.post("/", (req, res) => {
  const b = req.body || {};
  const info = db
    .prepare(
      `INSERT INTO history (method, url, status_code, duration_ms, size_bytes, snapshot, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    )
    .run(
      b.method || "GET",
      b.url || "",
      b.statusCode ?? 0,
      b.durationMs ?? 0,
      b.sizeBytes ?? 0,
      JSON.stringify(b.snapshot || {}),
      now()
    );
  res.json({ id: info.lastInsertRowid });
});

router.delete("/", (_req, res) => {
  db.prepare("DELETE FROM history").run();
  res.json({ ok: true });
});

export default router;
