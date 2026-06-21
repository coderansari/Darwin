import { Logo } from "./brand/Logo";
import type { Identity } from "@/lib/data";
import { shortAddr } from "@/lib/data";

const GITHUB = "https://github.com/coderansari/darwin";

export function Footer({ identity }: { identity: Identity }) {
  return (
    <footer className="relative mt-12 border-t border-white/[0.06]">
      <div className="mx-auto max-w-6xl px-5 py-14 sm:px-8">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          <div className="lg:col-span-1">
            <div className="flex items-center gap-2.5">
              <Logo size={28} />
              <span className="text-lg font-semibold tracking-tight text-white">Darwin</span>
            </div>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-zinc-500">
              An evolutionary trading-strategy foundry for BNB Chain. It breeds a
              population of backtestable strategies into a champion.
            </p>
          </div>

          <FooterCol
            title="Project"
            links={[
              { label: "GitHub", href: GITHUB },
              { label: "BNB Hack · Track 2", href: GITHUB },
              { label: "MIT License", href: `${GITHUB}/blob/main/LICENSE` },
            ]}
          />
          <FooterCol
            title="Sponsors"
            links={[
              { label: "CoinMarketCap", href: "https://coinmarketcap.com/api/" },
              { label: "BNB AI Agent SDK", href: "https://www.bnbchain.org/" },
              { label: "Trust Wallet Agent Kit", href: "https://trustwallet.com/" },
            ]}
          />
          <FooterCol
            title="On-chain"
            links={[
              identity.explorer
                ? { label: `Identity tx · agent #${identity.agentId}`, href: identity.explorer }
                : { label: "Identity", href: GITHUB },
              { label: `Registry ${shortAddr(identity.registry)}`, href: `https://testnet.bscscan.com/address/${identity.registry}` },
              { label: `Wallet ${shortAddr(identity.wallet)}`, href: `https://testnet.bscscan.com/address/${identity.wallet}` },
            ]}
          />
        </div>

        <div className="mt-12 flex flex-col items-start justify-between gap-4 border-t border-white/[0.06] pt-6 text-sm text-zinc-500 sm:flex-row sm:items-center">
          <p>Built for BNB Hack 2026 · evolved on live CoinMarketCap data.</p>
          <p className="font-mono text-xs text-zinc-600">
            ERC-8004 agent #{identity.agentId} · {identity.network}
          </p>
        </div>
      </div>
    </footer>
  );
}

function FooterCol({ title, links }: { title: string; links: { label: string; href: string }[] }) {
  return (
    <div>
      <h4 className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">{title}</h4>
      <ul className="mt-4 space-y-2.5">
        {links.map((l) => (
          <li key={l.label}>
            <a
              href={l.href}
              target="_blank"
              rel="noreferrer"
              className="text-sm text-zinc-400 transition-colors hover:text-gold"
            >
              {l.label}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
