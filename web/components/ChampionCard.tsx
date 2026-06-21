import { Reveal } from "./ui/Reveal";
import { Pill } from "./ui/Pill";
import type { Champion, Condition, Metrics } from "@/lib/data";
import { championTitle } from "@/lib/data";

const OP_LABEL: Record<string, string> = {
  cross_above: "crosses above",
  cross_below: "crosses below",
  ">": ">",
  "<": "<",
  ">=": "≥",
  "<=": "≤",
  "==": "=",
};

const TOKEN_COLORS: Record<string, string> = {
  BTC: "text-amber-400",
  ETH: "text-indigo-300",
  BNB: "text-gold",
  SOL: "text-emerald-soft",
};

function term(t: string | number): string {
  if (typeof t === "number") return t.toString();
  return t.replace(/_/g, " ").toUpperCase();
}

function Rule({ c }: { c: Condition }) {
  return (
    <li className="flex items-center gap-2 text-sm">
      <code className="rounded-md bg-white/[0.05] px-1.5 py-0.5 font-mono text-xs text-zinc-200">{term(c.left)}</code>
      <span className="text-zinc-500">{OP_LABEL[c.op] ?? c.op}</span>
      <code className="rounded-md bg-white/[0.05] px-1.5 py-0.5 font-mono text-xs text-zinc-200">{term(c.right)}</code>
    </li>
  );
}

export function ChampionCard({ champion, metrics }: { champion: Champion; metrics: Metrics }) {
  const entry = champion.entry.all ?? champion.entry.any ?? [];
  const exit = champion.exit.all ?? champion.exit.any ?? [];
  const entryJoin = champion.entry.all ? "ALL of" : "ANY of";
  const exitJoin = champion.exit.all ? "ALL of" : "ANY of";

  return (
    <div className="grid gap-5 lg:grid-cols-5">
      {/* Identity / rationale */}
      <Reveal className="lg:col-span-3">
        <div className="glass h-full rounded-3xl p-6 sm:p-8">
          <div className="flex flex-wrap items-center gap-2.5">
            <Pill className="border-emerald/25 bg-emerald/[0.08] text-emerald-soft">Champion</Pill>
            <Pill className="font-mono">{champion.fingerprint}</Pill>
            <Pill>{champion.timeframe} timeframe</Pill>
          </div>

          <h3 className="mt-5 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
            {championTitle(champion.name)}
          </h3>
          <p className="mt-4 leading-relaxed text-zinc-400">{champion.rationale}</p>

          <div className="mt-6">
            <div className="mb-2.5 text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">Universe</div>
            <div className="flex flex-wrap gap-2">
              {champion.universe.map((u) => (
                <span
                  key={u}
                  className={`rounded-lg border border-white/8 bg-white/[0.04] px-2.5 py-1 font-mono text-sm ${
                    TOKEN_COLORS[u] ?? "text-zinc-300"
                  }`}
                >
                  {u}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-6">
            <div className="mb-2.5 text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">Indicators</div>
            <div className="flex flex-wrap gap-2">
              {champion.indicators.map((ind) => (
                <span
                  key={ind.id}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-white/8 bg-white/[0.03] px-2.5 py-1 text-sm text-zinc-300"
                >
                  <span className="font-medium text-white">{ind.type.replace(/_/g, " ")}</span>
                  {ind.period ? <span className="font-mono text-xs text-zinc-500">{ind.period}</span> : null}
                </span>
              ))}
            </div>
          </div>
        </div>
      </Reveal>

      {/* Rules + risk */}
      <Reveal delay={0.1} className="lg:col-span-2">
        <div className="flex h-full flex-col gap-4">
          <div className="glass rounded-3xl p-6">
            <div className="flex items-center gap-2 text-sm font-semibold text-emerald-soft">
              <span className="h-2 w-2 rounded-full bg-emerald" /> Entry — {entryJoin}
            </div>
            <ul className="mt-3 space-y-2">
              {entry.map((c, i) => (
                <Rule key={i} c={c} />
              ))}
            </ul>
          </div>

          <div className="glass rounded-3xl p-6">
            <div className="flex items-center gap-2 text-sm font-semibold text-rose">
              <span className="h-2 w-2 rounded-full bg-rose" /> Exit — {exitJoin}
            </div>
            <ul className="mt-3 space-y-2">
              {exit.map((c, i) => (
                <Rule key={i} c={c} />
              ))}
            </ul>
          </div>

          <div className="glass rounded-3xl p-6">
            <div className="text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">Risk controls</div>
            <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2.5 text-sm">
              <Risk k="Stop loss" v={`${(champion.risk.stop_loss_pct * 100).toFixed(0)}%`} />
              <Risk k="Take profit" v={`${(champion.risk.take_profit_pct * 100).toFixed(0)}%`} />
              <Risk k="Max position" v={`${(champion.risk.max_position_pct * 100).toFixed(0)}%`} />
              <Risk k="Trailing stop" v={`${(champion.risk.trailing_stop_pct * 100).toFixed(1)}%`} />
              <Risk k="Max positions" v={`${champion.risk.max_open_positions}`} />
              <Risk k="Sizing" v={`${(champion.sizing.fraction * 100).toFixed(0)}% eq-wt`} />
            </dl>
          </div>
        </div>
      </Reveal>
    </div>
  );
}

function Risk({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-zinc-500">{k}</dt>
      <dd className="font-mono text-zinc-200">{v}</dd>
    </div>
  );
}
