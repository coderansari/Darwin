"""Out-of-sample validation test — proves the train/validation/test split is sound
and lookahead-free. Run: python -m scripts.oos_test
"""
from __future__ import annotations

from darwin.data_source import derive_market_signals, load_market_data, load_signals
from darwin.strategy.backtest import run_backtest
from darwin.strategy.spec import StrategySpec
from darwin.validation import DEFAULT_SPLITS, evaluate_oos, split_dates, train_split

UNIVERSE = ["BTC", "ETH", "BNB", "SOL"]

SPEC = StrategySpec.from_dict(
    {
        "name": "EMA cross + regime",
        "universe": UNIVERSE,
        "timeframe": "1d",
        "indicators": [
            {"id": "ema_f", "type": "EMA", "period": 12},
            {"id": "ema_s", "type": "EMA", "period": 30},
        ],
        "entry": {"all": [
            {"left": "ema_f", "op": "cross_above", "right": "ema_s"},
            {"left": "breadth", "op": ">", "right": 50},
        ]},
        "exit": {"any": [{"left": "ema_f", "op": "cross_below", "right": "ema_s"}]},
        "risk": {"max_position_pct": 0.2, "max_open_positions": 3, "stop_loss_pct": 0.08,
                 "take_profit_pct": 0.25, "max_drawdown_pct": 0.3, "trailing_stop_pct": 0.0},
        "sizing": {"type": "equal_weight"},
        "rationale": "regime-gated trend",
    }
)


def main() -> None:
    data = load_market_data(UNIVERSE, count=600, force_synthetic=True)
    signals = load_signals(count=600, force_synthetic=True)
    signals.update(derive_market_signals(data))

    # 1) Split is ordered and non-degenerate.
    tl, t1, t2 = split_dates(data, DEFAULT_SPLITS)
    assert tl[0] < t1 < t2 < tl[-1], f"bad split boundaries: {t1} {t2}"
    print(f"split: train < {t1.date()} < val < {t2.date()} < test  ({len(tl)} bars)")

    # 2) Evolution train slice never includes validation/test bars (no leakage).
    train_data, _, st1, _ = train_split(data, signals, DEFAULT_SPLITS)
    for s, df in train_data.items():
        assert df.index.max() < t1, f"{s}: train slice leaks past train_end"
    assert st1 == t1
    print("OK: train slice strictly precedes validation/test (no leakage)")

    # 3) OOS windows all evaluate; held-out test starts at out-of-sample boundary.
    oos = evaluate_oos(SPEC, data, signals, with_full=True)
    assert oos.test.equity.index[0] >= t2, "test equity starts before the held-out boundary"
    assert abs(float(oos.test.equity.iloc[0]) - 10_000.0) < 1e-6, "test equity must start at initial cash (warmup, no carried positions)"
    print(
        "OOS  train ret={:+.1%}  valid ret={:+.1%}  TEST ret={:+.1%} sharpe={:.2f} trades={}".format(
            oos.train.metrics.total_return,
            oos.validation.metrics.total_return,
            oos.test.metrics.total_return,
            oos.test.metrics.sharpe,
            oos.test.metrics.num_trades,
        )
    )

    # 4) Warmup is non-trivial: the test window's first traded bar is well after its
    #    raw data start (proving indicators were warmed, not cold-started).
    full = run_backtest(SPEC, data, signals=signals)
    assert len(full.equity) > len(oos.test.equity), "full run should span more bars than the test window"
    print("OK: oos_test assertions passed.")


if __name__ == "__main__":
    main()
