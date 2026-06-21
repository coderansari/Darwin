"use client";

import { motion } from "framer-motion";
import type { FearGreed } from "@/lib/data";

const ARC_START = -220; // degrees
const ARC_END = 40;
const RANGE = ARC_END - ARC_START;

function colorFor(v: number): string {
  if (v < 25) return "#F43F5E";
  if (v < 45) return "#FB923C";
  if (v < 55) return "#FCD34D";
  if (v < 75) return "#34D399";
  return "#10B981";
}

function polar(cx: number, cy: number, r: number, deg: number) {
  const rad = (deg * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function arcPath(cx: number, cy: number, r: number, startDeg: number, endDeg: number) {
  const s = polar(cx, cy, r, startDeg);
  const e = polar(cx, cy, r, endDeg);
  const large = endDeg - startDeg > 180 ? 1 : 0;
  return `M ${s.x} ${s.y} A ${r} ${r} 0 ${large} 1 ${e.x} ${e.y}`;
}

export function FearGreedGauge({ fg }: { fg: FearGreed }) {
  const value = fg.value ?? 50;
  const color = colorFor(value);
  const cx = 110;
  const cy = 110;
  const r = 88;
  const valueDeg = ARC_START + (value / 100) * RANGE;
  const series = fg.series.slice(-60);
  const sMin = Math.min(...series.map((s) => s.value));
  const sMax = Math.max(...series.map((s) => s.value));

  return (
    <div className="grid gap-5 sm:grid-cols-5">
      <div className="glass flex flex-col items-center justify-center rounded-3xl p-6 sm:col-span-2">
        <svg viewBox="0 0 220 200" className="w-full max-w-[260px]">
          {/* track */}
          <path d={arcPath(cx, cy, r, ARC_START, ARC_END)} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="14" strokeLinecap="round" />
          {/* value arc */}
          <motion.path
            d={arcPath(cx, cy, r, ARC_START, valueDeg)}
            fill="none"
            stroke={color}
            strokeWidth="14"
            strokeLinecap="round"
            initial={{ pathLength: 0, opacity: 0.4 }}
            whileInView={{ pathLength: 1, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 1.3, ease: "easeOut" }}
            style={{ filter: `drop-shadow(0 0 8px ${color}66)` }}
          />
          <text x={cx} y={cy - 2} textAnchor="middle" className="fill-white font-mono" style={{ fontSize: 40, fontWeight: 600 }}>
            {value}
          </text>
          <text x={cx} y={cy + 26} textAnchor="middle" style={{ fontSize: 13, fill: color, fontWeight: 600 }}>
            {fg.classification}
          </text>
        </svg>
        <div className="mt-1 flex items-center gap-2 text-xs text-zinc-500">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald" />
          CMC Fear &amp; Greed · {fg.source}
        </div>
      </div>

      <div className="glass rounded-3xl p-6 sm:col-span-3">
        <div className="flex items-center justify-between">
          <div className="text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">90-day sentiment</div>
          <div className="text-xs text-zinc-500">
            range <span className="font-mono text-zinc-300">{sMin}</span>–<span className="font-mono text-zinc-300">{sMax}</span>
          </div>
        </div>

        <div className="mt-5 h-40">
          <Sparkline series={series} />
        </div>

        <p className="mt-4 text-sm leading-relaxed text-zinc-400">
          Darwin treats CMC&apos;s Fear &amp; Greed Index as a first-class signal — champions gate
          entries and exits on the sentiment regime, not just price.
        </p>
      </div>
    </div>
  );
}

function Sparkline({ series }: { series: { date: string; value: number }[] }) {
  const w = 600;
  const h = 140;
  const pad = 6;
  const min = Math.min(...series.map((s) => s.value));
  const max = Math.max(...series.map((s) => s.value));
  const span = Math.max(1, max - min);
  const pts = series.map((s, i) => {
    const x = pad + (i / (series.length - 1)) * (w - pad * 2);
    const y = pad + (1 - (s.value - min) / span) * (h - pad * 2);
    return [x, y] as const;
  });
  const line = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ");
  const area = `${line} L ${pts[pts.length - 1][0].toFixed(1)} ${h - pad} L ${pad} ${h - pad} Z`;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="h-full w-full">
      <defs>
        <linearGradient id="fgfill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#F0B90B" stopOpacity={0.28} />
          <stop offset="100%" stopColor="#F0B90B" stopOpacity={0} />
        </linearGradient>
      </defs>
      {[25, 50, 75].map((g) => {
        const y = pad + (1 - (g - min) / span) * (h - pad * 2);
        if (y < 0 || y > h) return null;
        return <line key={g} x1={0} x2={w} y1={y} y2={y} stroke="rgba(255,255,255,0.05)" strokeWidth={1} />;
      })}
      <path d={area} fill="url(#fgfill)" />
      <motion.path
        d={line}
        fill="none"
        stroke="#FCD34D"
        strokeWidth={2.5}
        strokeLinejoin="round"
        initial={{ pathLength: 0 }}
        whileInView={{ pathLength: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 1.4, ease: "easeOut" }}
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
