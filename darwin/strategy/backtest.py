"""Deterministic event-driven backtester.

Convention (lookahead-free):
  * Signals are evaluated on the CLOSE of bar t-1.
  * Orders execute at the OPEN of bar t.
  * Stops / take-profits are checked against bar t's HIGH/LOW.
  * Equity is marked at the CLOSE of bar t.

Strategies are LONG/FLAT only. The same risk engine used here is what the live
executor (execute/twak.py) enforces on-chain — so a Darwin strategy adheres to
its user-defined rules by construction.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from .indicators import compute_all
from .metrics import Metrics, compute_metrics
from .spec import StrategySpec

INITIAL_CASH = 10_000.0
# Realistic round-trip frictions. PancakeSwap v2 charges 0.25% per swap; we add
# slippage on top. Charged on BOTH entry and exit. This is what stops the GA from
# "winning" by churning thousands of micro-trades.
DEFAULT_FEE_PCT = 0.0025
DEFAULT_SLIPPAGE_PCT = 0.0010


# ---------------------------------------------------------------------------
# Vectorized condition evaluation
# ---------------------------------------------------------------------------


def _resolve(ref: Any, frame: pd.DataFrame) -> pd.Series:
    if isinstance(ref, (int, float)) and not isinstance(ref, bool):
        return pd.Series(float(ref), index=frame.index)
    if isinstance(ref, str) and ref in frame.columns:
        return frame[ref]
    # Unknown reference -> all-NaN (never fires). Validation should prevent this.
    return pd.Series(np.nan, index=frame.index)


def eval_condition(node: dict[str, Any], frame: pd.DataFrame) -> pd.Series:
    if "all" in node:
        parts = [eval_condition(c, frame) for c in node["all"]]
        out = parts[0]
        for p in parts[1:]:
            out = out & p
        return out.fillna(False)
    if "any" in node:
        parts = [eval_condition(c, frame) for c in node["any"]]
        out = parts[0]
        for p in parts[1:]:
            out = out | p
        return out.fillna(False)

    left = _resolve(node["left"], frame)
    right = _resolve(node["right"], frame)
    op = node["op"]
    if op == ">":
        res = left > right
    elif op == "<":
        res = left < right
    elif op == ">=":
        res = left >= right
    elif op == "<=":
        res = left <= right
    elif op == "cross_above":
        res = (left > right) & (left.shift(1) <= right.shift(1))
    elif op == "cross_below":
        res = (left < right) & (left.shift(1) >= right.shift(1))
    else:
        raise ValueError(f"bad operator {op}")
    return res.fillna(False)


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------


@dataclass
class BacktestResult:
    spec: StrategySpec
    metrics: Metrics
    equity: pd.Series
    trades: list[dict] = field(default_factory=list)

    @property
    def fitness(self) -> float:
        return fitness_score(self.metrics)

    def summary(self) -> str:
        m = self.metrics
        return (
            f"{self.spec.name} [{self.spec.fingerprint()}] "
            f"ret={m.total_return:+.1%} cagr={m.cagr:+.1%} "
            f"sharpe={m.sharpe:.2f} maxDD={m.max_drawdown:.1%} "
            f"trades={m.num_trades} adher={m.rule_adherence:.0%} "
            f"fit={fitness_score(m):.3f}"
        )


def fitness_score(m: Metrics) -> float:
    """Bounded, robust fitness that mirrors the judges' rubric and resists
    reward-hacking (over-trading, compounding flukes, rule-fighting).

    - risk-adjusted core uses Sortino+Sharpe, each CLAMPED to +-5 so a
      lucky tiny-drawdown run can't produce an astronomical Calmar.
    - drawdown is penalized multiplicatively.
    - total return is capped before it can contribute.
    - rule adherence is SQUARED: a strategy that constantly fights its own
      risk rules (low adherence) is heavily penalized.
    - turnover is penalized continuously: more trades => more cost & fragility.
    """
    if m.num_trades == 0:
        return 0.0
    sortino = float(np.clip(m.sortino, -5.0, 5.0))
    sharpe = float(np.clip(m.sharpe, -5.0, 5.0))
    ret = float(np.clip(m.total_return, -1.0, 2.0))

    risk_adj = 0.5 * sortino + 0.5 * sharpe
    score = risk_adj / (1.0 + abs(m.max_drawdown) * 3.0)
    score += 0.3 * ret
    score *= m.rule_adherence ** 2               # coherence gate
    score /= (1.0 + m.num_trades / 40.0)         # turnover penalty (over-trading)
    if m.exposure < 0.02:                         # never really in the market
        score *= 0.3
    if m.num_trades < 8:                          # too few trades to be statistically trustworthy
        score *= max(0.15, m.num_trades / 8.0)
    return float(score)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


def run_backtest(
    spec: StrategySpec,
    data: dict[str, pd.DataFrame],
    signals: dict[str, pd.Series] | None = None,
    initial_cash: float = INITIAL_CASH,
    fee_pct: float = DEFAULT_FEE_PCT,
    slippage_pct: float = DEFAULT_SLIPPAGE_PCT,
) -> BacktestResult:
    """Run `spec` against `data` (symbol -> OHLCV DataFrame, DatetimeIndex).

    `signals` is an optional map of market-wide series (e.g. {"fgi": <Fear&Greed
    series>}) that conditions may reference by name. `fee_pct`/`slippage_pct` are
    charged on every entry and exit leg.
    """
    spec.validate()
    cost_mult = fee_pct + slippage_pct

    symbols = [s for s in spec.universe if s in data and not data[s].empty]
    if not symbols:
        empty = pd.Series(dtype=float)
        return BacktestResult(spec, Metrics(), empty, [])

    # Master timeline = sorted union of all symbol timestamps.
    timeline = sorted(set().union(*[set(data[s].index) for s in symbols]))
    timeline = pd.DatetimeIndex(timeline)

    # Per-symbol arrays aligned to the master timeline.
    opens, highs, lows, marks, entry_sig, exit_sig = {}, {}, {}, {}, {}, {}
    for s in symbols:
        df = data[s].sort_index()
        frame = df.copy()
        ind = compute_all(spec.indicators, df)
        for col in ind.columns:
            frame[col] = ind[col]
        if signals:
            for name, series in signals.items():
                frame[name] = series.reindex(df.index).ffill()
        es = eval_condition(spec.entry, frame).reindex(timeline).fillna(False)
        xs = eval_condition(spec.exit, frame).reindex(timeline).fillna(False)
        o = df["open"].reindex(timeline)
        h = df["high"].reindex(timeline)
        l = df["low"].reindex(timeline)
        c = df["close"].reindex(timeline).ffill()  # carry last price for valuation
        opens[s] = o.to_numpy(dtype=float)
        highs[s] = h.to_numpy(dtype=float)
        lows[s] = l.to_numpy(dtype=float)
        marks[s] = c.to_numpy(dtype=float)
        entry_sig[s] = es.to_numpy(dtype=bool)
        exit_sig[s] = xs.to_numpy(dtype=bool)

    risk = spec.risk
    cash = initial_cash
    positions: dict[str, dict] = {}   # symbol -> {qty, entry, stop, tp, peak}
    equity_curve = np.empty(len(timeline), dtype=float)
    trades: list[dict] = []
    peak_equity = initial_cash
    halted = False
    exposure_bars = 0
    rule_checks = 0
    rule_violations = 0

    def mark_equity(t: int) -> float:
        val = cash
        for s, p in positions.items():
            px = marks[s][t]
            if not np.isnan(px):
                val += p["qty"] * px
        return val

    def close_position(s: str, price: float, t: int, reason: str) -> None:
        nonlocal cash
        p = positions.pop(s)
        proceeds = p["qty"] * price * (1.0 - cost_mult)
        cash += proceeds
        pnl = proceeds - p["cost_basis"]
        trades.append(
            {
                "symbol": s,
                "entry": p["entry"],
                "exit": price,
                "qty": p["qty"],
                "pnl": pnl,
                "ret": proceeds / p["cost_basis"] - 1.0 if p["cost_basis"] else 0.0,
                "bars_held": int(t) - p["entry_bar"],
                "exit_bar": int(t),
                "reason": reason,
            }
        )

    for t in range(len(timeline)):
        # (a) signal-driven exits at this bar's open (signal formed at t-1).
        if t > 0:
            for s in list(positions.keys()):
                if exit_sig[s][t - 1] and not np.isnan(opens[s][t]):
                    close_position(s, opens[s][t], t, "signal")

        # (b) signal-driven entries at this bar's open.
        if t > 0 and not halted:
            for s in symbols:
                if s in positions:
                    continue
                if not entry_sig[s][t - 1]:
                    continue
                px = opens[s][t]
                if np.isnan(px) or px <= 0:
                    continue
                rule_checks += 1
                if len(positions) >= risk.max_open_positions:
                    rule_violations += 1   # alpha wanted in, risk rules said no
                    continue
                equity_now = mark_equity(t)
                if spec.sizing.type == "fixed_fraction":
                    target = spec.sizing.fraction * equity_now
                else:  # equal_weight
                    target = risk.max_position_pct * equity_now
                target = min(target, risk.max_position_pct * equity_now, cash)
                if target <= 0:
                    rule_violations += 1
                    continue
                qty = target / (px * (1.0 + cost_mult))
                cost_basis = qty * px * (1.0 + cost_mult)
                cash -= cost_basis
                positions[s] = {
                    "qty": qty,
                    "entry": px,
                    "cost_basis": cost_basis,
                    "stop": px * (1.0 - risk.stop_loss_pct),
                    "tp": px * (1.0 + risk.take_profit_pct),
                    "peak": px,
                    "entry_bar": t,
                }

        # (c) intrabar stop / take-profit / trailing checks on bar t.
        #     A position opened at this bar's open is NOT eligible for an intrabar
        #     fill on the same bar (we have no sub-candle data — that would be a
        #     lookahead exploit). It becomes eligible from the next bar.
        for s in list(positions.keys()):
            p = positions[s]
            if t == p["entry_bar"]:
                continue
            hi, lo = highs[s][t], lows[s][t]
            if np.isnan(hi) or np.isnan(lo):
                continue
            if risk.trailing_stop_pct > 0:
                p["peak"] = max(p["peak"], hi)
                trail = p["peak"] * (1.0 - risk.trailing_stop_pct)
                p["stop"] = max(p["stop"], trail)
            if lo <= p["stop"]:                       # stop assumed to fill first
                close_position(s, p["stop"], t, "stop")
            elif hi >= p["tp"]:
                close_position(s, p["tp"], t, "take_profit")

        # (d) portfolio drawdown kill-switch (rule adherence in action).
        eq = mark_equity(t)
        peak_equity = max(peak_equity, eq)
        if not halted and peak_equity > 0 and (eq / peak_equity - 1.0) <= -risk.max_drawdown_pct:
            for s in list(positions.keys()):
                px = marks[s][t]
                if not np.isnan(px):
                    close_position(s, px, t, "max_drawdown")
            halted = True

        if positions:
            exposure_bars += 1
        equity_curve[t] = mark_equity(t)

    equity = pd.Series(equity_curve, index=timeline, name="equity")
    metrics = compute_metrics(
        equity, trades, spec.timeframe, rule_checks, rule_violations, exposure_bars
    )
    return BacktestResult(spec, metrics, equity, trades)
