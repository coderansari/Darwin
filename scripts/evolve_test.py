"""Offline evolution test — proves the GA converges with NO API key.
Run: python -m scripts.evolve_test
"""
from __future__ import annotations

from darwin.data_source import load_market_data
from darwin.evolve.engine import EvolutionConfig, Evolver

UNIVERSE = ["BTC", "ETH", "BNB", "SOL"]


def on_gen(gen, partial, ranked):
    h = partial.history[-1]
    print(f"  gen {gen}: best_fit={h['best_fitness']:+.3f} "
          f"mean_fit={h['mean_fitness']:+.3f} | {h['best']}")


def main() -> None:
    data = load_market_data(UNIVERSE, count=500, timeframe="1d", force_synthetic=True)
    cfg = EvolutionConfig(generations=8, pop_size=20, elite=3, seed=42)
    evolver = Evolver(data, generator=None, config=cfg)  # offline: no Claude

    print("Evolving (offline, deterministic operators only)...")
    result = evolver.evolve(UNIVERSE, context=None, on_generation=on_gen)

    print(f"\nEvaluated {result.evaluated} unique specs across {result.generations} generations.")
    print(f"\nCHAMPION: {result.champion.summary()}")
    print(result.champion.spec.to_json())
    print("\nHall of fame:")
    for r in result.hall_of_fame[:5]:
        print(f"  {r.summary()}")


if __name__ == "__main__":
    main()
