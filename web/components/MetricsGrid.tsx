import { Reveal } from "./ui/Reveal";
import type { Metrics } from "@/lib/data";
import { pct, pctAbs, num, usd } from "@/lib/data";

export function MetricsGrid({ metrics: m }: { metrics: Metrics }) {
  const tiles = [
    { label: "CAGR", value: pct(m.cagr, 1), tone: "emerald", hint: "annualized" },
    { label: "Sortino", value: num(m.sortino, 2), tone: "gold", hint: "downside-adj." },
    { label: "Calmar", value: num(m.calmar, 2), tone: "gold", hint: "return / max DD" },
    { label: "Win rate", value: pctAbs(m.winRate, 1), tone: "emerald", hint: "of closed trades" },
    { label: "Trades", value: m.numTrades.toString(), tone: "default", hint: "low churn" },
    { label: "Exposure", value: pctAbs(m.exposure, 1), tone: "default", hint: "time in market" },
    { label: "Final equity", value: usd(m.finalEquity), tone: "emerald", hint: "from $10k" },
    { label: "Rule adherence", value: pctAbs(m.ruleAdherence, 0), tone: "gold", hint: "risk rules honored" },
  ] as const;

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {tiles.map((t, i) => (
        <Reveal key={t.label} delay={i * 0.04}>
          <div className="glass glass-hover h-full rounded-2xl p-5">
            <div
              className={`font-mono text-2xl font-semibold tracking-tight ${
                t.tone === "emerald"
                  ? "text-emerald-soft"
                  : t.tone === "gold"
                    ? "text-gold-soft"
                    : "text-white"
              }`}
            >
              {t.value}
            </div>
            <div className="mt-2 text-sm text-zinc-400">{t.label}</div>
            <div className="text-xs text-zinc-600">{t.hint}</div>
          </div>
        </Reveal>
      ))}
    </div>
  );
}
