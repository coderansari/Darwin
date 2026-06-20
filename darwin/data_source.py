"""Market data loader.

Uses the real CoinMarketCap API when a key is configured; otherwise falls back
to a deterministic synthetic generator so the engine is always testable without
spending API credits. Synthetic data is seeded per-symbol => reproducible.
"""
from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from .cmc.client import CMCClient, CMCError
from .config import settings

_TIMEFRAME_TO_CMC = {
    "1d": ("daily", "daily"),
    "1h": ("hourly", "hourly"),
    "1w": ("daily", "weekly"),
}


def _seed_for(symbol: str) -> int:
    return int(hashlib.sha256(symbol.encode()).hexdigest(), 16) % (2**32)


def synthetic_ohlcv(symbol: str, n: int = 365, timeframe: str = "1d") -> pd.DataFrame:
    """Deterministic geometric-random-walk candles with per-symbol regime shifts."""
    rng = np.random.default_rng(_seed_for(symbol))
    drift = rng.uniform(-0.0003, 0.0009)          # daily drift
    vol = rng.uniform(0.02, 0.06)                  # daily vol
    price = rng.uniform(0.5, 500.0)

    closes = np.empty(n)
    # Inject a couple of regime changes so trend/mean-reversion edges can exist.
    regime = rng.uniform(-1, 1, size=3)
    for i in range(n):
        seg = min(i // max(1, n // 3), 2)
        step = drift * (1 + regime[seg]) + vol * rng.standard_normal()
        price *= float(np.exp(step))
        closes[i] = price

    freq = {"1d": "D", "1h": "h", "1w": "W"}.get(timeframe, "D")
    idx = pd.date_range(end=pd.Timestamp.utcnow().normalize(), periods=n, freq=freq)

    opens = np.empty(n)
    opens[0] = closes[0] * (1 - vol * 0.5)
    opens[1:] = closes[:-1]
    intrabar = np.abs(rng.standard_normal(n)) * vol * 0.5
    highs = np.maximum(opens, closes) * (1 + intrabar)
    lows = np.minimum(opens, closes) * (1 - intrabar)
    volume = rng.uniform(1e6, 1e8, size=n)

    return pd.DataFrame(
        {"open": opens, "high": highs, "low": lows, "close": closes, "volume": volume},
        index=idx,
    )


def load_market_data(
    symbols: list[str],
    count: int = 365,
    timeframe: str = "1d",
    force_synthetic: bool = False,
) -> dict[str, pd.DataFrame]:
    """Return {symbol -> OHLCV DataFrame}. Source preference:
    CoinMarketCap OHLCV (paid tier) -> Binance public klines -> deterministic synthetic.
    """
    if force_synthetic:
        return {s: synthetic_ohlcv(s, count, timeframe) for s in symbols}

    from .binance import binance_klines

    cmc = None
    if settings.has_cmc:
        try:
            cmc = CMCClient()
        except CMCError:
            cmc = None
    time_period, interval = _TIMEFRAME_TO_CMC.get(timeframe, ("daily", "daily"))

    out: dict[str, pd.DataFrame] = {}
    for s in symbols:
        df = None
        if cmc is not None:
            try:
                got = cmc.ohlcv_historical(s, count=count, time_period=time_period, interval=interval)
                df = got if not got.empty else None
            except CMCError:
                df = None
        if df is None:
            try:
                got = binance_klines(s, count=count, timeframe=timeframe)
                df = got if not got.empty else None
            except Exception:
                df = None
        out[s] = df if df is not None else synthetic_ohlcv(s, count, timeframe)
    return out


def load_fear_greed() -> pd.DataFrame | None:
    """CMC's proprietary 0-100 sentiment index as a time series, or None."""
    if not settings.has_cmc:
        return None
    try:
        return CMCClient().fear_greed_historical(limit=1000)
    except CMCError:
        return None


def synthetic_fgi(n: int = 500, timeframe: str = "1d") -> pd.Series:
    """Deterministic mean-reverting Fear & Greed proxy (0-100) for offline demos."""
    rng = np.random.default_rng(99)
    vals = np.empty(n)
    x = 50.0
    for i in range(n):
        x = float(np.clip(x + rng.normal(0, 7) + (50.0 - x) * 0.05, 5, 95))
        vals[i] = x
    freq = {"1d": "D", "1h": "h", "1w": "W"}.get(timeframe, "D")
    idx = pd.date_range(end=pd.Timestamp.utcnow().normalize(), periods=n, freq=freq)
    return pd.Series(vals, index=idx, name="fgi")


def load_signals(count: int = 500, timeframe: str = "1d", force_synthetic: bool = False) -> dict[str, pd.Series]:
    """Market-wide signals usable by strategy conditions. Always returns an `fgi`
    series (real CMC Fear & Greed when available, synthetic otherwise)."""
    if force_synthetic or not settings.has_cmc:
        return {"fgi": synthetic_fgi(count, timeframe)}
    fg = load_fear_greed()
    if fg is not None and "value" in fg.columns and not fg.empty:
        return {"fgi": fg["value"].astype(float)}
    return {"fgi": synthetic_fgi(count, timeframe)}
