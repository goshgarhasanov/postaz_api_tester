// Postaz backend — Express app wiring the proxy + persistence routes,
// plus a tiny net-latency probe for the top-bar connection indicator.
import express from "express";
import cors from "cors";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { existsSync } from "node:fs";

import proxy from "./routes/proxy.js";
import collections from "./routes/collections.js";
import history from "./routes/history.js";
import environments from "./routes/environments.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = process.env.PORT || 5050;

const app = express();
app.use(cors());
app.use(express.json({ limit: "25mb" }));
app.use(express.text({ type: "text/*", limit: "25mb" }));

app.use("/api", proxy);
app.use("/api/collections", collections);
app.use("/api/history", history);
app.use("/api/environments", environments);

// ── net latency probe (for the colour-coded connection pill) ──────────
app.get("/api/net/ping", async (_req, res) => {
  const started = performance.now();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 3000);
  try {
    await fetch("https://www.gstatic.com/generate_204", {
      method: "GET",
      signal: controller.signal,
      cache: "no-store",
    });
    res.json({ online: true, ms: Math.round(performance.now() - started) });
  } catch {
    res.json({ online: false, ms: -1 });
  } finally {
    clearTimeout(timer);
  }
});

app.get("/api/health", (_req, res) => res.json({ ok: true }));

// ── serve the built client when a production build exists ─────────────
// Re-checked per request so a build produced after boot is picked up.
const dist = join(__dirname, "..", "..", "client", "dist");
app.use(express.static(dist));
app.get("*", (req, res, next) => {
  if (req.path.startsWith("/api/")) return next();
  const index = join(dist, "index.html");
  if (existsSync(index)) return res.sendFile(index);
  next();
});

app.listen(PORT, () => {
  console.log(`Postaz server listening on http://localhost:${PORT}`);
});
