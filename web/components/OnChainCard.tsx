import { Reveal } from "./ui/Reveal";
import type { Identity } from "@/lib/data";
import { shortAddr } from "@/lib/data";

export function OnChainCard({ identity }: { identity: Identity }) {
  const rows = [
    { k: "Agent ID", v: `#${identity.agentId}`, mono: true },
    { k: "Registry", v: shortAddr(identity.registry, 8, 6), href: `https://testnet.bscscan.com/address/${identity.registry}`, mono: true },
    { k: "Wallet", v: shortAddr(identity.wallet, 8, 6), href: `https://testnet.bscscan.com/address/${identity.wallet}`, mono: true },
    { k: "Network", v: identity.network },
  ];

  return (
    <Reveal>
      <div className="glass relative overflow-hidden rounded-3xl p-6 sm:p-8">
        {/* certificate glow */}
        <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-emerald/20 blur-3xl" />

        <div className="relative flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-2 rounded-full border border-emerald/30 bg-emerald/10 px-3 py-1 text-sm font-semibold text-emerald-soft">
            <CheckIcon /> Verified on-chain
          </span>
          {identity.gasless && (
            <span className="rounded-full border border-gold/25 bg-gold/[0.08] px-3 py-1 text-sm font-medium text-gold-soft">
              ⛽ Gas-sponsored
            </span>
          )}
          <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-sm text-zinc-300">
            ERC-8004
          </span>
        </div>

        <h3 className="relative mt-5 text-2xl font-semibold tracking-tight text-white">
          Darwin holds a verifiable identity on BNB Chain
        </h3>
        <p className="relative mt-3 max-w-2xl leading-relaxed text-zinc-400">
          Registered via the official BNB AI Agent SDK — a portable, on-chain identity the
          agent can carry across the BNB ecosystem. Not a mock: it&apos;s a real testnet transaction.
        </p>

        <div className="relative mt-6 grid gap-3 sm:grid-cols-2">
          {rows.map((r) => (
            <div key={r.k} className="flex items-center justify-between rounded-xl border border-white/8 bg-white/[0.02] px-4 py-3">
              <span className="text-sm text-zinc-500">{r.k}</span>
              {r.href ? (
                <a
                  href={r.href}
                  target="_blank"
                  rel="noreferrer"
                  className={`text-sm text-zinc-200 transition-colors hover:text-gold ${r.mono ? "font-mono" : ""}`}
                >
                  {r.v} ↗
                </a>
              ) : (
                <span className={`text-sm text-zinc-200 ${r.mono ? "font-mono" : ""}`}>{r.v}</span>
              )}
            </div>
          ))}
        </div>

        {identity.explorer && (
          <a
            href={identity.explorer}
            target="_blank"
            rel="noreferrer"
            className="relative mt-5 inline-flex items-center gap-2 rounded-full bg-emerald px-5 py-2.5 text-sm font-semibold text-ink-950 transition-transform hover:scale-[1.03]"
          >
            View registration tx on BscScan ↗
          </a>
        )}
      </div>
    </Reveal>
  );
}

function CheckIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
      <path d="M20 6L9 17l-5-5" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
