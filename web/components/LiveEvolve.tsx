"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Champion, Condition } from "@/lib/data";

const OP_LABEL: Record<string, string> = {
  cross_above: "crosses above",
  cross_below: "crosses below",
  ">": ">", "<": "<", ">=": "≥", "<=": "≤", "==": "=",
};

function term(t: string | number): string {
  return typeof t === "number" ? String(t) : t.replace(/_/g, " ").toUpperCase();
}

type Node = Condition | { all?: Node[]; any?: Node[] };

/** Recursively render a condition tree (leaves + nested all/any groups). */
function ConditionView({ node, depth = 0 }: { node: Node; depth?: number }) {
  const group = (node as any).all ? "all" : (node as any).any ? "any" : null;
  if (group) {
    const children: Node[] = (node as any)[group];
    return (
      <div className={depth > 0 ? "rounded-lg border border-white/8 bg-white/[0.02] p-2.5" : ""}>
        <div className="mb-1.5 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
          {group === "all" ? "all of" : "any of"}
        </div>
        <ul className="space-y-1.5">
          {children.map((c, i) => (
            <li key={i}>
              <ConditionView node={c} depth={depth + 1} />
            </li>
          ))}
        </ul>
      </div>
    );
  }
  const c = node as Condition;
  return (
    <span className="flex flex-wrap items-center gap-1.5 text-sm">
      <code className="rounded bg-white/[0.06] px-1.5 py-0.5 font-mono text-xs text-zinc-200">{term(c.left)}</code>
      <span className="text-zinc-500">{OP_LABEL[c.op] ?? c.op}</span>
      <code className="rounded bg-white/[0.06] px-1.5 py-0.5 font-mono text-xs text-zinc-200">{term(c.right)}</code>
    </span>
  );
}

export function LiveEvolve() {
  const [loading, setLoading] = useState(false);
  const [spec, setSpec] = useState<Champion | null>(null);
  const [model, setModel] = useState<string>("");
  const [error, setError] = useState<string>("");

  async function evolve() {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/evolve", { method: "POST" });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || "Live evolution failed.");
      setSpec(json.spec);
      setModel(json.model || "");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Live evolution failed.");
      setSpec(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="glass rounded-3xl p-6 sm:p-8">    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.16em] text-gold">
            <span className="h-1.5 w-1.5 rounded-full bg-gold" /> Live · powered by Claude
          </div>
          <h3 className="mt-2 text-xl font-semibold text-white">Watch Darwin invent a strategy</h3>
          <p className="mt-1 max-w-xl text-sm text-zinc-400">
            Run the genetic algorithm&apos;s real LLM operator on the spot — it breeds a fresh,
            backtestable candidate from the champion, live.
          </p>
        </div>
        <button
          onClick={evolve}
          disabled={loading}
          className="shrink-0 rounded-full bg-gold px-5 py-2.5 text-sm font-semibold text-ink-950 transition-transform hover:scale-[1.03] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Evolving…" : spec ? "Evolve another" : "⚡ Evolve live"}
        </button>
      </div>

      <AnimatePresence mode="wait">
        {loading && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="mt-6 flex items-center gap-3 text-sm text-zinc-400"
          >
            <span className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <motion.span
                  key={i}
                  className="h-2 w-2 rounded-full bg-gold"
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                />
              ))}
            </span>
            Diagnosing the champion&apos;s weakness and breeding a variant…
          </motion.div>
        )}

        {error && !loading && (
          <motion.div
            key="error"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 rounded-xl border border-rose/30 bg-rose/[0.08] px-4 py-3 text-sm text-rose"
          >
            {error}
          </motion.div>
        )}

        {spec && !loading && (
          <motion.div
            key={spec.name}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="mt-6 rounded-2xl border border-gold/20 bg-gold/[0.03] p-5"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-gold/30 bg-gold/10 px-2.5 py-1 text-xs font-medium text-gold-soft">
                Freshly evolved
              </span>
              {model && <span className="rounded-full border border-white/10 px-2.5 py-1 font-mono text-xs text-zinc-400">{model}</span>}
            </div>
            <h4 className="mt-3 text-lg font-semibold text-white">{spec.name}</h4>
            {spec.rationale && <p className="mt-2 text-sm leading-relaxed text-zinc-400">{spec.rationale}</p>}

            <div className="mt-4 flex flex-wrap gap-2">
              {spec.indicators?.map((ind) => (
                <span key={ind.id} className="inline-flex items-center gap-1.5 rounded-lg border border-white/8 bg-white/[0.03] px-2.5 py-1 text-sm text-zinc-300">
                  <span className="font-medium text-white">{ind.type.replace(/_/g, " ")}</span>
                  {ind.period ? <span className="font-mono text-xs text-zinc-500">{ind.period}</span> : null}
                </span>
              ))}
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <div className="text-xs font-semibold text-emerald-soft">Entry</div>
                <div className="mt-2">
                  <ConditionView node={spec.entry} />
                </div>
              </div>
              <div>
                <div className="text-xs font-semibold text-rose">Exit</div>
                <div className="mt-2">
                  <ConditionView node={spec.exit} />
                </div>
              </div>
            </div>

            <p className="mt-4 border-t border-white/[0.06] pt-3 text-xs text-zinc-500">
              A real candidate from the LLM operator. In a full run, the GA backtests it on live data,
              scores its fitness, and keeps it only if it beats the champion.
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
