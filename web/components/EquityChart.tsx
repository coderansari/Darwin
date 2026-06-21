"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { EquityPoint } from "@/lib/data";

export function EquityChart({
  equity,
  start = 10000,
  oosStart,
}: {
  equity: EquityPoint[];
  start?: number;
  oosStart?: string;
}) {
  const last = equity[equity.length - 1]?.value ?? start;
  const min = Math.min(...equity.map((e) => e.value));
  const max = Math.max(...equity.map((e) => e.value));
  const up = last >= start;
  // First equity point at/after the out-of-sample boundary (dates are downsampled).
  const oosX = oosStart ? equity.find((e) => e.date >= oosStart)?.date : undefined;

  return (
    <div className="glass rounded-3xl p-5 sm:p-7">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">Equity curve</div>
          <div className="mt-1 font-mono text-2xl font-semibold text-white">
            ${last.toLocaleString("en-US", { maximumFractionDigits: 0 })}
          </div>
        </div>
        <div className="text-right text-sm text-zinc-500">
          <span className="text-zinc-400">{equity.length}</span> bars ·{" "}
          <span className="text-zinc-400">${start.toLocaleString("en-US")}</span> start
        </div>
      </div>

      <div className="h-64 w-full sm:h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={equity} margin={{ top: 6, right: 6, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="eqfill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={up ? "#10B981" : "#F43F5E"} stopOpacity={0.32} />
                <stop offset="100%" stopColor={up ? "#10B981" : "#F43F5E"} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fill: "#71717a", fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              minTickGap={48}
              tickFormatter={(d: string) => d.slice(2, 7)}
            />
            <YAxis
              domain={[Math.floor(min / 250) * 250, Math.ceil(max / 250) * 250]}
              tick={{ fill: "#71717a", fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              width={52}
              tickFormatter={(v: number) => `$${(v / 1000).toFixed(1)}k`}
            />
            <Tooltip
              contentStyle={{
                background: "rgba(14,14,17,0.95)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 12,
                color: "#fff",
                fontSize: 13,
              }}
              labelStyle={{ color: "#a1a1aa", marginBottom: 4 }}
              formatter={(v: number) => [`$${v.toLocaleString("en-US")}`, "Equity"]}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke={up ? "#34D399" : "#F43F5E"}
              strokeWidth={2.5}
              fill="url(#eqfill)"
              isAnimationActive
              animationDuration={1400}
            />
            {oosX && (
              <ReferenceLine
                x={oosX}
                stroke="#F0B90B"
                strokeDasharray="4 4"
                strokeOpacity={0.7}
                label={{ value: "out-of-sample →", position: "insideTopRight", fill: "#FCD34D", fontSize: 11 }}
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
