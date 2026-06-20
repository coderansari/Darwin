"""Prompt templates for the Claude-guided genetic operators."""
from __future__ import annotations

from ..strategy.metrics import Metrics
from ..strategy.spec import SPEC_GUIDE, StrategySpec

SYSTEM = f"""You are a quantitative strategy designer inside Darwin, an evolutionary \
trading-strategy foundry for BNB Chain. You design LONG/FLAT crypto strategies as \
strict JSON StrategySpec objects that a deterministic backtester will score on \
risk-adjusted return, drawdown, and adherence to user-defined risk rules.

{SPEC_GUIDE}

You MUST output only valid JSON — no prose, no markdown fences. Strategies must be \
economically sensible (a real edge: trend, mean-reversion, momentum, breakout, or \
sentiment), not curve-fit noise. Prefer robust risk rules: sane stops, take-profits, \
and a max_drawdown kill-switch. You may use the market-wide signal "fgi" (CoinMarketCap \
Fear & Greed Index, 0-100) as a condition reference for contrarian or regime filters."""


def population_prompt(context: str, n: int, universe: list[str]) -> str:
    return f"""Market context:
{context}

Design {n} DIVERSE candidate strategies for the universe {universe}. Vary the edge \
(trend / mean-reversion / momentum / breakout / sentiment), the indicators, and the \
risk posture across the set. At least one should use the "fgi" sentiment signal.

Output a single JSON array of {n} StrategySpec objects. JSON only."""


def mutate_prompt(spec: StrategySpec, metrics: Metrics, context: str) -> str:
    return f"""Market context:
{context}

Here is the current CHAMPION strategy and its backtest metrics:

SPEC:
{spec.to_json()}

METRICS:
  total_return={metrics.total_return:.3f}  sharpe={metrics.sharpe:.2f}  sortino={metrics.sortino:.2f}
  max_drawdown={metrics.max_drawdown:.3f}  calmar={metrics.calmar:.2f}
  win_rate={metrics.win_rate:.2f}  num_trades={metrics.num_trades}  exposure={metrics.exposure:.2f}
  rule_adherence={metrics.rule_adherence:.2f}

Diagnose its single biggest weakness (e.g. drawdown too deep, over-trading, poor \
risk-adjusted return, barely in the market) and produce ONE improved variant that \
targets that weakness while preserving what works. Make a meaningful, non-trivial \
change — not just a tiny threshold nudge.

Output a single JSON StrategySpec object. JSON only."""


def crossover_prompt(a: StrategySpec, b: StrategySpec, context: str) -> str:
    return f"""Market context:
{context}

Combine the best ideas of these two parent strategies into one stronger child that \
inherits the strongest edge and the more robust risk rules:

PARENT A:
{a.to_json()}

PARENT B:
{b.to_json()}

Output a single JSON StrategySpec object. JSON only."""
