"use client";

import { motion } from "framer-motion";
import { Counter } from "./ui/Counter";
import { LiveBadge, Pill } from "./ui/Pill";
import type { Champion, Metrics, Meta } from "@/lib/data";
import { championTitle, pct, pctAbs, num } from "@/lib/data";

export function Hero({
  champion,
  metrics,
  meta,
  live,
}: {
  champion: Champion;
  metrics: Metrics;
  meta: Meta;
  live: boolean;
}) {
  const kpis = [
    { label: "Total return", to: metrics.totalReturn, fmt: (v: number) => pct(v, 1), tone: "emerald" as const },
    { label: "Sharpe", to: metrics.sharpe, fmt: (v: number) => num(v, 2), tone: "gold" as const },
    { label: "Max drawdown", to: metrics.maxDrawdown, fmt: (v: number) => pct(v, 1), tone: "emerald" as const },
    { label: "Rule adherence", to: metrics.ruleAdherence, fmt: (v: number) => pctAbs(v, 0), tone: "gold" as const },
  ];

  return (
    <section id="top" className="relative overflow-hidden pt-32 sm:pt-40">
      <HelixBackdrop />
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.21, 0.47, 0.32, 0.98] }}
          className="max-w-3xl"
        >
          <div className="mb-6 flex flex-wrap items-center gap-2.5">
            <Pill className="border-gold/25 bg-gold/[0.07] text-gold-soft">BNB Hack · Track 2</Pill>
            {live ? <LiveBadge /> : <Pill>Synthetic demo data</Pill>}
          </div>

          <h1 className="text-balance text-4xl font-semibold leading-[1.05] tracking-tight text-white sm:text-6xl">
            Darwin <span className="text-gradient-gold">evolves</span> trading strategies.
            <br className="hidden sm:block" /> It doesn&apos;t just prompt them.
          </h1>

          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-zinc-400">
            A population of backtestable strategy specs, scored on a deterministic,
            lookahead-free backtester and bred across generations into a champion —
            evolved on {meta.dataSource.toLowerCase().includes("live") ? "live" : ""}{" "}
            CoinMarketCap market data, then given an on-chain identity on BNB Chain.
          </p>

          <div className="mt-7 flex flex-wrap items-center gap-3">
            <a
              href="#champion"
              className="rounded-full bg-gold px-5 py-2.5 text-sm font-semibold text-ink-950 transition-transform hover:scale-[1.03]"
            >
              Meet the champion
            </a>
            <a
              href="#evolution"
              className="rounded-full border border-white/12 bg-white/[0.04] px-5 py-2.5 text-sm font-medium text-white transition-colors hover:border-white/25"
            >
              See the evolution
            </a>
          </div>
        </motion.div>

        {/* KPI row */}
        <motion.div
          initial={{ opacity: 0, y: 22 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.15 }}
          className="mt-14 grid grid-cols-2 gap-3 sm:mt-20 lg:grid-cols-4"
        >
          {kpis.map((k) => (
            <div key={k.label} className="glass glass-hover rounded-2xl p-5">
              <div
                className={`font-mono text-3xl font-semibold tracking-tight sm:text-4xl ${
                  k.tone === "emerald" ? "text-emerald-soft" : "text-gold-soft"
                }`}
              >
                <Counter to={k.to} format={k.fmt} />
              </div>
              <div className="mt-2 text-sm text-zinc-500">{k.label}</div>
            </div>
          ))}
        </motion.div>

        <p className="mt-5 text-sm text-zinc-600">
          Champion <span className="text-zinc-400">{championTitle(champion.name)}</span> ·{" "}
          <span className="font-mono text-zinc-500">{champion.fingerprint}</span> · bred across{" "}
          {meta.generations} generations · {metrics.numTrades} trades
        </p>
      </div>
    </section>
  );
}

/** Subtle animated DNA-helix lines behind the hero. */
function HelixBackdrop() {
  return (
    <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      <svg
        className="absolute -right-20 -top-24 h-[34rem] w-[34rem] opacity-[0.13] sm:opacity-20"
        viewBox="0 0 400 400"
        fill="none"
      >
        <defs>
          <linearGradient id="hb" x1="0" y1="400" x2="400" y2="0">
            <stop stopColor="#F0B90B" />
            <stop offset="1" stopColor="#10B981" />
          </linearGradient>
        </defs>
        {Array.from({ length: 9 }).map((_, i) => {
          const y = 30 + i * 42;
          return (
            <motion.line
              key={i}
              x1={120 + 80 * Math.sin(i * 0.7)}
              x2={280 - 80 * Math.sin(i * 0.7)}
              y1={y}
              y2={y}
              stroke="url(#hb)"
              strokeWidth="3"
              strokeLinecap="round"
              initial={{ opacity: 0.2 }}
              animate={{ opacity: [0.2, 0.7, 0.2] }}
              transition={{ duration: 4, delay: i * 0.25, repeat: Infinity }}
            />
          );
        })}
        <path d="M120 30C200 130 200 270 120 372" stroke="url(#hb)" strokeWidth="2" opacity="0.5" />
        <path d="M280 30C200 130 200 270 280 372" stroke="url(#hb)" strokeWidth="2" opacity="0.5" />
      </svg>
    </div>
  );
}
