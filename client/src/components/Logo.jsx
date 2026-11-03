// Postaz logomark — a refined, professional lockup:
//   · a squircle "send" mark (orange gradient, soft depth, white paper plane)
//   · the wordmark "POST" (white) + "AZ" (orange)
//   · a crisp Azerbaijan flag chip (blue/red/green bands + white crescent and
//     eight-pointed star) as a national badge
function AzFlag({ h = 18 }) {
  const w = h * 1.7;
  // 8-pointed star points around (sx, sy)
  const sx = 40;
  const sy = 15;
  const R = 4.1;
  const r = R * 0.46;
  const pts = [];
  for (let i = 0; i < 16; i++) {
    const a = (-90 + i * 22.5) * (Math.PI / 180);
    const rad = i % 2 === 0 ? R : r;
    pts.push(`${(sx + rad * Math.cos(a)).toFixed(2)},${(sy + rad * Math.sin(a)).toFixed(2)}`);
  }
  return (
    <svg
      width={w}
      height={h}
      viewBox="0 0 60 30"
      className="shrink-0 rounded-[3px]"
      style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.35)", border: "1px solid rgba(255,255,255,0.12)" }}
    >
      <defs>
        <clipPath id="az-clip">
          <rect x="0" y="0" width="60" height="30" rx="3" />
        </clipPath>
      </defs>
      <g clipPath="url(#az-clip)">
        <rect x="0" y="0" width="60" height="10" fill="#00B5E2" />
        <rect x="0" y="10" width="60" height="10" fill="#EF3340" />
        <rect x="0" y="20" width="60" height="10" fill="#4FA72E" />
        {/* crescent: white disc carved by a red disc shifted right */}
        <circle cx="26.5" cy="15" r="6" fill="#ffffff" />
        <circle cx="29" cy="15" r="5" fill="#EF3340" />
        {/* eight-pointed star */}
        <polygon points={pts.join(" ")} fill="#ffffff" />
      </g>
    </svg>
  );
}

export default function Logo({ size = 30, showWordmark = true, showFlag = true }) {
  return (
    <div className="flex items-center gap-2.5 select-none">
      <svg
        width={size}
        height={size}
        viewBox="0 0 48 48"
        fill="none"
        style={{ filter: "drop-shadow(0 4px 10px rgba(255,108,55,0.28))" }}
        className="shrink-0"
      >
        <defs>
          <linearGradient id="pz-mark" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#FF9A6B" />
            <stop offset="0.5" stopColor="#FF6C37" />
            <stop offset="1" stopColor="#E25421" />
          </linearGradient>
          <linearGradient id="pz-sheen" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#ffffff" stopOpacity="0.35" />
            <stop offset="0.45" stopColor="#ffffff" stopOpacity="0" />
          </linearGradient>
        </defs>
        <rect x="2" y="2" width="44" height="44" rx="13.5" fill="url(#pz-mark)" />
        <rect x="2" y="2" width="44" height="26" rx="13.5" fill="url(#pz-sheen)" />
        <rect
          x="2.75" y="2.75" width="42.5" height="42.5" rx="12.9"
          fill="none" stroke="#ffffff" strokeOpacity="0.22" strokeWidth="1.1"
        />
        <path d="M14 24.5 L34 15 L27.5 34 L23 26.5 Z" fill="#ffffff" />
        <path d="M23 26.5 L34 15" stroke="#E25421" strokeOpacity="0.55" strokeWidth="1.4" />
        <path
          d="M12 29.5 L17 29.5 M13.5 33 L16.5 33"
          stroke="#ffffff" strokeOpacity="0.6" strokeWidth="1.6" strokeLinecap="round"
        />
      </svg>

      {showWordmark && (
        <span
          className="font-black tracking-tight leading-none"
          style={{ fontSize: size * 0.56, letterSpacing: "-0.01em" }}
        >
          <span className="text-white">POST</span>
          <span className="text-brand">AZ</span>
        </span>
      )}

      {showFlag && <AzFlag h={size * 0.62} />}
    </div>
  );
}
