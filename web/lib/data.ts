import darwin from "@/public/data/darwin.json";

/* ---- Types (shape of web/public/data/darwin.json) ---- */

export interface Indicator {
  id: string;
  type: string;
  period?: number;
  source?: string;
  fast?: number;
  slow?: number;
  signal?: number;
}

export interface Condition {
  left: string;
  op: string;
  right: string | number;
}

export interface Champion {
  name: string;
  fingerprint: string;
  rationale: string;
  universe: string[];
  timeframe: string;
  indicators: Indicator[];
  entry: { all?: Condition[]; any?: Condition[] };
  exit: { all?: Condition[]; any?: Condition[] };
  risk: Record<string, number>;
  sizing: { type: string; fraction: number };
}

export interface Metrics {
  totalReturn: number;
  cagr: number;
  sharpe: number;
  sortino: number;
  maxDrawdown: number;
  calmar: number;
  winRate: number;
  numTrades: number;
  exposure: number;
  ruleAdherence: number;
  finalEquity: number;
}

export interface EquityPoint {
  date: string;
  value: number;
}

export interface Generation {
  generation: number;
  best_fitness: number;
  mean_fitness: number;
  best: string;
}

export interface FearGreed {
  value: number | null;
  classification: string;
  series: { date: string; value: number }[];
  source: string;
}

export interface Identity {
  agentId: number | null;
  txHash: string;
  registry: string;
  wallet: string;
  network: string;
  gasless: boolean;
  explorer: string;
}

export interface Meta {
  dataSource: string;
  universe: string[];
  bars: number;
  generations: number;
  sponsors: { cmc: string; bnb: string; twak: string };
}

export interface DarwinData {
  champion: Champion;
  metrics: Metrics;
  equity: EquityPoint[];
  history: Generation[];
  fearGreed: FearGreed;
  identity: Identity;
  meta: Meta;
}

export const data = darwin as DarwinData;

/* ---- Derived helpers ---- */

/** The raw GA name is a long crossover concatenation; produce a clean human title. */
export function championTitle(name: string): string {
  // Collapse repeated lineage fragments into a readable hybrid name.
  const parts = name
    .split(/\s+x\s+/i)
    .map((p) => p.replace(/#\d+/g, "").trim())
    .filter(Boolean);
  const seen = new Set<string>();
  const unique: string[] = [];
  for (const p of parts) {
    const key = p.toLowerCase();
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(p);
    }
  }
  const top = unique.slice(0, 2);
  return top.join(" × ");
}

export function pct(n: number, digits = 1): string {
  return `${n >= 0 ? "+" : ""}${(n * 100).toFixed(digits)}%`;
}

export function pctAbs(n: number, digits = 1): string {
  return `${(n * 100).toFixed(digits)}%`;
}

export function num(n: number, digits = 2): string {
  return n.toFixed(digits);
}

export function usd(n: number): string {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

export function shortAddr(a: string, head = 6, tail = 4): string {
  if (!a) return "";
  return a.length > head + tail ? `${a.slice(0, head)}…${a.slice(-tail)}` : a;
}
