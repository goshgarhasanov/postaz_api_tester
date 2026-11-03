import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

const methodColor = (m) =>
  ({
    GET: "#5FD38A",
    POST: "#FFC24D",
    PUT: "#5BAEF5",
    PATCH: "#C792EA",
    DELETE: "#FF6B78",
  }[m] || "#80CBC4");

export default function Sidebar({
  collections,
  history,
  onOpenRequest,
  onOpenHistory,
  onNewCollection,
  onDeleteCollection,
  onRenameCollection,
  onDeleteRequest,
  onClearHistory,
}) {
  const [tab, setTab] = useState("collections");
  const [open, setOpen] = useState({});
  const [editing, setEditing] = useState(null); // collection id being renamed
  const [draft, setDraft] = useState("");
  const inputRef = useRef(null);

  useEffect(() => {
    if (editing != null && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  const startRename = (c) => {
    setEditing(c.id);
    setDraft(c.name);
  };
  const commitRename = () => {
    const name = draft.trim();
    if (editing != null && name) onRenameCollection(editing, name);
    setEditing(null);
  };

  return (
    <aside className="hidden sm:flex w-[236px] lg:w-[290px] shrink-0 flex-col bg-ink-2/60 backdrop-blur-md border-r border-line">
      <div className="px-4 h-11 flex items-center border-b border-line">
        <span className="text-[10.5px] font-bold uppercase tracking-[0.18em] text-txt-mut">Workspace</span>
      </div>

      {/* tab switch */}
      <div className="flex gap-1 p-2">
        {[
          ["collections", "Collections"],
          ["history", "History"],
        ].map(([id, label]) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`relative flex-1 py-2 rounded-lg text-[12px] font-semibold transition-colors ${
              tab === id ? "text-white" : "text-txt-mut hover:text-txt-body hover:bg-ink-3"
            }`}
          >
            {tab === id && (
              <motion.span
                layoutId="side-tab"
                className="absolute inset-0 rounded-lg bg-gradient-to-r from-brand/25 to-pink/15 ring-1 ring-brand/30 shadow-glow-sm"
                transition={{ type: "spring", stiffness: 500, damping: 34 }}
              />
            )}
            <span className="relative">{label}</span>
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto px-2 pb-3">
        {tab === "collections" ? (
          <>
            <button
              onClick={async () => {
                const col = await onNewCollection();
                if (col && col.id != null) {
                  setOpen((o) => ({ ...o, [col.id]: true }));
                  setEditing(col.id);
                  setDraft(col.name || "");
                }
              }}
              className="btn-ghost w-full py-2 text-[12px] mb-2"
            >
              + New Collection
            </button>
            <AnimatePresence initial={false}>
              {collections.map((c) => (
                <motion.div
                  key={c.id}
                  layout
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mb-1"
                >
                  <div
                    className="group flex items-center gap-2 px-2.5 py-2 rounded-lg hover:bg-ink-3 cursor-pointer"
                    onClick={() => editing !== c.id && setOpen((o) => ({ ...o, [c.id]: !o[c.id] }))}
                  >
                    <motion.span animate={{ rotate: open[c.id] ? 90 : 0 }} className="text-txt-mut text-xs">
                      ▶
                    </motion.span>
                    {editing === c.id ? (
                      <input
                        ref={inputRef}
                        value={draft}
                        onChange={(e) => setDraft(e.target.value)}
                        onClick={(e) => e.stopPropagation()}
                        onBlur={commitRename}
                        onKeyDown={(e) => {
                          e.stopPropagation();
                          if (e.key === "Enter") commitRename();
                          if (e.key === "Escape") setEditing(null);
                        }}
                        className="flex-1 min-w-0 bg-ink-4 border border-brand rounded-md px-2 py-1 text-[13px]
                          text-txt-body outline-none"
                        spellCheck={false}
                      />
                    ) : (
                      <span
                        className="flex-1 text-[13px] font-medium truncate"
                        onDoubleClick={(e) => {
                          e.stopPropagation();
                          startRename(c);
                        }}
                        title="Double-click to rename"
                      >
                        {c.name}
                      </span>
                    )}
                    {editing !== c.id && (
                      <>
                        <span className="text-[10px] text-txt-faint group-hover:hidden">{c.requests.length}</span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            startRename(c);
                          }}
                          className="hidden group-hover:block text-txt-faint hover:text-brand transition text-[12px]"
                          title="Rename"
                        >
                          ✎
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteCollection(c.id);
                          }}
                          className="opacity-0 group-hover:opacity-100 text-txt-faint hover:text-err transition"
                          title="Delete"
                        >
                          ✕
                        </button>
                      </>
                    )}
                  </div>
                  <AnimatePresence initial={false}>
                    {open[c.id] && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden ml-5"
                      >
                        {c.requests.map((r) => (
                          <div
                            key={r.id}
                            onClick={() => onOpenRequest(r)}
                            className="group flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-ink-3 cursor-pointer"
                          >
                            <span
                              className="text-[9.5px] font-bold w-10 shrink-0"
                              style={{ color: methodColor(r.method) }}
                            >
                              {r.method}
                            </span>
                            <span className="flex-1 text-[12.5px] text-txt-dim truncate">{r.name}</span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onDeleteRequest(r.id);
                              }}
                              className="opacity-0 group-hover:opacity-100 text-txt-faint hover:text-err transition"
                            >
                              ✕
                            </button>
                          </div>
                        ))}
                        {c.requests.length === 0 && (
                          <div className="px-2.5 py-1.5 text-[11.5px] text-txt-faint">empty</div>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </AnimatePresence>
          </>
        ) : (
          <>
            {history.length > 0 && (
              <button onClick={onClearHistory} className="btn-ghost w-full py-2 text-[12px] mb-2 hover:!border-err hover:!text-err">
                Clear History
              </button>
            )}
            <AnimatePresence initial={false}>
              {history.map((h) => (
                <motion.div
                  key={h.id}
                  layout
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, height: 0 }}
                  onClick={() => onOpenHistory(h)}
                  className="flex items-center gap-2 px-2.5 py-2 rounded-lg hover:bg-ink-3 cursor-pointer mb-1"
                >
                  <span className="text-[9.5px] font-bold w-10 shrink-0" style={{ color: methodColor(h.method) }}>
                    {h.method}
                  </span>
                  <span className="flex-1 text-[12px] text-txt-dim truncate">{h.url}</span>
                  <span className="text-[10px] text-txt-faint">{h.statusCode || "—"}</span>
                </motion.div>
              ))}
            </AnimatePresence>
            {history.length === 0 && (
              <div className="px-3 py-6 text-center text-[12px] text-txt-faint">No history yet.</div>
            )}
          </>
        )}
      </div>
    </aside>
  );
}
