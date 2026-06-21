/**
 * Darwin brand mark — placeholder DNA-helix-that-becomes-a-rising-chart.
 * Swap this SVG for the final generated logo (drop into /public and reference)
 * without touching layout: the component API (size, withWord) stays the same.
 */
export function Logo({ size = 32, className = "" }: { size?: number; className?: string }) {
  const id = "darwin-grad";
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={id} x1="6" y1="42" x2="42" y2="6" gradientUnits="userSpaceOnUse">
          <stop stopColor="#F0B90B" />
          <stop offset="0.55" stopColor="#FCD34D" />
          <stop offset="1" stopColor="#10B981" />
        </linearGradient>
      </defs>
      {/* left helix strand */}
      <path
        d="M14 40c0-7 8-9 8-16s-8-9-8-16"
        stroke={`url(#${id})`}
        strokeWidth="2.6"
        strokeLinecap="round"
        opacity="0.55"
      />
      {/* right strand unwinding into a rising trend line */}
      <path
        d="M30 40c0-7-8-9-8-16s8-9 8-16"
        stroke={`url(#${id})`}
        strokeWidth="2.6"
        strokeLinecap="round"
        opacity="0.55"
      />
      {/* helix rungs becoming ascending bars */}
      <path d="M15 34h14" stroke={`url(#${id})`} strokeWidth="2.6" strokeLinecap="round" />
      <path d="M16.5 24h11" stroke={`url(#${id})`} strokeWidth="2.6" strokeLinecap="round" />
      <path d="M15 14h14" stroke={`url(#${id})`} strokeWidth="2.6" strokeLinecap="round" />
      {/* breakout trend line + arrow */}
      <path
        d="M12 30l7-6 6 4 11-14"
        stroke={`url(#${id})`}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M31 14h5v5"
        stroke="#10B981"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function Wordmark({ size = 32, className = "" }: { size?: number; className?: string }) {
  return (
    <span className={`flex items-center gap-2.5 ${className}`}>
      <Logo size={size} />
      <span className="text-[1.15rem] font-semibold tracking-tight text-white">
        Darwin
      </span>
    </span>
  );
}
