// Environments — named sets of {{variables}} with one active at a time.
import { Router } from "express";
import db, { parse } from "../db.js";

const router = Router();

const rowToEnv = (e) => ({
  id: e.id,
  name: e.name,
  variables: parse(e.variables, {}),
  active: !!e.active,
});

router.get("/", (_req, res) => {
  res.json(db.prepare("SELECT * FROM environments ORDER BY name COLLATE NOCASE").all().map(rowToEnv));
});

router.post("/", (req, res) => {
  const b = req.body || {};
  const info = db
    .prepare("INSERT INTO environments (name, variables, active) VALUES (?, ?, 0)")
    .run((b.name || "New Environment").trim(), JSON.stringify(b.variables || {}));
  res.json(rowToEnv(db.prepare("SELECT * FROM environments WHERE id = ?").get(info.lastInsertRowid)));
});

router.put("/:id", (req, res) => {
  const b = req.body || {};
  db.prepare("UPDATE environments SET name = ?, variables = ? WHERE id = ?").run(
    (b.name || "").trim(),
    JSON.stringify(b.variables || {}),
    req.params.id
  );
  res.json(rowToEnv(db.prepare("SELECT * FROM environments WHERE id = ?").get(req.params.id)));
});

router.post("/:id/activate", (req, res) => {
  db.prepare("UPDATE environments SET active = 0").run();
  db.prepare("UPDATE environments SET active = 1 WHERE id = ?").run(req.params.id);
  res.json({ ok: true });
});

router.post("/deactivate", (_req, res) => {
  db.prepare("UPDATE environments SET active = 0").run();
  res.json({ ok: true });
});

router.delete("/:id", (req, res) => {
  db.prepare("DELETE FROM environments WHERE id = ?").run(req.params.id);
  res.json({ ok: true });
});

export default router;
