"""Smoke test for the deterministic core. Run: python -m scripts.smoke_test

Validates indicators, condition evaluation, the backtester, and metrics against
seeded synthetic data — no API keys required.
"""
from __future__ import annotations

from darwin.data_source import load_market_data
from darwin.strategy.backtest import run_backtest
from darwin.strategy.spec import StrategySpec

UNIVERSE = ["BTC", "ETH", "BNB"]

GOLDEN_CROSS = {
    "name": "Golden Cross 10/30",
    "universe": UNIVERSE,
    "timeframe": "1d",
    "indicators": [
        {"id": "sma_fast", "type": "SMA", "source": "close", "period": 10},
        {"id": "sma_slow", "type": "SMA", "source": "close", "period": 30},
    ],
    "entry": {"all": [{"left": "sma_fast", "op": "cross_above", "right": "sma_slow"}]},
    "exit": {"any": [{"left": "sma_fast", "op": "cross_below", "right": "sma_slow"}]},
    "risk": {
        "max_position_pct": 0.3, "max_open_positions": 3,
        "stop_loss_pct": 0.1, "take_profit_pct": 0.3,
        "max_drawdown_pct": 0.35, "trailing_stop_pct": 0.0,
    },
    "sizing": {"type": "equal_weight"},
    "rationale": "ride medium-term trends via a moving-average crossover",
}

RSI_REVERSION = {
    "name": "RSI Mean Reversion",
    "universe": UNIVERSE,
    "timeframe": "1d",
    "indicators": [{"id": "rsi", "type": "RSI", "period": 14}],
    "entry": {"all": [{"left": "rsi", "op": "<", "right": 30}]},
    "exit": {"any": [{"left": "rsi", "op": ">", "right": 55}]},
    "risk": {
        "max_position_pct": 0.25, "max_open_positions": 2,
        "stop_loss_pct": 0.08, "take_profit_pct": 0.15,
        "max_drawdown_pct": 0.25, "trailing_stop_pct": 0.05,
    },
    "sizing": {"type": "equal_weight"},
    "rationale": "buy oversold dips, exit on momentum recovery",
}


def main() -> None:
    data = load_market_data(UNIVERSE, count=400, timeframe="1d", force_synthetic=True)
    print(f"Loaded synthetic data: {[f'{s}:{len(df)}bars' for s, df in data.items()]}\n")

    for raw in (GOLDEN_CROSS, RSI_REVERSION):
        spec = StrategySpec.from_dict(raw)
        result = run_backtest(spec, data)
        print(result.summary())
        m = result.metrics
        print(
            f"    final_equity=${m.final_equity:,.0f}  win_rate={m.win_rate:.0%}  "
            f"exposure={m.exposure:.0%}  sortino={m.sortino:.2f}  calmar={m.calmar:.2f}"
        )
        for t in result.trades[:3]:
            print(f"    trade {t['symbol']}: {t['ret']:+.1%} via {t['reason']}")
        print()


if __name__ == "__main__":
    main()
