export function Pill({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs font-medium text-zinc-300 ${className}`}
    >
      {children}
    </span>
  );
}

export function LiveBadge({ label = "LIVE", source = "CoinMarketCap" }: { label?: string; source?: string }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-emerald/25 bg-emerald/[0.08] px-3 py-1 text-xs font-medium text-emerald-soft">
      <span className="relative flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald opacity-60" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald" />
      </span>
      {label}
      <span className="text-emerald/50">·</span>
      <span className="text-zinc-300">{source}</span>
    </span>
  );
}
