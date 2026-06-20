"""Performance + risk metrics computed from a backtest result.

The fitness function (evolve/) consumes these. We deliberately surface the
metrics the hackathon judges named: returns, drawdown, risk-adjusted
performance, and rule adherence.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

# Bars per year per timeframe, for annualization.
_ANNUALIZATION = {"1d": 365, "4h": 6 * 365, "1h": 24 * 365, "1w": 52}


@dataclass
class Metrics:
    total_return: float = 0.0
    cagr: float = 0.0
    ann_vol: float = 0.0
    sharpe: float = 0.0
    sortino: float = 0.0
    max_drawdown: float = 0.0      # negative number, e.g. -0.23
    calmar: float = 0.0
    win_rate: float = 0.0
    num_trades: int = 0
    exposure: float = 0.0          # fraction of bars with >=1 open position
    rule_adherence: float = 1.0    # 1.0 = never violated the spec's risk rules
    final_equity: float = 0.0

    def as_dict(self) -> dict:
        return asdict(self)


def _max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    running_max = equity.cummax()
    dd = equity / running_max - 1.0
    return float(dd.min())


def compute_metrics(
    equity: pd.Series,
    trades: list[dict],
    timeframe: str,
    rule_checks: int,
    rule_violations: int,
    exposure_bars: int,
) -> Metrics:
    if equity.empty or len(equity) < 2:
        return Metrics()

    ppy = _ANNUALIZATION.get(timeframe, 365)
    start_eq = float(equity.iloc[0])
    end_eq = float(equity.iloc[-1])
    total_return = end_eq / start_eq - 1.0

    rets = equity.pct_change().dropna()
    n = len(rets)
    years = n / ppy if ppy else 0.0
    cagr = (end_eq / start_eq) ** (1.0 / years) - 1.0 if years > 0 and start_eq > 0 else 0.0

    ann_vol = float(rets.std(ddof=0) * math.sqrt(ppy)) if n > 1 else 0.0
    mean_ann = float(rets.mean() * ppy)
    sharpe = mean_ann / ann_vol if ann_vol > 1e-9 else 0.0

    downside = rets[rets < 0]
    down_vol = float(downside.std(ddof=0) * math.sqrt(ppy)) if len(downside) > 1 else 0.0
    sortino = mean_ann / down_vol if down_vol > 1e-9 else 0.0

    mdd = _max_drawdown(equity)
    calmar = cagr / abs(mdd) if mdd < -1e-9 else 0.0

    wins = sum(1 for t in trades if t.get("pnl", 0.0) > 0)
    num_trades = len(trades)
    win_rate = wins / num_trades if num_trades else 0.0

    exposure = exposure_bars / len(equity) if len(equity) else 0.0
    adherence = 1.0 - (rule_violations / rule_checks) if rule_checks else 1.0

    return Metrics(
        total_return=total_return,
        cagr=cagr,
        ann_vol=ann_vol,
        sharpe=sharpe,
        sortino=sortino,
        max_drawdown=mdd,
        calmar=calmar,
        win_rate=win_rate,
        num_trades=num_trades,
        exposure=exposure,
        rule_adherence=float(np.clip(adherence, 0.0, 1.0)),
        final_equity=end_eq,
    )
