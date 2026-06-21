"use client";

import { useEffect, useState } from "react";

/** Fetches today's live CMC Fear & Greed (server-side route) and shows it as a badge. */
export function LiveSentimentBadge() {
  const [fg, setFg] = useState<{ value: number; classification: string } | null>(null);

  useEffect(() => {
    let alive = true;
    fetch("/api/sentiment")
      .then((r) => r.json())
      .then((j) => {
        if (alive && j?.live) setFg({ value: j.value, classification: j.classification });
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);

  if (!fg) return null;

  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-emerald/25 bg-emerald/[0.08] px-3 py-1 text-xs font-medium text-emerald-soft">
      <span className="relative flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald opacity-60" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald" />
      </span>
      Live now: <span className="font-mono text-white">{fg.value}</span>
      <span className="text-emerald/50">·</span>
      <span className="text-zinc-300">{fg.classification}</span>
    </span>
  );
}
