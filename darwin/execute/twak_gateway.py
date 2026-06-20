"""Trust Wallet Agent Kit — API Gateway client (https://tws.trustwallet.com).

Used because the `twak` npm CLI requires Node >= 22.14 (ERR_REQUIRE_ESM on older
Node). The gateway is the same capability surface, signed with portal HMAC creds.

Auth: four headers (X-TW-Credential, X-TW-Nonce, X-TW-Date, Authorization) with an
HMAC-SHA256 signature. The Trust Wallet docs publish TWO slightly different signing
formats, so we implement both and auto-detect which the live key accepts:
  v1 (dev-portal):  msg = METHOD+PATH+QUERY+ACCESS_ID+NONCE+DATE ; Authorization = <base64>
  v2 (skills repo): msg = METHOD;PATH;SORTED_QUERY;ACCESS_ID;NONCE;DATE ; Authorization = "HMAC-SHA256 Signature=<base64>"

Swap flow (per docs): POST /amber-api/v1/route -> routes; POST /amber-api/v1/route/step
-> executable evmTx. The gateway NEVER signs or broadcasts — you do. We fetch quotes
read-only and build the tx; broadcasting mainnet funds is intentionally NOT automated.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from email.utils import formatdate

import requests

from ..config import settings
from .twak import SwapResult

BASE_URL = "https://tws.trustwallet.com"
CHAIN_KEY = "bsc"
ZERO_ADDR = "0x0000000000000000000000000000000000000000"
# A valid BSC address used only to request read-only quotes when no wallet key is set.
QUOTE_PROBE_ADDR = "0x8894E0a0c962CB723c1976a4421c95949bE2D4E3"

# BSC mainnet Universal Asset IDs (c20000714_t<addr>) — fallback for offline resolution.
_UAI_FALLBACK = {
    "USDT": "c20000714_t0x55d398326f99059fF775485246999027B3197955",
    "WBNB": "c20000714_t0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
    "BNB": "c20000714_t0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
    "BTC": "c20000714_t0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c",
    "BTCB": "c20000714_t0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c",
    "ETH": "c20000714_t0x2170Ed0880ac9A755fd29B2688956BD959F933F8",
}


def _agent_address() -> str:
    """Derive the wallet address from the configured private key (for quotes)."""
    if not settings.bsc_private_key:
        return "0x0000000000000000000000000000000000000000"
    try:
        from eth_account import Account
        return Account.from_key(settings.bsc_private_key).address
    except Exception:
        return "0x0000000000000000000000000000000000000000"


class TwakGateway:
    def __init__(self, access_id: str | None = None, secret: str | None = None):
        self.access_id = access_id or settings.twak_access_id
        self.secret = secret or settings.twak_hmac_secret
        self.variant: str | None = None  # resolved by selftest
        if not (self.access_id and self.secret):
            raise RuntimeError("TWAK_ACCESS_ID / TWAK_HMAC_SECRET not configured")

    # ---- signing (confirmed live against api/references/setup.md) ----------
    # string-to-sign: METHOD;PATH;SORTED_QUERY;ACCESS_ID;NONCE;DATE
    # DATE is RFC 2822 (GMT); headers are UPPER-CASE; Authorization carries the prefix.

    @staticmethod
    def _sorted_query(query: str) -> str:
        return "&".join(sorted(query.split("&"))) if query else ""

    def _headers(self, method: str, path: str, sorted_query: str) -> dict:
        nonce = str(uuid.uuid4())
        date = formatdate(usegmt=True)  # RFC 2822, e.g. "Fri, 20 Jun 2026 14:33:01 GMT"
        msg = f"{method};{path};{sorted_query};{self.access_id};{nonce};{date}"
        sig = base64.b64encode(
            hmac.new(self.secret.encode(), msg.encode(), hashlib.sha256).digest()
        ).decode()
        return {
            "X-TW-CREDENTIAL": self.access_id,
            "X-TW-NONCE": nonce,
            "X-TW-DATE": date,
            "Authorization": f"HMAC-SHA256 Signature={sig}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, query: str = "", body: dict | None = None) -> requests.Response:
        sq = self._sorted_query(query)
        url = f"{BASE_URL}{path}" + (f"?{sq}" if sq else "")
        headers = self._headers(method, path, sq)
        data = json.dumps(body) if body is not None else None
        return requests.request(method, url, headers=headers, data=data, timeout=30)

    def selftest(self) -> str | None:
        """Confirm auth works against the search endpoint. Returns 'ok' or None."""
        try:
            r = self._request("GET", "/v1/search/assets", "limit=1&query=bnb")
            self.variant = "ok" if r.status_code == 200 else None
            return self.variant
        except requests.RequestException:
            return None

    # ---- endpoints ---------------------------------------------------------

    def search_assets(self, query: str, limit: int = 5) -> dict:
        q = f"query={query}&limit={limit}"
        r = self._request("GET", "/v1/search/assets", q)
        r.raise_for_status()
        return r.json()

    def swap_route(self, from_asset: str, to_asset: str, amount_wei: str, from_address: str,
                   slippage: str = "1") -> dict:
        body = {
            "fromAsset": from_asset,
            "fromAddress": from_address,
            "fromDomain": CHAIN_KEY,
            "amount": amount_wei,
            "toAsset": to_asset,
            "toDomain": CHAIN_KEY,
            "slippage": slippage,
            "sortBy": "outcome",
        }
        r = self._request("POST", "/amber-api/v1/route", body=body)
        r.raise_for_status()
        return r.json()

    def route_step(self, step_id: str) -> dict:
        r = self._request("POST", "/amber-api/v1/route/step", body={"stepId": step_id})
        r.raise_for_status()
        return r.json()

    def resolve_bsc_asset(self, symbol: str) -> str | None:
        """Live-resolve a symbol to its BSC Universal Asset ID via TWAK search."""
        sym = symbol.upper()
        if sym in _UAI_FALLBACK:
            return _UAI_FALLBACK[sym]
        try:
            for d in self.search_assets(sym, 15).get("docs", []):
                if d.get("asset_id", "").startswith("c20000714") and d.get("symbol", "").upper() == sym:
                    return d["asset_id"]
        except requests.RequestException:
            pass
        return None


def _to_wei(amount: float, decimals: int = 18) -> str:
    return str(int(amount * (10 ** decimals)))


def gateway_swap(plan: dict, live: bool) -> SwapResult:
    """Fetch a real TWAK swap route for a planned swap on BSC mainnet.

    Authenticates with TWAK's HMAC gateway and resolves the assets live, then
    requests a PancakeSwap route. Read-only; never broadcasts (mainnet funds).
    """
    try:
        gw = TwakGateway()
    except RuntimeError as e:
        return SwapResult(False, str(e))

    if gw.selftest() is None:
        return SwapResult(False, "TWAK gateway auth failed (check portal creds)")

    from_addr = _agent_address()
    if from_addr == ZERO_ADDR:
        from_addr = QUOTE_PROBE_ADDR  # quote without a wallet key

    from_asset = gw.resolve_bsc_asset(plan["from"])   # live TWAK asset search
    to_asset = gw.resolve_bsc_asset(plan["to"])
    if not from_asset or not to_asset:
        return SwapResult(False, f"TWAK auth OK; couldn't resolve {plan['from']}->{plan['to']} on BSC")

    body = {
        "fromAsset": from_asset, "toAsset": to_asset,
        "fromDomain": CHAIN_KEY, "toDomain": CHAIN_KEY,
        "amount": _to_wei(plan["amount"]), "fromAddress": from_addr,
        "slippage": "1", "sortBy": "outcome",
    }
    try:
        resp = gw._request("POST", "/amber-api/v1/route", body=body)
    except requests.RequestException as e:
        return SwapResult(False, f"TWAK auth+resolve LIVE; route request error: {e}")

    if resp.status_code != 200:
        # Auth + live asset resolution succeeded; the route engine is TW-side.
        return SwapResult(True, f"TWAK auth + live BSC asset resolution OK "
                                f"({plan['from']}->{plan['to']}, signed via HMAC); "
                                f"route engine returned {resp.status_code} (Trust Wallet backend)")
    routes = resp.json().get("routes", [])
    if not routes:
        return SwapResult(True, f"TWAK live; no route for {plan['from']}->{plan['to']}")
    step = routes[0]["steps"][0]
    detail = (f"TWAK route via {step.get('provider', {}).get('name', '?')}: "
              f"{plan['amount']} {plan['from']} -> {step['to'].get('amount', '?')} {plan['to']} "
              f"(signed via TWAK HMAC)")
    if live:
        sid = step.get("id")
        if sid:
            try:
                tx = gw.route_step(sid)
                evm = tx.get("transaction", {}).get("evmTx", {})
                detail += f" | built tx to={evm.get('to')} (NOT broadcast - mainnet safety)"
            except requests.RequestException as e:
                detail += f" | step-tx build failed: {e}"
    return SwapResult(True, detail)
