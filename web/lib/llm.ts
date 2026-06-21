/**
 * TS port of Darwin's LLM strategy operators (darwin/evolve/prompts.py,
 * darwin/evolve/generate.py, darwin/strategy/spec.py).
 *
 * Used by the /api/evolve route to run the *same* mutate operator the offline
 * genetic algorithm uses — live, in the browser, on the locked champion.
 */
import type { Champion, Metrics } from "./data";

const INDICATOR_TYPES = new Set([
  "SMA", "EMA", "RSI", "ATR", "ROC", "PRICE", "MACD", "MACD_SIGNAL", "MACD_HIST",
]);
const PRICE_SOURCES = new Set(["open", "high", "low", "close", "volume"]);
const SIGNAL_SOURCES = new Set(["fgi", "mom", "breadth"]);
const OPERATORS = new Set([">", "<", ">=", "<=", "cross_above", "cross_below"]);

export const SPEC_GUIDE = `A StrategySpec is JSON with this shape:

{
  "name": "short human label",
  "universe": ["BTC", "ETH", "BNB"],
  "timeframe": "1d",
  "indicators": [
    {"id": "sma_fast", "type": "SMA", "source": "close", "period": 10},
    {"id": "rsi", "type": "RSI", "period": 14},
    {"id": "macd", "type": "MACD", "source": "close", "fast": 12, "slow": 26, "signal": 9},
    {"id": "macd_sig", "type": "MACD_SIGNAL", "source": "close", "fast": 12, "slow": 26, "signal": 9}
  ],
  "entry": {"all": [
    {"left": "sma_fast", "op": "cross_above", "right": "sma_slow"},
    {"left": "rsi", "op": "<", "right": 70}
  ]},
  "exit": {"any": [
    {"left": "sma_fast", "op": "cross_below", "right": "sma_slow"},
    {"left": "rsi", "op": ">", "right": 80}
  ]},
  "risk": {
    "max_position_pct": 0.25, "max_open_positions": 3,
    "stop_loss_pct": 0.08, "take_profit_pct": 0.25,
    "max_drawdown_pct": 0.30, "trailing_stop_pct": 0.0
  },
  "sizing": {"type": "equal_weight"},
  "rationale": "one sentence on the edge this strategy exploits"
}

Rules:
- indicator.type in {SMA, EMA, RSI, ATR, ROC, PRICE, MACD, MACD_SIGNAL, MACD_HIST}. PRICE exposes a raw price source.
- MACD/MACD_SIGNAL/MACD_HIST use fast/slow/signal (default 12/26/9), not period. Cross MACD over MACD_SIGNAL for classic signals.
- A condition is either {"all":[...]}, {"any":[...]}, or a leaf {"left","op","right"}.
- op in {">","<",">=","<=","cross_above","cross_below"}.
- left/right are an indicator id, a price source (open/high/low/close/volume), the signal "fgi", or a number.
- Market signals (CMC-derived, usable in any condition): "fgi" = Fear & Greed Index (0-100), "mom" = market momentum (mean trailing % return across the universe), "breadth" = % of the universe above its 50-bar trend (0-100). Use them for regime filters.
- Strategies are LONG/FLAT only. Entry opens, exit (or a risk rule) closes.
- Keep it simple and economically sensible; the backtester is strict and deterministic.`;

export const SYSTEM = `You are a quantitative strategy designer inside Darwin, an evolutionary trading-strategy foundry for BNB Chain. You design LONG/FLAT crypto strategies as strict JSON StrategySpec objects that a deterministic backtester will score on risk-adjusted return, drawdown, and adherence to user-defined risk rules.

${SPEC_GUIDE}

You MUST output only valid JSON — no prose, no markdown fences. Strategies must be economically sensible (a real edge: trend, mean-reversion, momentum, breakout, or sentiment), not curve-fit noise. Prefer robust risk rules: sane stops, take-profits, and a max_drawdown kill-switch. You may use the market-wide signal "fgi" (CoinMarketCap Fear & Greed Index, 0-100) as a condition reference for contrarian or regime filters.`;

export function mutatePrompt(spec: Champion, m: Metrics, fgi: number | null): string {
  const context =
    `Universe ${JSON.stringify(spec.universe)} on the ${spec.timeframe} timeframe.` +
    (fgi != null ? ` Current CMC Fear & Greed Index: ${fgi}.` : "");
  const specJson = JSON.stringify(
    {
      name: spec.name,
      universe: spec.universe,
      timeframe: spec.timeframe,
      indicators: spec.indicators,
      entry: spec.entry,
      exit: spec.exit,
      risk: spec.risk,
      sizing: spec.sizing,
      rationale: spec.rationale,
    },
    null,
    2,
  );
  return `Market context:
${context}

Here is the current CHAMPION strategy and its backtest metrics:

SPEC:
${specJson}

METRICS:
  total_return=${m.totalReturn.toFixed(3)}  sharpe=${m.sharpe.toFixed(2)}  sortino=${m.sortino.toFixed(2)}
  max_drawdown=${m.maxDrawdown.toFixed(3)}  calmar=${m.calmar.toFixed(2)}
  win_rate=${m.winRate.toFixed(2)}  num_trades=${m.numTrades}  exposure=${m.exposure.toFixed(2)}
  rule_adherence=${m.ruleAdherence.toFixed(2)}

Diagnose its single biggest weakness (e.g. drawdown too deep, over-trading, poor risk-adjusted return, barely in the market) and produce ONE improved variant that targets that weakness while preserving what works. Make a meaningful, non-trivial change — not just a tiny threshold nudge. Give it a fresh, distinct name and a one-sentence rationale.

Output a single JSON StrategySpec object. JSON only.`;
}

/** Pull the first balanced JSON object/array out of a model response. */
export function extractJson(text: string): unknown {
  let t = text.trim().replace(/^```(?:json)?/i, "").replace(/```$/i, "").trim();
  const candidates = [t.indexOf("{"), t.indexOf("[")].filter((i) => i !== -1);
  if (candidates.length === 0) throw new Error("no JSON found in response");
  const start = Math.min(...candidates);
  const open = t[start];
  let depth = 0;
  let inStr = false;
  let esc = false;
  for (let i = start; i < t.length; i++) {
    const c = t[i];
    if (inStr) {
      if (esc) esc = false;
      else if (c === "\\") esc = true;
      else if (c === '"') inStr = false;
      continue;
    }
    if (c === '"') inStr = true;
    else if (c === "[" || c === "{") depth++;
    else if (c === "]" || c === "}") {
      depth--;
      if (depth === 0) return JSON.parse(t.slice(start, i + 1));
    }
  }
  return JSON.parse(t.slice(start));
}

function validateCondition(node: any, ids: Set<string>, where: string): void {
  if (!node || typeof node !== "object") throw new Error(`${where} condition is empty`);
  if ("all" in node || "any" in node) {
    const key = "all" in node ? "all" : "any";
    const children = node[key];
    if (!Array.isArray(children) || children.length === 0)
      throw new Error(`${where}: ${key} must be a non-empty list`);
    for (const child of children) validateCondition(child, ids, where);
    return;
  }
  for (const k of ["left", "op", "right"]) {
    if (!(k in node)) throw new Error(`${where}: leaf missing '${k}'`);
  }
  if (!OPERATORS.has(node.op)) throw new Error(`${where}: bad operator ${node.op}`);
  for (const side of ["left", "right"]) {
    const ref = node[side];
    if (typeof ref === "string" && !ids.has(ref) && !PRICE_SOURCES.has(ref) && !SIGNAL_SOURCES.has(ref))
      throw new Error(`${where}: unknown reference '${ref}'`);
  }
}

/** Structural validation mirroring StrategySpec.validate(). Throws on invalid. */
export function validateSpec(d: any): Champion {
  if (!d || typeof d !== "object") throw new Error("spec is not an object");
  if (!d.name) throw new Error("spec needs a name");
  if (!Array.isArray(d.universe) || d.universe.length === 0) throw new Error("universe cannot be empty");
  if (!Array.isArray(d.indicators)) throw new Error("indicators must be a list");
  const ids = new Set<string>();
  for (const ind of d.indicators) {
    if (!INDICATOR_TYPES.has(ind.type)) throw new Error(`unknown indicator type: ${ind.type}`);
    if (ind.source && !PRICE_SOURCES.has(ind.source)) throw new Error(`bad source ${ind.source}`);
    ids.add(ind.id);
  }
  validateCondition(d.entry, ids, "entry");
  validateCondition(d.exit, ids, "exit");
  return d as Champion;
}
