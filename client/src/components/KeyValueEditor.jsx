import { AnimatePresence, motion } from "framer-motion";

// Editable key/value rows (headers / query params). A trailing blank row is
// always kept so the user can just start typing. Toggle enables/disables a row.
export default function KeyValueEditor({ rows, onChange, keyPlaceholder = "Key" }) {
  const list = [...rows, { key: "", value: "", enabled: true }];

  const setCell = (i, patch) => {
    if (i < rows.length) {
      onChange(rows.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
    } else {
      onChange([...rows, { key: "", value: "", enabled: true, ...patch }]);
    }
  };

  const remove = (i) => onChange(rows.filter((_, idx) => idx !== i));

  return (
    <div className="rounded-xl border border-line overflow-hidden">
      <div className="grid grid-cols-[40px_1fr_1fr_40px] bg-ink-2 text-[10.5px] font-bold uppercase tracking-wider text-txt-mut">
        <div className="px-3 py-2.5" />
        <div className="px-3 py-2.5">{keyPlaceholder}</div>
        <div className="px-3 py-2.5">Value</div>
        <div className="px-3 py-2.5" />
      </div>
      <AnimatePresence initial={false}>
        {list.map((row, i) => {
          const isBlank = i >= rows.length;
          return (
            <motion.div
              key={i}
              layout
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.18 }}
              className="grid grid-cols-[40px_1fr_1fr_40px] items-center border-t border-line/60 hover:bg-white/[0.02]"
            >
              <button
                onClick={() => !isBlank && setCell(i, { enabled: !row.enabled })}
                className="flex items-center justify-center py-2"
                title="Enable / disable"
              >
                <span
                  className={`w-9 h-5 rounded-full p-0.5 transition-colors ${
                    row.enabled !== false && !isBlank ? "bg-brand" : "bg-ink-5"
                  }`}
                >
                  <motion.span
                    layout
                    className="block w-4 h-4 rounded-full bg-white"
                    animate={{ x: row.enabled !== false && !isBlank ? 16 : 0 }}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  />
                </span>
              </button>
              <input
                value={row.key || ""}
                onChange={(e) => setCell(i, { key: e.target.value })}
                placeholder={keyPlaceholder}
                className="bg-transparent px-3 py-2.5 text-[13px] outline-none placeholder:text-txt-faint"
              />
              <input
                value={row.value || ""}
                onChange={(e) => setCell(i, { value: e.target.value })}
                placeholder="Value"
                className="bg-transparent px-3 py-2.5 text-[13px] outline-none placeholder:text-txt-faint"
              />
              <button
                onClick={() => !isBlank && remove(i)}
                className={`py-2 text-txt-faint hover:text-err transition-colors ${
                  isBlank ? "invisible" : ""
                }`}
                title="Remove"
              >
                ✕
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
