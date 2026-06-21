"""Out-of-sample validation — the difference between a real quant result and an
overfit one.

Darwin evolves on a TRAIN window, *selects* the champion on a VALIDATION window,
and reports its performance on a held-out TEST window the genetic algorithm never
saw. A strategy that survives this is robust, not curve-fit.

Cold-start guard: a naively sliced window starts with un-warmed indicators (an
EMA-100 needs 100 prior bars). Each non-train window therefore carries a WARMUP
buffer of preceding bars for indicator computation only — `run_backtest(trade_from=)`
ensures no trades or equity are counted before the window's true start.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .strategy.backtest import BacktestResult, run_backtest
from .strategy.spec import StrategySpec

# train / validation / test fractions of the timeline.
DEFAULT_SPLITS = (0.60, 0.20, 0.20)
# Warmup bars prepended to validation/test windows (covers EMA-100 + MACD slow).
WARMUP_BARS = 150


@dataclass
class OOSReport:
    train: BacktestResult
    validation: BacktestResult
    test: BacktestResult
    split_dates: tuple[pd.Timestamp, pd.Timestamp]  # (train_end, val_end)
    full: BacktestResult | None = None              # continuous run over all data


@dataclass
class HoldoutReport:
    """Clean 2-way in-sample vs out-of-sample holdout (for a fixed/locked champion,
    where no validation selection is needed)."""
    in_sample: BacktestResult
    out_sample: BacktestResult
    split_date: pd.Timestamp
    full: BacktestResult | None = None


def union_timeline(data: dict[str, pd.DataFrame]) -> pd.DatetimeIndex:
    frames = [df.index for df in data.values() if not df.empty]
    if not frames:
        return pd.DatetimeIndex([])
    return pd.DatetimeIndex(sorted(set().union(*[set(ix) for ix in frames])))


def split_dates(
    data: dict[str, pd.DataFrame], splits: tuple[float, float, float] = DEFAULT_SPLITS
) -> tuple[pd.DatetimeIndex, pd.Timestamp, pd.Timestamp]:
    tl = union_timeline(data)
    n = len(tl)
    i1 = max(1, int(n * splits[0]))
    i2 = max(i1 + 1, int(n * (splits[0] + splits[1])))
    i1 = min(i1, n - 1)
    i2 = min(i2, n - 1)
    return tl, tl[i1], tl[i2]


def _slice(
    data: dict[str, pd.DataFrame],
    signals: dict[str, pd.Series] | None,
    lo: pd.Timestamp | None,
    hi: pd.Timestamp | None,
):
    """Slice data + signals to [lo, hi). lo/hi None means open-ended."""
    def cut(ix: pd.DatetimeIndex) -> pd.Series:
        m = pd.Series(True, index=ix)
        if lo is not None:
            m &= ix >= lo
        if hi is not None:
            m &= ix < hi
        return m.to_numpy()

    out_d = {s: df[cut(df.index)] for s, df in data.items()}
    out_s = None
    if signals:
        out_s = {k: ser[cut(ser.index)] for k, ser in signals.items()}
    return out_d, out_s


def _window(data, signals, tl, trade_lo, hi, warmup=WARMUP_BARS):
    """Build a (data, signals, trade_from) window with a warmup buffer."""
    if trade_lo is None:
        d, s = _slice(data, signals, None, hi)
        return d, s, None
    lo_pos = int(tl.searchsorted(pd.Timestamp(trade_lo)))
    buf_ts = tl[max(0, lo_pos - warmup)]
    d, s = _slice(data, signals, buf_ts, hi)
    return d, s, trade_lo


def train_split(data, signals=None, splits: tuple[float, float, float] = DEFAULT_SPLITS):
    """Return the TRAIN slice (data, signals) plus the (train_end, val_end) dates.
    Evolution runs on this slice only — validation/test stay unseen."""
    tl, t1, t2 = split_dates(data, splits)
    d, s = _slice(data, signals, None, t1)
    return d, s, t1, t2


def evaluate_oos(
    spec: StrategySpec,
    data: dict[str, pd.DataFrame],
    signals: dict[str, pd.Series] | None = None,
    splits: tuple[float, float, float] = DEFAULT_SPLITS,
    with_full: bool = False,
) -> OOSReport:
    """Backtest `spec` on train / validation / test windows (and optionally the
    full continuous series for a single equity curve)."""
    tl, t1, t2 = split_dates(data, splits)

    dtr, str_, _ = _window(data, signals, tl, None, t1)
    rtr = run_backtest(spec, dtr, signals=str_)

    dv, sv, tfv = _window(data, signals, tl, t1, t2)
    rv = run_backtest(spec, dv, signals=sv, trade_from=tfv)

    dte, ste, tfte = _window(data, signals, tl, t2, None)
    rte = run_backtest(spec, dte, signals=ste, trade_from=tfte)

    full = run_backtest(spec, data, signals=signals) if with_full else None
    return OOSReport(train=rtr, validation=rv, test=rte, split_dates=(t1, t2), full=full)


def evaluate_holdout(
    spec: StrategySpec,
    data: dict[str, pd.DataFrame],
    signals: dict[str, pd.Series] | None = None,
    train_frac: float = 0.5,
    with_full: bool = False,
) -> HoldoutReport:
    """In-sample (first `train_frac`) vs out-of-sample (the rest, warmup-aware).
    The out-of-sample window is a true forward test — no look-ahead, cold-start-free."""
    tl = union_timeline(data)
    i = max(1, min(len(tl) - 1, int(len(tl) * train_frac)))
    split = tl[i]
    d_in, s_in = _slice(data, signals, None, split)
    r_in = run_backtest(spec, d_in, signals=s_in)
    d_out, s_out, tf = _window(data, signals, tl, split, None)
    r_out = run_backtest(spec, d_out, signals=s_out, trade_from=tf)
    full = run_backtest(spec, data, signals=signals) if with_full else None
    return HoldoutReport(in_sample=r_in, out_sample=r_out, split_date=split, full=full)


def select_by_validation(
    specs: list[StrategySpec],
    data: dict[str, pd.DataFrame],
    signals: dict[str, pd.Series] | None = None,
    splits: tuple[float, float, float] = DEFAULT_SPLITS,
    min_val_trades: int = 3,
) -> tuple[StrategySpec, OOSReport]:
    """Pick the champion that GENERALIZES, judged on the VALIDATION window only —
    the TEST window is never consulted for selection.

    Robustness gate: prefer specs that actually trade (>= `min_val_trades`) AND are
    positive on validation; rank those by validation fitness. This avoids crowning
    an in-sample overfit that doesn't trade (or loses) out-of-sample. Falls back to
    best validation fitness if nothing clears the gate.
    """
    scored: list[tuple[int, float, StrategySpec, OOSReport]] = []
    seen: set[str] = set()
    for spec in specs:
        fp = spec.fingerprint()
        if fp in seen:
            continue
        seen.add(fp)
        oos = evaluate_oos(spec, data, signals, splits)
        v = oos.validation.metrics
        robust = 1 if (v.num_trades >= min_val_trades and oos.validation.fitness > 0) else 0
        scored.append((robust, oos.validation.fitness, spec, oos))

    if not scored:  # empty input guard
        best = specs[0]
        return best, evaluate_oos(best, data, signals, splits)

    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    _, _, best_spec, best_oos = scored[0]
    return best_spec, best_oos
