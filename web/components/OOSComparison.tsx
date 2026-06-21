import { Reveal } from "./ui/Reveal";
import type { OOS, Metrics } from "@/lib/data";
import { pct, num, pctAbs } from "@/lib/data";

const ROWS: { label: string; fmt: (m: Metrics) => string; hero?: boolean }[] = [
  { label: "Return", fmt: (m) => pct(m.totalReturn, 1) },
  { label: "Sharpe", fmt: (m) => num(m.sharpe, 2) },
  { label: "Max drawdown", fmt: (m) => pct(m.maxDrawdown, 1), hero: true },
  { label: "Win rate", fmt: (m) => pctAbs(m.winRate, 0) },
  { label: "Trades", fmt: (m) => String(m.numTrades) },
  { label: "Rule adherence", fmt: (m) => pctAbs(m.ruleAdherence, 0), hero: true },
];

function Col({
  title,
  sub,
  m,
  tone,
}: {
  title: string;
  sub: string;
  m: Metrics;
  tone: "muted" | "hero";
}) {
  const isHero = tone === "hero";
  return (
    <div
      className={`flex-1 rounded-2xl border p-5 ${
        isHero ? "border-emerald/25 bg-emerald/[0.05]" : "border-white/8 bg-white/[0.02]"
      }`}
    >
      <div className={`text-sm font-semibold ${isHero ? "text-emerald-soft" : "text-zinc-300"}`}>{title}</div>
      <div className="text-[11px] text-zinc-600">{sub}</div>
      <dl className="mt-4 space-y-2.5">
        {ROWS.map((r) => (
          <div key={r.label} className="flex items-center justify-between gap-3">
            <dt className="text-sm text-zinc-500">{r.label}</dt>
            <dd
              className={`font-mono text-sm ${
                isHero && r.hero ? "font-semibold text-emerald-soft" : isHero ? "text-zinc-100" : "text-zinc-300"
              }`}
            >
              {r.fmt(m)}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

export function OOSComparison({ oos }: { oos: OOS }) {
  return (
    <Reveal>
      <div className="glass overflow-hidden rounded-3xl p-6 sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-2xl">
            <div className="flex items-center gap-2.5 text-xs font-medium uppercase tracking-[0.2em] text-gold">
              <span className="h-px w-6 bg-gold/60" /> Not overfit
            </div>
            <h3 className="mt-3 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
              Forward-tested out-of-sample
            </h3>
            <p className="mt-3 leading-relaxed text-zinc-400">
              The strategy was designed on the first half of history and{" "}
              <span className="text-emerald-soft">forward-tested on a held-out window it never saw</span>.
              On unseen data it preserved capital with a{" "}
              <span className="text-zinc-200">{pct(oos.outOfSample.maxDrawdown, 1)}</span> max drawdown and{" "}
              <span className="text-zinc-200">{pctAbs(oos.outOfSample.ruleAdherence, 0)}</span> rule adherence —
              no overtrading, no blow-up. Most &quot;AI strategy&quot; results are 100% in-sample and can&apos;t show this at all.
            </p>
          </div>
          <div className="rounded-xl border border-white/8 bg-white/[0.02] px-4 py-2.5 text-xs text-zinc-500">
            held out after <span className="font-mono text-zinc-300">{oos.splitDate}</span>
          </div>
        </div>

        <div className="mt-7 flex flex-col gap-3 sm:flex-row">
          <Col title="In-sample" sub="design window" m={oos.inSample} tone="muted" />
          <div className="hidden items-center sm:flex">
            <span className="text-2xl text-zinc-700">→</span>
          </div>
          <Col title="Out-of-sample" sub="held-out · never seen" m={oos.outOfSample} tone="hero" />
        </div>

        <p className="mt-5 text-xs text-zinc-600">
          The held-out window is never used to design or select the strategy — a true forward test, the same
          way Track 2 judges score against an unseen market window.
        </p>
      </div>
    </Reveal>
  );
}
