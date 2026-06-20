"""Seed strategy templates — the initial gene pool.

These are classic, economically-grounded archetypes. Evolution mutates and
crosses them (and Claude injects fresh ones) to search for an edge. Keeping a
deterministic seed library means Darwin always has a viable starting population
even with no API key.
"""
from __future__ import annotations

from .. config import settings  # noqa: F401  (kept for parity / future use)


def _risk(**overrides) -> dict:
    base = {
        "max_position_pct": 0.25,
        "max_open_positions": 3,
        "stop_loss_pct": 0.08,
        "take_profit_pct": 0.20,
        "max_drawdown_pct": 0.30,
        "trailing_stop_pct": 0.0,
    }
    base.update(overrides)
    return base


def golden_cross(universe: list[str], fast: int = 20, slow: int = 50) -> dict:
    return {
        "name": f"Golden Cross {fast}/{slow}",
        "universe": universe,
        "timeframe": "1d",
        "indicators": [
            {"id": "ma_fast", "type": "EMA", "source": "close", "period": fast},
            {"id": "ma_slow", "type": "EMA", "source": "close", "period": slow},
        ],
        "entry": {"all": [{"left": "ma_fast", "op": "cross_above", "right": "ma_slow"}]},
        "exit": {"any": [{"left": "ma_fast", "op": "cross_below", "right": "ma_slow"}]},
        "risk": _risk(take_profit_pct=0.30, trailing_stop_pct=0.10),
        "sizing": {"type": "equal_weight"},
        "rationale": "ride medium-term trends via EMA crossover",
    }


def rsi_reversion(universe: list[str], period: int = 14, lo: int = 30, hi: int = 55) -> dict:
    return {
        "name": f"RSI Reversion {period}",
        "universe": universe,
        "timeframe": "1d",
        "indicators": [{"id": "rsi", "type": "RSI", "period": period}],
        "entry": {"all": [{"left": "rsi", "op": "<", "right": lo}]},
        "exit": {"any": [{"left": "rsi", "op": ">", "right": hi}]},
        "risk": _risk(stop_loss_pct=0.07, take_profit_pct=0.15, max_open_positions=2),
        "sizing": {"type": "equal_weight"},
        "rationale": "buy oversold, exit on momentum recovery",
    }


def momentum_roc(universe: list[str], period: int = 20, thresh: int = 8) -> dict:
    return {
        "name": f"Momentum ROC {period}",
        "universe": universe,
        "timeframe": "1d",
        "indicators": [
            {"id": "roc", "type": "ROC", "source": "close", "period": period},
            {"id": "rsi", "type": "RSI", "period": 14},
        ],
        "entry": {"all": [
            {"left": "roc", "op": ">", "right": thresh},
            {"left": "rsi", "op": "<", "right": 75},
        ]},
        "exit": {"any": [{"left": "roc", "op": "<", "right": 0}]},
        "risk": _risk(take_profit_pct=0.25, trailing_stop_pct=0.12),
        "sizing": {"type": "equal_weight"},
        "rationale": "chase positive rate-of-change momentum, avoid overbought entries",
    }


def trend_pullback(universe: list[str]) -> dict:
    return {
        "name": "Trend Pullback",
        "universe": universe,
        "timeframe": "1d",
        "indicators": [
            {"id": "ema_trend", "type": "EMA", "source": "close", "period": 50},
            {"id": "rsi", "type": "RSI", "period": 10},
        ],
        "entry": {"all": [
            {"left": "close", "op": ">", "right": "ema_trend"},
            {"left": "rsi", "op": "<", "right": 40},
        ]},
        "exit": {"any": [
            {"left": "rsi", "op": ">", "right": 65},
            {"left": "close", "op": "cross_below", "right": "ema_trend"},
        ]},
        "risk": _risk(stop_loss_pct=0.06, take_profit_pct=0.18),
        "sizing": {"type": "equal_weight"},
        "rationale": "buy pullbacks within an established uptrend",
    }


def ema_breakout(universe: list[str], period: int = 30) -> dict:
    return {
        "name": f"EMA Breakout {period}",
        "universe": universe,
        "timeframe": "1d",
        "indicators": [{"id": "ema", "type": "EMA", "source": "close", "period": period}],
        "entry": {"all": [{"left": "close", "op": "cross_above", "right": "ema"}]},
        "exit": {"any": [{"left": "close", "op": "cross_below", "right": "ema"}]},
        "risk": _risk(trailing_stop_pct=0.08),
        "sizing": {"type": "equal_weight"},
        "rationale": "trade momentum breakouts above a single EMA",
    }


def macd_sentiment(universe: list[str]) -> dict:
    """The Track-2 archetype: RSI + MACD + CMC Fear & Greed into entry/exit rules."""
    return {
        "name": "MACD + RSI + Fear&Greed",
        "universe": universe,
        "timeframe": "1d",
        "indicators": [
            {"id": "macd", "type": "MACD", "source": "close", "fast": 12, "slow": 26, "signal": 9},
            {"id": "macd_sig", "type": "MACD_SIGNAL", "source": "close", "fast": 12, "slow": 26, "signal": 9},
            {"id": "rsi", "type": "RSI", "period": 14},
        ],
        "entry": {"all": [
            {"left": "macd", "op": "cross_above", "right": "macd_sig"},
            {"left": "rsi", "op": "<", "right": 70},
            {"left": "fgi", "op": ">", "right": 30},
        ]},
        "exit": {"any": [
            {"left": "macd", "op": "cross_below", "right": "macd_sig"},
            {"left": "fgi", "op": ">", "right": 82},
        ]},
        "risk": _risk(stop_loss_pct=0.07, take_profit_pct=0.22, trailing_stop_pct=0.10),
        "sizing": {"type": "equal_weight"},
        "rationale": "enter on MACD momentum confirmed by RSI room and non-fearful sentiment; exit on momentum loss or extreme greed",
    }


def seed_library(universe: list[str]) -> list[dict]:
    return [
        golden_cross(universe),
        golden_cross(universe, 10, 30),
        rsi_reversion(universe),
        rsi_reversion(universe, 7, 25, 50),
        momentum_roc(universe),
        trend_pullback(universe),
        ema_breakout(universe),
        macd_sentiment(universe),
    ]
