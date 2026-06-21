"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Generation } from "@/lib/data";

/** Pull a short readable label + return out of the GA's "best" string. */
function parseBest(s: string): { name: string; ret: string | null } {
  const retMatch = s.match(/ret=([+\-]?\d+(?:\.\d+)?%)/);
  const name = s
    .split("[")[0]
    .split(/\s+x\s+/i)[0]
    .replace(/#\d+/g, "")
    .trim();
  return { name, ret: retMatch ? retMatch[1] : null };
}

export function EvolutionTimeline({ history }: { history: Generation[] }) {
  const data = history.map((h) => ({
    gen: `G${h.generation}`,
    best: Number((h.best_fitness * 100).toFixed(1)),
    mean: Number((h.mean_fitness * 100).toFixed(1)),
  }));

  const first = history[0];
  const last = history[history.length - 1];
  const lift = last && first ? last.best_fitness - first.best_fitness : 0;

  return (
    <div className="grid gap-5 lg:grid-cols-5">
      {/* fitness chart */}
      <div className="glass rounded-3xl p-5 sm:p-7 lg:col-span-3">
        <div className="mb-4 flex items-end justify-between">
          <div>
            <div className="text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">
              Fitness per generation
            </div>
            <div className="mt-1 text-sm text-zinc-400">
              Best climbs <span className="font-mono text-emerald-soft">+{(lift * 100).toFixed(0)}pts</span>;
              the whole population converges upward.
            </div>
          </div>
        </div>
        <div className="h-64 w-full sm:h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 6, right: 8, left: -8, bottom: 0 }}>
              <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis dataKey="gen" tick={{ fill: "#71717a", fontSize: 12 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: "#71717a", fontSize: 11 }} tickLine={false} axisLine={false} width={36} />
              <Tooltip
                contentStyle={{
                  background: "rgba(14,14,17,0.95)",
                  border: "1px solid rgba(255,255,255,0.1)",
                  borderRadius: 12,
                  fontSize: 13,
                }}
                labelStyle={{ color: "#a1a1aa" }}
                formatter={(v: number, n: string) => [`${v}`, n === "best" ? "Best fitness" : "Mean fitness"]}
              />
              <Line
                type="monotone"
                dataKey="mean"
                stroke="#6366F1"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={false}
                animationDuration={1400}
              />
              <Line
                type="monotone"
                dataKey="best"
                stroke="#F0B90B"
                strokeWidth={2.75}
                dot={{ r: 3, fill: "#F0B90B" }}
                activeDot={{ r: 5 }}
                animationDuration={1600}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-3 flex items-center gap-5 text-xs text-zinc-500">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-4 rounded-full bg-gold" /> Best
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-4 rounded-full bg-indigo-500" /> Population mean
          </span>
        </div>
      </div>

      {/* generation ladder */}
      <div className="lg:col-span-2">
        <ol className="relative space-y-3 before:absolute before:left-[15px] before:top-2 before:h-[calc(100%-1rem)] before:w-px before:bg-white/10">
          {history.map((h) => {
            const { name, ret } = parseBest(h.best);
            const isLast = h.generation === last.generation;
            return (
              <li key={h.generation} className="relative flex gap-3.5">
                <span
                  className={`relative z-10 mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-xs font-semibold ${
                    isLast
                      ? "border-gold/50 bg-gold/15 text-gold-soft"
                      : "border-white/12 bg-ink-850 text-zinc-400"
                  }`}
                >
                  {h.generation}
                </span>
                <div className={`min-w-0 flex-1 rounded-xl border p-3 ${isLast ? "border-gold/25 bg-gold/[0.05]" : "border-white/8 bg-white/[0.02]"}`}>
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-medium text-zinc-200">{name}</span>
                    {ret && <span className="shrink-0 font-mono text-xs text-emerald-soft">{ret}</span>}
                  </div>
                  <div className="mt-1 flex items-center gap-3 text-xs text-zinc-500">
                    <span>fitness <span className="font-mono text-zinc-300">{h.best_fitness.toFixed(3)}</span></span>
                    {isLast && <span className="rounded-full bg-gold/15 px-2 py-0.5 text-gold-soft">champion</span>}
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
