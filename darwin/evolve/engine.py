"""The evolution engine — a genetic algorithm over StrategySpecs.

Hybrid design:
  * Deterministic operators (mutate.py) run every generation: fast, free, reproducible.
  * Claude operators (generate.py) inject creative diversity and metric-guided
    "insight" mutations when an API key is present.

Fitness is the backtest score (backtest.fitness_score), which mirrors the
hackathon rubric: risk-adjusted return, drawdown penalty, rule adherence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np
import pandas as pd

from ..strategy.backtest import BacktestResult, run_backtest
from ..strategy.spec import StrategySpec
from . import mutate as ops
from .seeds import seed_library


@dataclass
class EvolutionConfig:
    generations: int = 6
    pop_size: int = 16
    elite: int = 3
    tournament: int = 3
    crossover_rate: float = 0.4
    mutation_ops: int = 2          # max deterministic ops per mutation
    seed: int = 7
    llm_seed_count: int = 6        # Claude specs added to the initial pool
    llm_mutations_per_gen: int = 2 # Claude insight-mutations of the champion per gen


@dataclass
class EvolutionResult:
    champion: BacktestResult
    hall_of_fame: list[BacktestResult]
    history: list[dict] = field(default_factory=list)
    generations: int = 0
    evaluated: int = 0


GenCallback = Optional[Callable[[int, "EvolutionResult", list[BacktestResult]], None]]


class Evolver:
    def __init__(
        self,
        data: dict[str, pd.DataFrame],
        signals: dict[str, pd.Series] | None = None,
        generator=None,                 # StrategyGenerator | None
        config: EvolutionConfig | None = None,
    ):
        self.data = data
        self.signals = signals
        self.generator = generator
        self.cfg = config or EvolutionConfig()
        self.rng = np.random.default_rng(self.cfg.seed)
        self._cache: dict[str, BacktestResult] = {}
        self.evaluated = 0

    # ---- evaluation --------------------------------------------------------

    def _evaluate(self, spec: StrategySpec) -> BacktestResult:
        fp = spec.fingerprint()
        if fp in self._cache:
            return self._cache[fp]
        result = run_backtest(spec, self.data, signals=self.signals)
        self._cache[fp] = result
        self.evaluated += 1
        return result

    def _evaluate_many(self, specs: list[StrategySpec]) -> list[BacktestResult]:
        out: list[BacktestResult] = []
        seen: set[str] = set()
        for s in specs:
            fp = s.fingerprint()
            if fp in seen:
                continue
            seen.add(fp)
            out.append(self._evaluate(s))
        out.sort(key=lambda r: r.fitness, reverse=True)
        return out

    def evaluated_specs(self) -> list[StrategySpec]:
        """Every unique spec the GA scored on train — the full candidate pool for
        out-of-sample selection (far more diverse than the train-fitness top-k)."""
        return [r.spec for r in self._cache.values()]

    # ---- population --------------------------------------------------------

    def _init_population(self, universe: list[str], context: str | None) -> list[StrategySpec]:
        specs = [StrategySpec.from_dict(d) for d in seed_library(universe)]

        # Claude-seeded diversity.
        if self.generator and self.generator.enabled and context is not None:
            try:
                specs += self.generator.generate_population(
                    context, self.cfg.llm_seed_count, universe
                )
            except Exception as e:  # never let the LLM crash evolution
                print(f"[evolve] Claude seeding skipped: {e}")

        # Fill out the pool with mutations of the seeds.
        while len(specs) < self.cfg.pop_size:
            parent = specs[int(self.rng.integers(0, len(specs)))]
            specs.append(ops.mutate(parent, self.rng, self.cfg.mutation_ops))
        return specs

    def _tournament(self, ranked: list[BacktestResult]) -> BacktestResult:
        picks = self.rng.choice(len(ranked), size=min(self.cfg.tournament, len(ranked)), replace=False)
        best = min(int(p) for p in picks)  # ranked is sorted desc => lowest index = best
        return ranked[best]

    def _breed(self, ranked: list[BacktestResult]) -> StrategySpec:
        if self.rng.random() < self.cfg.crossover_rate and len(ranked) >= 2:
            a = self._tournament(ranked).spec
            b = self._tournament(ranked).spec
            child = ops.crossover(a, b, self.rng)
            return ops.mutate(child, self.rng, 1) if self.rng.random() < 0.5 else child
        parent = self._tournament(ranked).spec
        return ops.mutate(parent, self.rng, self.cfg.mutation_ops)

    # ---- main loop ---------------------------------------------------------

    def evolve(
        self,
        universe: list[str],
        context: str | None = None,
        on_generation: GenCallback = None,
    ) -> EvolutionResult:
        population = self._init_population(universe, context)
        ranked = self._evaluate_many(population)

        history: list[dict] = []
        hall: dict[str, BacktestResult] = {}

        for gen in range(self.cfg.generations):
            champion = ranked[0]
            for r in ranked[: self.cfg.elite]:
                hall[r.spec.fingerprint()] = r

            fits = [r.fitness for r in ranked]
            history.append({
                "generation": gen,
                "best_fitness": round(champion.fitness, 4),
                "mean_fitness": round(float(np.mean(fits)), 4),
                "best": champion.summary(),
            })

            partial = EvolutionResult(
                champion=champion,
                hall_of_fame=sorted(hall.values(), key=lambda r: r.fitness, reverse=True)[:10],
                history=history,
                generations=gen + 1,
                evaluated=self.evaluated,
            )
            if on_generation:
                on_generation(gen, partial, ranked)

            if gen == self.cfg.generations - 1:
                break

            # ---- produce next generation ----
            next_specs = [r.spec for r in ranked[: self.cfg.elite]]  # elitism

            # Claude insight-mutations of the champion (metric-guided).
            if self.generator and self.generator.enabled and context is not None:
                for _ in range(self.cfg.llm_mutations_per_gen):
                    try:
                        child = self.generator.claude_mutate(champion.spec, champion.metrics, context)
                        if child is not None:
                            next_specs.append(child)
                    except Exception as e:
                        print(f"[evolve] Claude mutation skipped: {e}")
                        break

            while len(next_specs) < self.cfg.pop_size:
                next_specs.append(self._breed(ranked))

            ranked = self._evaluate_many(next_specs)

        champion = ranked[0] if ranked[0].fitness >= max(r.fitness for r in hall.values()) \
            else max(hall.values(), key=lambda r: r.fitness)

        return EvolutionResult(
            champion=champion,
            hall_of_fame=sorted(hall.values(), key=lambda r: r.fitness, reverse=True)[:10],
            history=history,
            generations=self.cfg.generations,
            evaluated=self.evaluated,
        )
