"""Thin CoinMarketCap Pro API client.

Endpoints used (verified against CMC Pro docs):
  * /v2/cryptocurrency/ohlcv/historical  -> backtest candles (paid tier)
  * /v2/cryptocurrency/quotes/latest      -> live price (all tiers)
  * /v3/fear-and-greed/latest|historical  -> CMC's proprietary sentiment signal
                                             (ALL tiers, incl. free)
  * /v1/cryptocurrency/trending/gainers-losers -> momentum signal (Startup+)

Responses are cached to data/cache/ so repeated backtests don't re-bill credits.
Auth header for REST is X-CMC_PRO_API_KEY (underscores). Note the MCP server uses
a DIFFERENT header, X-CMC-MCP-API-KEY (hyphens) — not used here.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import pandas as pd
import requests

from ..config import DATA_DIR, settings

BASE_URL = "https://pro-api.coinmarketcap.com"


class CMCError(RuntimeError):
    pass


class CMCClient:
    def __init__(self, api_key: str | None = None, cache_dir: Path = DATA_DIR):
        self.api_key = api_key or settings.cmc_api_key
        if not self.api_key:
            raise CMCError("no CMC_PRO_API_KEY configured")
        self.cache_dir = cache_dir
        self.session = requests.Session()
        self.session.headers.update(
            {"X-CMC_PRO_API_KEY": self.api_key, "Accept": "application/json"}
        )

    # ---- low-level ---------------------------------------------------------

    def _get(self, path: str, params: dict, cache_ttl: float | None = None) -> dict:
        key = hashlib.sha256(f"{path}?{json.dumps(params, sort_keys=True)}".encode()).hexdigest()[:16]
        cache_file = self.cache_dir / f"cmc_{key}.json"
        if cache_file.exists():
            if cache_ttl is None or (time.time() - cache_file.stat().st_mtime) < cache_ttl:
                return json.loads(cache_file.read_text())

        resp = self.session.get(f"{BASE_URL}{path}", params=params, timeout=30)
        try:
            payload = resp.json()
        except ValueError:
            raise CMCError(f"non-JSON response ({resp.status_code}) from {path}")
        status = payload.get("status", {})
        if status.get("error_code"):
            raise CMCError(f"CMC error {status['error_code']}: {status.get('error_message')}")
        if resp.status_code != 200:
            raise CMCError(f"HTTP {resp.status_code} from {path}")
        cache_file.write_text(json.dumps(payload))
        return payload

    # ---- historical OHLCV --------------------------------------------------

    def ohlcv_historical(
        self,
        symbol: str,
        count: int = 365,
        time_period: str = "daily",
        interval: str = "daily",
        convert: str = "USD",
    ) -> pd.DataFrame:
        """Return OHLCV DataFrame indexed by candle close time (UTC)."""
        payload = self._get(
            "/v2/cryptocurrency/ohlcv/historical",
            {
                "symbol": symbol,
                "count": count,
                "time_period": time_period,
                "interval": interval,
                "convert": convert,
            },
        )
        data = payload["data"]
        # v2 keyed-by-symbol may return a list; normalize to the first match.
        if isinstance(data, dict) and symbol in data:
            data = data[symbol]
        if isinstance(data, list):
            data = data[0]
        rows = []
        for q in data.get("quotes", []):
            cell = q["quote"][convert]
            rows.append(
                {
                    "time": pd.to_datetime(q.get("time_close") or cell.get("timestamp")),
                    "open": cell["open"],
                    "high": cell["high"],
                    "low": cell["low"],
                    "close": cell["close"],
                    "volume": cell.get("volume", 0.0) or 0.0,
                }
            )
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        return df.set_index("time").sort_index()

    # ---- live quotes -------------------------------------------------------

    def quotes_latest(self, symbols: list[str], convert: str = "USD") -> dict:
        payload = self._get(
            "/v2/cryptocurrency/quotes/latest",
            {"symbol": ",".join(symbols), "convert": convert},
            cache_ttl=60,
        )
        out = {}
        for sym, entries in payload["data"].items():
            entry = entries[0] if isinstance(entries, list) else entries
            out[sym] = entry["quote"][convert]
        return out

    # ---- CMC proprietary sentiment signal ----------------------------------

    def fear_greed_latest(self) -> dict:
        payload = self._get("/v3/fear-and-greed/latest", {}, cache_ttl=600)
        return payload["data"]

    def fear_greed_historical(self, limit: int = 500) -> pd.DataFrame:
        payload = self._get("/v3/fear-and-greed/historical", {"limit": limit}, cache_ttl=3600)
        rows = payload.get("data", [])
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        ts_col = "timestamp" if "timestamp" in df.columns else "update_time"
        df["time"] = pd.to_datetime(df[ts_col], unit="s", errors="coerce")
        if df["time"].isna().all():
            df["time"] = pd.to_datetime(df[ts_col], errors="coerce")
        return df.set_index("time").sort_index()

    def gainers_losers(self, time_period: str = "24h", limit: int = 20, convert: str = "USD") -> list[dict]:
        payload = self._get(
            "/v1/cryptocurrency/trending/gainers-losers",
            {"time_period": time_period, "limit": limit, "convert": convert},
            cache_ttl=600,
        )
        return payload.get("data", [])
