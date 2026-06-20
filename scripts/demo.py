"""End-to-end narrated demo. Run: python -m scripts.demo

Shows the full Darwin pipeline: CMC data + Fear&Greed -> evolve a population ->
champion strategy -> backtest report -> rule-gated execution plan. Works with no
API keys (synthetic fallback); set keys in .env to run it live.
"""
from __future__ import annotations

from darwin import report
from darwin.config import settings
from darwin.data_source import load_market_data, load_signals
from darwin.evolve.engine import EvolutionConfig, Evolver
from darwin.evolve.generate import StrategyGenerator, market_context

UNIVERSE = ["BTC", "ETH", "BNB", "SOL"]


def banner(t: str) -> None:
    print("\n" + "=" * 70 + f"\n  {t}\n" + "=" * 70)


def main() -> None:
    live = settings.has_cmc
    banner("1. DATA - CoinMarketCap market data + Fear & Greed signal")
    data = load_market_data(UNIVERSE, count=500, force_synthetic=not live)
    signals = load_signals(count=500, force_synthetic=not live)
    fgi_now = float(signals["fgi"].iloc[-1])
    print(f"  universe: {UNIVERSE}  ({'live CMC' if live else 'synthetic'} data)")
    print(f"  Fear & Greed now: {fgi_now:.0f}/100")

    banner("2. EVOLVE - breed a population, score on the judges' rubric")
    generator = StrategyGenerator() if settings.has_anthropic else None
    print(f"  Claude operators: {'on' if (generator and generator.enabled) else 'off (deterministic)'}")
    evolver = Evolver(data, signals=signals, generator=generator,
                      config=EvolutionConfig(generations=8, pop_size=22, seed=42))
    context = market_context(data, {"value": int(fgi_now), "value_classification": ""})

    def on_gen(gen, partial, ranked):
        h = partial.history[-1]
        print(f"  gen {gen}: best fitness {h['best_fitness']:+.3f}  ({h['best'].split('[')[0].strip()})")

    result = evolver.evolve(UNIVERSE, context=context, on_generation=on_gen)

    banner("3. CHAMPION - the evolved strategy")
    c = result.champion
    m = c.metrics
    print(f"  {c.spec.name}")
    print(f"  return {m.total_return:+.1%} | Sharpe {m.sharpe:.2f} | maxDD {m.max_drawdown:.1%} "
          f"| trades {m.num_trades} | rule-adherence {m.rule_adherence:.0%}")
    print(f"  indicators: {[i.type for i in c.spec.indicators]}")

    run_dir = report.render(result, meta={"data_source": "live" if live else "synthetic",
                                          "bars": 500, "llm": "on" if generator and generator.enabled else "off"})
    print(f"  full report -> {run_dir / 'report.md'}")

    banner("4. EXECUTE - evaluate live signal, plan a rule-gated swap (dry-run)")
    from darwin.execute.twak import execute_spec
    execute_spec(c.spec, live=False, amount=25.0)

    banner("DONE - champion spec is backtestable, executable, and ready to register on BNB")


if __name__ == "__main__":
    main()
