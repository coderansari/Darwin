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
from datetime import datetime, timezone

import requests

from ..config import settings
from .twak import SwapResult

BASE_URL = "https://tws.trustwallet.com"

# Common BSC mainnet token addresses (fallback when asset search is unavailable).
BSC_TOKENS = {
    "USDT": "0x55d398326f99059fF775485246999027B3197955",
    "WBNB": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
    "BNB": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",   # swap via WBNB
    "BTC": "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c",   # BTCB
    "BTCB": "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c",
    "ETH": "0x2170Ed0880ac9A755fd29B2688956BD959F933F8",
    "CAKE": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
}
CHAIN_KEY = "bsc"


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

    # ---- signing -----------------------------------------------------------

    def _headers(self, method: str, path: str, query: str, variant: str) -> dict:
        nonce = uuid.uuid4().hex
        date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if variant == "v2":
            sorted_q = "&".join(sorted(query.split("&"))) if query else ""
            msg = f"{method};{path};{sorted_q};{self.access_id};{nonce};{date}"
        else:  # v1
            msg = f"{method}{path}{query}{self.access_id}{nonce}{date}"
        sig = base64.b64encode(
            hmac.new(self.secret.encode(), msg.encode(), hashlib.sha256).digest()
        ).decode()
        auth = f"HMAC-SHA256 Signature={sig}" if variant == "v2" else sig
        return {
            "X-TW-Credential": self.access_id,
            "X-TW-Nonce": nonce,
            "X-TW-Date": date,
            "Authorization": auth,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, query: str = "", body: dict | None = None,
                 variant: str | None = None) -> requests.Response:
        variant = variant or self.variant or "v2"
        url = f"{BASE_URL}{path}" + (f"?{query}" if query else "")
        headers = self._headers(method, path, query, variant)
        data = json.dumps(body) if body is not None else None
        return requests.request(method, url, headers=headers, data=data, timeout=30)

    def selftest(self) -> str | None:
        """Probe both signing variants against the confirmed search endpoint.
        Returns the working variant ('v1'/'v2') or None."""
        path, query = "/v1/search/assets", "query=bnb&limit=1"
        for variant in ("v2", "v1"):
            try:
                r = self._request("GET", path, query, variant=variant)
                if r.status_code == 200:
                    self.variant = variant
                    return variant
            except requests.RequestException:
                continue
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


def _to_wei(amount: float, decimals: int = 18) -> str:
    return str(int(amount * (10 ** decimals)))


def gateway_swap(plan: dict, live: bool) -> SwapResult:
    """Fetch a real TWAK swap route for a planned swap on BSC mainnet.

    Read-only quote + executable-tx build. Does NOT broadcast (mainnet funds);
    broadcasting is a deliberate manual/guarded step.
    """
    try:
        gw = TwakGateway()
    except RuntimeError as e:
        return SwapResult(False, str(e))

    if gw.selftest() is None:
        return SwapResult(False, "gateway auth self-test failed (check portal creds / signing variant)")

    from_addr = _agent_address()
    from_asset = BSC_TOKENS.get(plan["from"].upper())
    to_asset = BSC_TOKENS.get(plan["to"].upper())
    if not from_asset or not to_asset:
        return SwapResult(False, f"no BSC mainnet address for {plan['from']}->{plan['to']} "
                                 f"(supported: {sorted(BSC_TOKENS)})")

    try:
        route = gw.swap_route(from_asset, to_asset, _to_wei(plan["amount"]), from_addr)
    except requests.RequestException as e:
        return SwapResult(False, f"route request failed: {e}")

    routes = route.get("routes", [])
    if not routes:
        return SwapResult(False, "no swap route returned")
    best = routes[0]
    steps = best.get("steps", [{}])
    provider = steps[0].get("provider", {}).get("name", "?")
    out_amt = steps[0].get("to", {}).get("amount", "?")
    detail = f"route via {provider}: {plan['amount']} {plan['from']} -> {out_amt} {plan['to']} (signed via TWAK)"

    if live:
        step_id = steps[0].get("id")
        if step_id:
            try:
                tx = gw.route_step(step_id)
                evm = tx.get("transaction", {}).get("evmTx", {})
                detail += f" | built tx to={evm.get('to')} (NOT broadcast - mainnet safety)"
            except requests.RequestException as e:
                detail += f" | step-tx build failed: {e}"
    return SwapResult(True, detail)
