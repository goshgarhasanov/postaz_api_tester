import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

const humanSize = (n = 0) => {
  const u = ["B", "KB", "MB", "GB"];
  let s = n;
  for (const unit of u) {
    if (s < 1024 || unit === "GB") return unit === "B" ? `${Math.round(s)} ${unit}` : `${s.toFixed(1)} ${unit}`;
    s /= 1024;
  }
};

const statusTone = (code) => {
  if (code >= 200 && code < 300) return { bg: "rgba(95,211,138,0.14)", fg: "#5FD38A" };
  if (code >= 300 && code < 400) return { bg: "rgba(91,174,245,0.14)", fg: "#5BAEF5" };
  if (code >= 400 && code < 500) return { bg: "rgba(255,194,77,0.14)", fg: "#FFC24D" };
  if (code >= 500) return { bg: "rgba(255,107,120,0.14)", fg: "#FF6B78" };
  return { bg: "rgba(255,107,120,0.14)", fg: "#FF6B78" };
};

function highlightJson(text) {
  // escape then colourise — returns HTML
  const esc = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return esc.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/g,
    (m) => {
      let cls = "#FFC24D"; // number
      if (/^"/.test(m)) cls = /:$/.test(m) ? "#5BAEF5" : "#5FD38A";
      else if (/true|false|null/.test(m)) cls = "#FF6B78";
      return `<span style="color:${cls}">${m}</span>`;
    }
  );
}

const isHtml = (resp) => {
  const ct = (resp?.contentType || "").toLowerCase();
  if (ct.includes("text/html") || ct.includes("xhtml")) return true;
  const head = (resp?.bodyText || "").trimStart().slice(0, 200).toLowerCase();
  return head.startsWith("<!doctype html") || head.startsWith("<html");
};

export default function ResponseView({ resp, loading }) {
  const [tab, setTab] = useState("body");
  const [copied, setCopied] = useState(false);
  const html = resp && isHtml(resp);

  const copy = async () => {
    const text =
      tab === "headers"
        ? Object.entries(resp?.headers || {}).map(([k, v]) => `${k}: ${v}`).join("\n")
        : tab === "raw"
        ? resp?.bodyText || ""
        : prettyBody || resp?.bodyText || "";
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {}
  };

  const prettyBody = useMemo(() => {
    if (!resp?.bodyText) return "";
    if ((resp.contentType || "").includes("json")) {
      try {
        return JSON.stringify(JSON.parse(resp.bodyText), null, 2);
      } catch {}
    }
    return resp.bodyText;
  }, [resp]);

  const tabs = [
    ["body", "Body"],
    ["headers", "Headers"],
    ["raw", "Raw"],
    ["preview", "Preview"],
  ];

  return (
    <div className="flex flex-col h-full bg-ink-1/40">
      {/* meta bar */}
      <div className="flex items-center gap-4 px-5 h-12 shrink-0 border-b border-line">
        {resp ? (
          resp.ok ? (
            <StatusPill code={resp.status} reason={resp.reason} />
          ) : (
            <span className="chip" style={{ background: "rgba(255,107,120,0.14)", color: "#FF6B78" }}>
              ERROR
            </span>
          )
        ) : (
          <span className="chip bg-ink-4 text-txt-mut">—</span>
        )}
        {resp && (
          <>
            <Meta icon="⏱" text={`${resp.durationMs ?? 0} ms`} />
            <Meta icon="⇣" text={resp.ok ? humanSize(resp.sizeBytes) : "—"} />
          </>
        )}
        {resp && resp.ok && tab !== "preview" && (
          <button
            onClick={copy}
            className="ml-auto btn-ghost h-7 px-3 text-[11px]"
            title="Copy to clipboard"
          >
            {copied ? "Copied ✓" : "Copy"}
          </button>
        )}
      </div>

      {/* tabs */}
      <div className="flex items-center gap-1 px-4 shrink-0 border-b border-line relative">
        {tabs.map(([id, label]) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`relative px-4 py-3 text-[12px] font-semibold transition-colors ${
              tab === id ? "text-white" : "text-txt-mut hover:text-txt-body"
            }`}
          >
            {label}
            {tab === id && (
              <motion.span
                layoutId="resp-underline"
                className="absolute left-2 right-2 -bottom-px h-0.5 bg-brand rounded-full"
                transition={{ type: "spring", stiffness: 500, damping: 34 }}
              />
            )}
          </button>
        ))}
      </div>

      {/* body */}
      <div className="relative flex-1 min-h-0">
        <AnimatePresence>
          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-ink-1/70 backdrop-blur-sm"
            >
              <motion.span
                className="w-10 h-10 rounded-full border-[3px] border-ink-5 border-t-brand"
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 0.8, ease: "linear" }}
              />
              <span className="text-[13px] text-txt-dim">Sending request…</span>
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence mode="wait">
          <motion.div
            key={tab + (resp ? resp.durationMs : "e")}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.16 }}
            className="absolute inset-0 overflow-auto p-4"
          >
            {!resp && <Empty />}

            {resp && !resp.ok && (
              <pre className="font-mono text-[12.5px] text-err whitespace-pre-wrap">{resp.error}</pre>
            )}

            {resp && resp.ok && tab === "body" && (
              <pre
                className="font-mono text-[12.5px] leading-relaxed whitespace-pre text-txt-body"
                dangerouslySetInnerHTML={{
                  __html: (resp.contentType || "").includes("json")
                    ? highlightJson(prettyBody)
                    : prettyBody.replace(/&/g, "&amp;").replace(/</g, "&lt;"),
                }}
              />
            )}

            {resp && resp.ok && tab === "headers" && (
              <div className="rounded-xl border border-line overflow-hidden">
                {Object.entries(resp.headers || {}).map(([k, v], i) => (
                  <div
                    key={k}
                    className={`grid grid-cols-[minmax(160px,0.4fr)_1fr] gap-3 px-4 py-2.5 text-[12.5px] ${
                      i ? "border-t border-line/60" : ""
                    }`}
                  >
                    <span className="font-semibold text-txt-dim break-all">{k}</span>
                    <span className="text-txt-mut break-all">{v}</span>
                  </div>
                ))}
              </div>
            )}

            {resp && resp.ok && tab === "raw" && (
              <pre className="font-mono text-[12.5px] whitespace-pre-wrap text-txt-body">
                {resp.bodyText}
              </pre>
            )}

            {tab === "preview" &&
              (resp && resp.ok && html ? (
                <iframe
                  title="preview"
                  sandbox=""
                  srcDoc={resp.bodyText}
                  className="w-full h-full min-h-[300px] rounded-xl border border-line bg-white"
                />
              ) : (
                <div className="h-full flex items-center justify-center text-txt-faint text-[13px]">
                  Preview is available for HTML responses.
                </div>
              ))}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}

function StatusPill({ code, reason }) {
  const t = statusTone(code);
  return (
    <motion.span
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 400, damping: 22 }}
      className="chip"
      style={{ background: t.bg, color: t.fg }}
    >
      {code} {reason}
    </motion.span>
  );
}

const Meta = ({ icon, text }) => (
  <span className="flex items-center gap-1.5 text-[12px] text-txt-mut">
    <span className="text-txt-faint">{icon}</span>
    {text}
  </span>
);

const Empty = () => (
  <div className="h-full flex flex-col items-center justify-center gap-2 text-txt-faint">
    <span className="text-4xl opacity-40">✈</span>
    <span className="text-[13px]">Send a request to see the response here.</span>
  </div>
);
