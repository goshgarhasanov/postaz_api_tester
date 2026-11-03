import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { api } from "./lib/api.js";
import Sidebar from "./components/Sidebar.jsx";
import ResponseView from "./components/ResponseView.jsx";
import NetStatus from "./components/NetStatus.jsx";
import KeyValueEditor from "./components/KeyValueEditor.jsx";
import Logo from "./components/Logo.jsx";

const METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"];
const METHOD_COLOR = {
  GET: "#5FD38A", POST: "#FFC24D", PUT: "#5BAEF5",
  PATCH: "#C792EA", DELETE: "#FF6B78", HEAD: "#80CBC4", OPTIONS: "#80CBC4",
};

const blankRequest = () => ({
  id: null,
  name: "Untitled",
  method: "GET",
  url: "",
  headers: [],
  params: [],
  body: "",
  bodyType: "none",
  authType: "none",
  authData: {},
});

export default function App() {
  const [req, setReq] = useState(blankRequest());
  const [resp, setResp] = useState(null);
  const [loading, setLoading] = useState(false);
  const [reqTab, setReqTab] = useState("params");
  const [collections, setCollections] = useState([]);
  const [history, setHistory] = useState([]);
  const [toast, setToast] = useState(null);

  const patch = (p) => setReq((r) => ({ ...r, ...p }));

  const refresh = async () => {
    try {
      const [c, h] = await Promise.all([api.collections(), api.history()]);
      setCollections(c);
      setHistory(h);
    } catch {}
  };
  useEffect(() => {
    refresh();
  }, []);

  const flash = (msg, kind = "info") => {
    setToast({ msg, kind, id: Date.now() });
    setTimeout(() => setToast(null), 2400);
  };

  const send = async () => {
    if (!req.url.trim()) return flash("URL is required", "warn");
    setLoading(true);
    setResp(null);
    try {
      const r = await api.send({
        method: req.method,
        url: req.url,
        headers: req.headers,
        params: req.params,
        body: req.body,
        bodyType: req.bodyType,
        auth: { type: req.authType, data: req.authData },
      });
      setResp(r);
      await api.addHistory({
        method: req.method,
        url: req.url,
        statusCode: r.status,
        durationMs: r.durationMs,
        sizeBytes: r.sizeBytes,
        snapshot: { request: req, response: r },
      });
      refresh();
      if (!r.ok) flash(r.error || "Request failed", "error");
    } catch (e) {
      flash(String(e.message || e), "error");
    } finally {
      setLoading(false);
    }
  };

  const save = async () => {
    try {
      if (req.id) {
        await api.updateRequest(req.id, req);
        flash("Saved", "success");
      } else {
        let col = collections[0];
        if (!col) col = await api.createCollection("My Collection");
        const saved = await api.createRequest({
          ...req,
          name: req.name === "Untitled" ? req.url || "Untitled" : req.name,
          collectionId: col.id,
        });
        setReq(saved);
        flash("Saved", "success");
      }
      refresh();
    } catch (e) {
      flash(String(e.message || e), "error");
    }
  };

  const onKey = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") send();
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
      e.preventDefault();
      save();
    }
  };

  const openRequest = (r) => {
    setReq({ ...blankRequest(), ...r });
    setResp(null);
  };
  const openHistory = (h) => {
    const s = h.snapshot || {};
    if (s.request) setReq({ ...blankRequest(), ...s.request, id: null });
    if (s.response) setResp(s.response);
  };

  return (
    <div className="h-full flex flex-col" onKeyDown={onKey}>
      {/* top chrome */}
      <header className="h-[56px] shrink-0 flex items-center justify-between px-3 sm:px-4 glass border-b border-line relative z-20">
        <div className="absolute inset-x-0 -bottom-px h-px bg-gradient-to-r from-transparent via-brand/40 to-transparent" />
        <Logo size={26} showFlag={true} />
        <NetStatus />
      </header>

      <div className="flex-1 flex min-h-0">
        <Sidebar
          collections={collections}
          history={history}
          onOpenRequest={openRequest}
          onOpenHistory={openHistory}
          onNewCollection={async () => {
            const col = await api.createCollection("New Collection");
            await refresh();
            return col;
          }}
          onDeleteCollection={async (id) => {
            await api.deleteCollection(id);
            refresh();
          }}
          onRenameCollection={async (id, name) => {
            await api.renameCollection(id, name);
            refresh();
          }}
          onDeleteRequest={async (id) => {
            await api.deleteRequest(id);
            refresh();
          }}
          onClearHistory={async () => {
            await api.clearHistory();
            refresh();
          }}
        />

        <main className="flex-1 flex flex-col min-w-0">
          {/* request bar */}
          <div className="p-4 border-b border-line bg-ink-1/70">
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <input
                value={req.name}
                onChange={(e) => patch({ name: e.target.value })}
                onFocus={(e) => req.name === "Untitled" && e.target.select()}
                className="bg-transparent text-[13px] font-semibold text-txt-dim outline-none
                  border-b border-transparent hover:border-line focus:border-brand transition-colors
                  px-0.5 py-0.5 min-w-[120px] max-w-[320px]"
                spellCheck={false}
              />
              {req.id && <span className="text-[10px] text-txt-faint">saved</span>}
              <button
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(toCurl(req));
                    flash("Copied as cURL", "success");
                  } catch {
                    flash("Copy failed", "error");
                  }
                }}
                className="ml-auto btn-ghost h-7 px-3 text-[11px]"
                title="Copy this request as a cURL command"
              >
                Copy as cURL
              </button>
              <button
                onClick={() => {
                  setReq(blankRequest());
                  setResp(null);
                }}
                className="btn-ghost h-7 px-3 text-[11px]"
              >
                + New
              </button>
            </div>
            <div className="flex flex-wrap items-stretch gap-2 sm:gap-2.5">
              <MethodSelect value={req.method} onChange={(m) => patch({ method: m })} />
              <input
                value={req.url}
                onChange={(e) => patch({ url: e.target.value })}
                onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder="https://api.example.com/v1/users"
                className="field flex-1 basis-[200px] min-w-0 h-11"
              />
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={send}
                disabled={loading}
                className="btn-primary h-11 px-5 sm:px-7 text-[13px] disabled:opacity-50 flex-1 sm:flex-none min-w-[88px]"
              >
                {loading ? "Sending…" : "Send"}
              </motion.button>
              <button onClick={save} className="btn-ghost h-11 px-5 text-[13px]">
                Save
              </button>
            </div>

            {/* request tabs */}
            <div className="flex items-center gap-1 mt-3 relative overflow-x-auto no-scrollbar">
              {[
                ["params", "Params"],
                ["headers", "Headers"],
                ["body", "Body"],
                ["auth", "Auth"],
              ].map(([id, label]) => (
                <button
                  key={id}
                  onClick={() => setReqTab(id)}
                  className={`relative px-3.5 py-2 text-[12px] font-semibold rounded-lg transition-colors ${
                    reqTab === id ? "text-white" : "text-txt-mut hover:text-txt-body"
                  }`}
                >
                  {reqTab === id && (
                    <motion.span
                      layoutId="req-tab"
                      className="absolute inset-0 rounded-lg bg-gradient-to-r from-brand/25 to-pink/15 ring-1 ring-brand/30 shadow-glow-sm"
                      transition={{ type: "spring", stiffness: 500, damping: 34 }}
                    />
                  )}
                  <span className="relative">{label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* request editor body */}
          <div className="shrink-0 max-h-[38%] overflow-auto p-4 bg-ink-1/50 border-b border-line">
            <AnimatePresence mode="wait">
              <motion.div
                key={reqTab}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.15 }}
              >
                {reqTab === "params" && (
                  <KeyValueEditor rows={req.params} onChange={(params) => patch({ params })} keyPlaceholder="Param" />
                )}
                {reqTab === "headers" && (
                  <KeyValueEditor rows={req.headers} onChange={(headers) => patch({ headers })} keyPlaceholder="Header" />
                )}
                {reqTab === "body" && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-[12px] text-txt-mut">Body type:</span>
                      <Segmented
                        options={["none", "json", "raw", "urlencoded"]}
                        value={req.bodyType}
                        onChange={(bodyType) => patch({ bodyType })}
                      />
                      {req.bodyType === "json" && req.body.trim() && (
                        <button
                          onClick={() => {
                            try {
                              patch({ body: JSON.stringify(JSON.parse(req.body), null, 2) });
                              flash("Formatted", "success");
                            } catch {
                              flash("Invalid JSON", "error");
                            }
                          }}
                          className="btn-ghost h-8 px-3 text-[11.5px] ml-auto"
                        >
                          Format JSON
                        </button>
                      )}
                    </div>
                    {req.bodyType !== "none" && (
                      <textarea
                        value={req.body}
                        onChange={(e) => patch({ body: e.target.value })}
                        placeholder={req.bodyType === "json" ? '{\n  "key": "value"\n}' : "request body"}
                        spellCheck={false}
                        className="field w-full h-40 py-3 font-mono resize-none leading-relaxed"
                      />
                    )}
                  </div>
                )}
                {reqTab === "auth" && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-[12px] text-txt-mut">Auth type:</span>
                      <Segmented
                        options={["none", "bearer", "basic", "apikey"]}
                        value={req.authType}
                        onChange={(authType) => patch({ authType, authData: {} })}
                      />
                    </div>
                    <AuthFields type={req.authType} data={req.authData} onChange={(authData) => patch({ authData })} />
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </div>

          {/* response */}
          <div className="flex-1 min-h-0">
            <ResponseView resp={resp} loading={loading} />
          </div>
        </main>
      </div>

      {/* toast */}
      <AnimatePresence>
        {toast && (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: 24, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 24, scale: 0.96 }}
            transition={{ type: "spring", stiffness: 400, damping: 28 }}
            className="fixed left-1/2 -translate-x-1/2 bottom-8 px-5 py-3 rounded-xl text-[13px] font-medium shadow-card border z-50"
            style={toastStyle(toast.kind)}
          >
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── method dropdown (animated, pointer cursor) ────────────────────────
function MethodSelect({ value, onChange }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    const h = (e) => ref.current && !ref.current.contains(e.target) && setOpen(false);
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);
  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="h-11 min-w-[112px] px-4 rounded-lg bg-ink-3 border border-line hover:border-brand
          flex items-center justify-between gap-2 font-extrabold text-[12px] tracking-wider cursor-pointer
          transition-colors"
        style={{ color: METHOD_COLOR[value] }}
      >
        {value}
        <motion.span animate={{ rotate: open ? 180 : 0 }} className="text-txt-mut text-[10px]">
          ▼
        </motion.span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.97 }}
            transition={{ duration: 0.14 }}
            className="absolute z-30 mt-1.5 w-full rounded-lg bg-ink-3 border border-line-hover p-1.5 shadow-card"
          >
            {METHODS.map((m) => (
              <button
                key={m}
                onClick={() => {
                  onChange(m);
                  setOpen(false);
                }}
                className="w-full text-left px-3 py-2 rounded-md font-extrabold text-[12px] tracking-wider
                  cursor-pointer hover:bg-ink-4 transition-colors"
                style={{ color: METHOD_COLOR[m] }}
              >
                {m}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Segmented({ options, value, onChange }) {
  return (
    <div className="inline-flex gap-1 p-1 rounded-lg bg-ink-2 border border-line">
      {options.map((o) => (
        <button
          key={o}
          onClick={() => onChange(o)}
          className={`relative px-3 py-1.5 rounded-md text-[11.5px] font-semibold cursor-pointer transition-colors ${
            value === o ? "text-white" : "text-txt-mut hover:text-txt-body"
          }`}
        >
          {value === o && (
            <motion.span layoutId={`seg-${options.join()}`} className="absolute inset-0 rounded-md bg-brand/80" />
          )}
          <span className="relative">{o}</span>
        </button>
      ))}
    </div>
  );
}

function AuthFields({ type, data, onChange }) {
  if (type === "none") return <p className="text-[12px] text-txt-faint">No authentication for this request.</p>;
  const set = (p) => onChange({ ...data, ...p });
  if (type === "bearer")
    return (
      <input className="field w-full h-10" placeholder="Token" value={data.token || ""} onChange={(e) => set({ token: e.target.value })} />
    );
  if (type === "basic")
    return (
      <div className="flex gap-2">
        <input className="field flex-1 h-10" placeholder="Username" value={data.username || ""} onChange={(e) => set({ username: e.target.value })} />
        <input className="field flex-1 h-10" placeholder="Password" type="password" value={data.password || ""} onChange={(e) => set({ password: e.target.value })} />
      </div>
    );
  if (type === "apikey")
    return (
      <div className="flex gap-2">
        <input className="field flex-1 h-10" placeholder="Key" value={data.key || ""} onChange={(e) => set({ key: e.target.value })} />
        <input className="field flex-1 h-10" placeholder="Value" value={data.value || ""} onChange={(e) => set({ value: e.target.value })} />
      </div>
    );
  return null;
}

// Build a cURL command string from the current request state.
function toCurl(req) {
  let url = (req.url || "").trim();
  if (url && !/^https?:\/\//i.test(url)) url = "https://" + url;
  try {
    const u = new URL(url);
    (req.params || []).forEach((p) => {
      if (p && p.enabled !== false && (p.key || "").trim()) u.searchParams.append(p.key, p.value ?? "");
    });
    url = u.toString();
  } catch {}

  const q = (s) => `'${String(s).replace(/'/g, "'\\''")}'`;
  const parts = [`curl -X ${req.method} ${q(url)}`];

  (req.headers || []).forEach((h) => {
    if (h && h.enabled !== false && (h.key || "").trim()) parts.push(`-H ${q(`${h.key}: ${h.value ?? ""}`)}`);
  });

  const { authType, authData = {} } = req;
  if (authType === "bearer" && authData.token) parts.push(`-H ${q(`Authorization: Bearer ${authData.token}`)}`);
  else if (authType === "basic") parts.push(`-u ${q(`${authData.username || ""}:${authData.password || ""}`)}`);
  else if (authType === "apikey" && authData.key) parts.push(`-H ${q(`${authData.key}: ${authData.value || ""}`)}`);

  if (!["GET", "HEAD"].includes(req.method) && req.bodyType !== "none" && req.body) {
    if (req.bodyType === "json") parts.push(`-H ${q("Content-Type: application/json")}`);
    parts.push(`--data ${q(req.body)}`);
  }
  return parts.join(" \\\n  ");
}

const toastStyle = (kind) =>
  ({
    info: { background: "#202130", color: "#cfd2ff", borderColor: "#3a3d70" },
    success: { background: "#16322a", color: "#7fe6b3", borderColor: "#1f5e48" },
    error: { background: "#321a20", color: "#ff8090", borderColor: "#6a2730" },
    warn: { background: "#322a1a", color: "#f5c97a", borderColor: "#6b4e20" },
  }[kind] || { background: "#202130", color: "#cfd2ff", borderColor: "#3a3d70" });
