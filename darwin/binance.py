"""Real historical OHLCV from Binance public klines (free, no API key).

CoinMarketCap's OHLCV endpoint requires a paid tier, so Binance provides the
price candles for backtesting while CMC provides its proprietary Fear & Greed
signal + live quotes. Symbols are mapped to USDT spot pairs (BTC -> BTCUSDT).
"""
from __future__ import annotations

import pandas as pd
import requests

BINANCE_BASE = "https://api.binance.com"
_INTERVAL = {"1d": "1d", "4h": "4h", "1h": "1h", "1w": "1w"}
# Symbols whose Binance pair isn't simply <SYMBOL>USDT.
_PAIR_OVERRIDE: dict[str, str] = {}


def _pair(symbol: str) -> str:
    return _PAIR_OVERRIDE.get(symbol.upper(), f"{symbol.upper()}USDT")


def binance_klines(symbol: str, count: int = 500, timeframe: str = "1d") -> pd.DataFrame:
    """Return an OHLCV DataFrame (open/high/low/close/volume) indexed by bar open time."""
    interval = _INTERVAL.get(timeframe, "1d")
    resp = requests.get(
        f"{BINANCE_BASE}/api/v3/klines",
        params={"symbol": _pair(symbol), "interval": interval, "limit": min(count, 1000)},
        timeout=30,
    )
    resp.raise_for_status()
    rows = resp.json()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(
        rows,
        columns=["openTime", "open", "high", "low", "close", "volume",
                 "closeTime", "qv", "trades", "tbv", "tqv", "ignore"],
    )
    df["time"] = pd.to_datetime(df["openTime"], unit="ms")
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype(float)
    return df.set_index("time")[["open", "high", "low", "close", "volume"]].sort_index()
