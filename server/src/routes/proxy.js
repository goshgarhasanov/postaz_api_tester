// The engine: execute an outbound HTTP request on behalf of the browser.
// A browser can't call arbitrary cross-origin APIs (CORS); the backend can.
// Accepts a fully-resolved request and returns a normalised response.
import { Router } from "express";

const router = Router();

function buildUrl(rawUrl, params = []) {
  let url = (rawUrl || "").trim();
  if (!url) throw new Error("URL is empty");
  if (!/^https?:\/\//i.test(url)) url = "https://" + url;
  const u = new URL(url);
  for (const p of params) {
    if (p && p.enabled !== false && (p.key || "").trim()) {
      u.searchParams.append(p.key, p.value ?? "");
    }
  }
  return u.toString();
}

function buildHeaders(headers = [], auth = { type: "none", data: {} }) {
  const h = {};
  for (const item of headers) {
    if (item && item.enabled !== false && (item.key || "").trim()) {
      h[item.key] = item.value ?? "";
    }
  }
  const { type, data = {} } = auth || {};
  if (type === "bearer" && data.token) {
    h["Authorization"] = `Bearer ${data.token}`;
  } else if (type === "basic") {
    const raw = `${data.username || ""}:${data.password || ""}`;
    h["Authorization"] = "Basic " + Buffer.from(raw).toString("base64");
  } else if (type === "apikey" && data.key) {
    if ((data.in || "header") === "header") h[data.key] = data.value || "";
  }
  return h;
}

router.post("/send", async (req, res) => {
  const {
    method = "GET",
    url = "",
    headers = [],
    params = [],
    body = "",
    bodyType = "none",
    auth = { type: "none", data: {} },
  } = req.body || {};

  let finalUrl;
  try {
    finalUrl = buildUrl(url, params);
  } catch (e) {
    return res.json({ ok: false, error: e.message, status: 0 });
  }

  const outHeaders = buildHeaders(headers, auth);
  let payload;
  if (!["GET", "HEAD"].includes(method.toUpperCase()) && bodyType !== "none") {
    payload = body;
    if (bodyType === "json" && !outHeaders["Content-Type"] && !outHeaders["content-type"]) {
      outHeaders["Content-Type"] = "application/json";
    }
    if (bodyType === "urlencoded" && !outHeaders["Content-Type"]) {
      outHeaders["Content-Type"] = "application/x-www-form-urlencoded";
    }
  }

  const started = performance.now();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60_000);
  try {
    const resp = await fetch(finalUrl, {
      method: method.toUpperCase(),
      headers: outHeaders,
      body: payload,
      redirect: "follow",
      signal: controller.signal,
    });
    const buf = Buffer.from(await resp.arrayBuffer());
    const durationMs = Math.round(performance.now() - started);
    const respHeaders = {};
    resp.headers.forEach((v, k) => (respHeaders[k] = v));

    res.json({
      ok: true,
      status: resp.status,
      reason: resp.statusText || "",
      headers: respHeaders,
      bodyText: buf.toString("utf-8"),
      contentType: resp.headers.get("content-type") || "",
      durationMs,
      sizeBytes: buf.length,
      finalUrl: resp.url || finalUrl,
    });
  } catch (e) {
    const durationMs = Math.round(performance.now() - started);
    const msg = e.name === "AbortError" ? "Request timed out (60s)" : (e.cause?.message || e.message);
    res.json({ ok: false, error: msg, status: 0, durationMs });
  } finally {
    clearTimeout(timeout);
  }
});

export default router;
