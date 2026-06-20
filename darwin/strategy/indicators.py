"""Deterministic technical indicators. Pure functions over pandas Series.

Everything here must be lookahead-free: indicator value at bar *i* uses only
data up to and including bar *i*. The backtester then acts on bar *i+1*.
"""
from __future__ import annotations

import pandas as pd

from .spec import Indicator


def sma(s: pd.Series, period: int) -> pd.Series:
    return s.rolling(window=period, min_periods=period).mean()


def ema(s: pd.Series, period: int) -> pd.Series:
    return s.ewm(span=period, adjust=False, min_periods=period).mean()


def rsi(s: pd.Series, period: int = 14) -> pd.Series:
    delta = s.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0.0, pd.NA)
    out = 100.0 - (100.0 / (1.0 + rs))
    # when avg_loss == 0 and avg_gain > 0 -> RSI 100; when both 0 -> neutral 50
    out = out.where(avg_loss != 0, other=100.0)
    out = out.where(~((avg_loss == 0) & (avg_gain == 0)), other=50.0)
    return out


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def roc(s: pd.Series, period: int = 10) -> pd.Series:
    return (s / s.shift(period) - 1.0) * 100.0


def macd(s: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Return (macd_line, signal_line, histogram)."""
    line = ema(s, fast) - ema(s, slow)
    sig = line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    return line, sig, line - sig


def compute_indicator(ind: Indicator, df: pd.DataFrame) -> pd.Series:
    """Compute one indicator over an OHLCV DataFrame (columns: open/high/low/close/volume)."""
    src = df[ind.source]
    if ind.type == "PRICE":
        return src
    if ind.type == "SMA":
        return sma(src, ind.period)
    if ind.type == "EMA":
        return ema(src, ind.period)
    if ind.type == "RSI":
        return rsi(src, ind.period)
    if ind.type == "ROC":
        return roc(src, ind.period)
    if ind.type == "ATR":
        return atr(df["high"], df["low"], df["close"], ind.period)
    if ind.type in ("MACD", "MACD_SIGNAL", "MACD_HIST"):
        line, sig, hist = macd(src, ind.fast, ind.slow, ind.signal)
        return {"MACD": line, "MACD_SIGNAL": sig, "MACD_HIST": hist}[ind.type]
    raise ValueError(f"unsupported indicator type: {ind.type}")


def compute_all(indicators: list[Indicator], df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame of all indicator series, indexed like df, columns = indicator ids."""
    out = pd.DataFrame(index=df.index)
    for ind in indicators:
        out[ind.id] = compute_indicator(ind, df)
    return out
