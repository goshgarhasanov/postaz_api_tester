import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { api } from "../lib/api.js";

// Colour-coded internet/latency pill. Polls the backend probe every few
// seconds; the dot and number turn green → amber → red as latency rises.
export default function NetStatus() {
  const [state, setState] = useState({ online: null, ms: -1 });

  useEffect(() => {
    let alive = true;
    const check = async () => {
      try {
        const r = await api.ping();
        if (alive) setState(r);
      } catch {
        if (alive) setState({ online: false, ms: -1 });
      }
    };
    check();
    const id = setInterval(check, 6000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  let color = "#63656F";
  let label = "…";
  if (state.online === false) {
    color = "#FF6B78";
    label = "Offline";
  } else if (state.online) {
    color = state.ms <= 100 ? "#5FD38A" : state.ms <= 300 ? "#FFC24D" : "#FF6B78";
    label = `${state.ms} ms`;
  }

  return (
    <div
      className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-ink-3/60 border border-line"
      title="Internet connection & latency"
    >
      <motion.span
        key={color}
        initial={{ scale: 0.6, opacity: 0.4 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 500, damping: 20 }}
        className="inline-block w-2.5 h-2.5 rounded-full"
        style={{ background: color, boxShadow: `0 0 10px ${color}` }}
      />
      <span className="font-mono text-[11px] font-bold tracking-wide text-txt-dim">{label}</span>
    </div>
  );
}
