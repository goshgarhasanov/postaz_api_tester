/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: "#FF6C37", hover: "#FF8557", press: "#E55A2B" },
        // deep slate-violet ink scale — colder, richer, with a faint blue cast
        ink: {
          0: "#0B0C12", 1: "#111320", 2: "#171A2A",
          3: "#1E2235", 4: "#272C44", 5: "#333A58",
        },
        line: { DEFAULT: "#2A2F47", hover: "#3B4267" },
        // high-contrast, vivid text for dark mode — much brighter, far less grey
        txt: { hi: "#FFFFFF", body: "#FBFCFF", dim: "#EAEEFF", mut: "#CFD5F2", faint: "#A6AEDC" },
        // punchier, more saturated semantic colours
        ok: "#4ADE80", info: "#60A5FA", warn: "#FBBF24", err: "#FB7185",
        violet: "#A78BFA", pink: "#F472B6", cyan: "#22D3EE",
        azblue: "#00B5E2", azred: "#EF3340", azgreen: "#4FA72E",
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Cascadia Code", "Consolas", "monospace"],
      },
      boxShadow: {
        glow: "0 0 0 3px rgba(255,108,55,0.25), 0 8px 24px -6px rgba(255,108,55,0.35)",
        "glow-sm": "0 0 14px -2px rgba(255,108,55,0.45)",
        card: "0 10px 40px -8px rgba(0,0,0,0.55)",
        neon: "0 0 20px -4px rgba(167,139,250,0.5)",
      },
      backgroundImage: {
        "brand-grad": "linear-gradient(135deg, #FF9A6B 0%, #FF6C37 45%, #E25421 100%)",
        "aurora":
          "radial-gradient(60% 55% at 15% 0%, rgba(255,108,55,0.16) 0%, transparent 60%)," +
          "radial-gradient(55% 55% at 100% 10%, rgba(99,102,241,0.18) 0%, transparent 55%)," +
          "radial-gradient(50% 50% at 50% 100%, rgba(34,211,238,0.10) 0%, transparent 60%)",
      },
    },
  },
  plugins: [],
};
