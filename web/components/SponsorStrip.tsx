import { Reveal } from "./ui/Reveal";
import type { Meta } from "@/lib/data";

const SPONSORS = [
  {
    key: "cmc" as const,
    name: "CoinMarketCap",
    tag: "Agent Hub",
    icon: "📊",
    accent: "text-amber-300",
    desc: "Live OHLCV, quotes, and the proprietary Fear & Greed Index — wired into the strategy DSL as a first-class signal.",
  },
  {
    key: "bnb" as const,
    name: "BNB AI Agent SDK",
    tag: "Identity",
    icon: "🪪",
    accent: "text-gold-soft",
    desc: "Registers Darwin's verifiable ERC-8004 on-chain identity on BSC testnet — gas-sponsored, portable across the ecosystem.",
  },
  {
    key: "twak" as const,
    name: "Trust Wallet Agent Kit",
    tag: "Execution",
    icon: "🔐",
    accent: "text-emerald-soft",
    desc: "Live HMAC-authenticated gateway client with correct request signing and live BSC asset resolution for PancakeSwap routes.",
  },
];

export function SponsorStrip({ meta }: { meta: Meta }) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {SPONSORS.map((s, i) => (
        <Reveal key={s.key} delay={i * 0.08}>
          <div className="glass glass-hover h-full rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <span className="text-2xl">{s.icon}</span>
              <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-zinc-400">
                {s.tag}
              </span>
            </div>
            <h3 className={`mt-4 text-lg font-semibold ${s.accent}`}>{s.name}</h3>
            <p className="mt-2 text-sm leading-relaxed text-zinc-400">{s.desc}</p>
            <div className="mt-4 border-t border-white/[0.06] pt-3 text-xs text-zinc-500">
              {meta.sponsors[s.key]}
            </div>
          </div>
        </Reveal>
      ))}
    </div>
  );
}
