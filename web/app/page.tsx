import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { Hero } from "@/components/Hero";
import { Section } from "@/components/ui/Section";
import { ChampionCard } from "@/components/ChampionCard";
import { EquityChart } from "@/components/EquityChart";
import { MetricsGrid } from "@/components/MetricsGrid";
import { EvolutionTimeline } from "@/components/EvolutionTimeline";
import { FearGreedGauge } from "@/components/FearGreedGauge";
import { OnChainCard } from "@/components/OnChainCard";
import { SponsorStrip } from "@/components/SponsorStrip";
import { LiveEvolve } from "@/components/LiveEvolve";
import { LiveSentimentBadge } from "@/components/LiveSentimentBadge";
import { Reveal } from "@/components/ui/Reveal";
import { data } from "@/lib/data";

export default function Page() {
  const { champion, metrics, equity, history, fearGreed, identity, meta } = data;
  const live = meta.dataSource.toLowerCase().includes("live");

  return (
    <main>
      <Header live={live} />
      <Hero champion={champion} metrics={metrics} meta={meta} live={live} />

      <Section
        id="champion"
        eyebrow="The survivor"
        title="The evolved champion"
        intro="Not prompt-generated — bred. This strategy is the fittest spec the genetic algorithm produced after evaluating a full population on a deterministic backtester."
      >
        <ChampionCard champion={champion} metrics={metrics} />
        <div className="mt-5 grid gap-5 lg:grid-cols-5">
          <div className="lg:col-span-3">
            <Reveal>
              <EquityChart equity={equity} />
            </Reveal>
          </div>
          <div className="lg:col-span-2">
            <Reveal delay={0.1}>
              <div className="glass h-full rounded-3xl p-6">
                <div className="text-xs font-medium uppercase tracking-[0.16em] text-zinc-500">
                  Why it&apos;s trustworthy
                </div>
                <ul className="mt-4 space-y-3 text-sm leading-relaxed text-zinc-400">
                  <li className="flex gap-2.5">
                    <Dot /> Execution at <span className="text-zinc-200">next-bar open</span> — no same-bar fills, no lookahead.
                  </li>
                  <li className="flex gap-2.5">
                    <Dot /> PancakeSwap-realistic <span className="text-zinc-200">fees + slippage</span>.
                  </li>
                  <li className="flex gap-2.5">
                    <Dot /> Fitness penalizes <span className="text-zinc-200">over-trading, drawdown, and rule-fighting</span>.
                  </li>
                  <li className="flex gap-2.5">
                    <Dot /> <span className="text-zinc-200">{(metrics.ruleAdherence * 100).toFixed(0)}%</span> adherence to user risk rules.
                  </li>
                </ul>
              </div>
            </Reveal>
          </div>
        </div>

        <div className="mt-8">
          <Reveal>
            <h3 className="mb-4 text-sm font-medium uppercase tracking-[0.16em] text-zinc-500">
              Performance metrics
            </h3>
          </Reveal>
          <MetricsGrid metrics={metrics} />
        </div>
      </Section>

      <Section
        id="evolution"
        eyebrow="The differentiator"
        title="A population, bred across generations"
        intro={`Most "AI strategy" tools prompt an LLM once. Darwin evolves a population: select, crossover, mutate, repeat. Over ${meta.generations} generations the GA refined a high-churn idea into a low-drawdown champion.`}
      >
        <EvolutionTimeline history={history} />
        <div className="mt-5">
          <Reveal>
            <LiveEvolve />
          </Reveal>
        </div>
      </Section>

      <Section
        id="sentiment"
        eyebrow="Live market signal"
        title="Sentiment, not just price"
        intro="The CoinMarketCap Fear & Greed Index feeds directly into the strategy rules."
      >
        <div className="mb-5">
          <Reveal>
            <LiveSentimentBadge />
          </Reveal>
        </div>
        <FearGreedGauge fg={fearGreed} />
      </Section>

      <Section
        id="onchain"
        eyebrow="BNB Chain"
        title="A real on-chain identity"
      >
        <OnChainCard identity={identity} />
      </Section>

      <Section
        eyebrow="The full stack"
        title="Three sponsor integrations, wired end-to-end"
        intro="CoinMarketCap for data and signal, the BNB AI Agent SDK for identity, and the Trust Wallet Agent Kit for execution."
      >
        <SponsorStrip meta={meta} />
      </Section>

      <Footer identity={identity} />
    </main>
  );
}

function Dot() {
  return <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-gold" />;
}
