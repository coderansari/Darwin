"""Bridge an evolved StrategySpec to live execution on BSC via Trust Wallet Agent Kit.

Pipeline:
  1. Evaluate the champion strategy's CURRENT signal on live market data
     (the same deterministic rule engine used in the backtest — so what we
     execute is exactly what we backtested).
  2. Turn active long signals into rule-gated swap plans (allowlist = the spec's
     universe; sizing = risk.max_position_pct; cap = risk.max_open_positions).
  3. Execute each swap on PancakeSwap (BSC) through TWAK, or dry-run the plan.

Backends (auto-selected):
  * "cli"     — shells out to the `twak` CLI (requires Node >= 22.14).
  * "gateway" — Trust Wallet portal API gateway over HTTPS (HMAC auth).
  * "dryrun"  — prints the exact intended action; always available.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

import pandas as pd

from ..config import settings
from ..data_source import load_market_data, load_signals
from ..strategy.backtest import eval_condition
from ..strategy.indicators import compute_all
from ..strategy.spec import SIGNAL_SOURCES, StrategySpec

QUOTE_TOKEN = "USDT"  # what we swap *from* when entering a position on BSC


# ---------------------------------------------------------------------------
# Live signal evaluation
# ---------------------------------------------------------------------------


def _frame_for(spec: StrategySpec, symbol: str, df: pd.DataFrame, fgi: pd.Series | None) -> pd.DataFrame:
    frame = df.copy()
    ind = compute_all(spec.indicators, df)
    for col in ind.columns:
        frame[col] = ind[col]
    if fgi is not None and any(
        ref in SIGNAL_SOURCES
        for cond in (spec.entry, spec.exit)
        for ref in _refs(cond)
    ):
        frame["fgi"] = fgi.reindex(df.index).ffill()
    return frame


def _refs(node: dict):
    if "all" in node or "any" in node:
        key = "all" if "all" in node else "any"
        for child in node[key]:
            yield from _refs(child)
    elif "op" in node:
        for side in ("left", "right"):
            yield node[side]


def current_signals(spec: StrategySpec, bars: int = 120) -> list[dict]:
    """Return the strategy's current per-symbol state on live (or synthetic) data."""
    force_syn = not settings.has_cmc
    data = load_market_data(spec.universe, count=bars, timeframe=spec.timeframe, force_synthetic=force_syn)
    fgi = load_signals(count=bars, timeframe=spec.timeframe, force_synthetic=force_syn).get("fgi")

    out = []
    for sym, df in data.items():
        if df.empty:
            continue
        frame = _frame_for(spec, sym, df, fgi)
        entry = bool(eval_condition(spec.entry, frame).iloc[-1])
        exit_ = bool(eval_condition(spec.exit, frame).iloc[-1])
        out.append({
            "symbol": sym,
            "price": float(df["close"].iloc[-1]),
            "entry_active": entry,
            "exit_active": exit_,
            "long": entry and not exit_,
        })
    return out


def plan_swaps(spec: StrategySpec, amount: float) -> list[dict]:
    """Rule-gated allocation: which swaps the agent would place right now."""
    signals = current_signals(spec)
    longs = [s for s in signals if s["long"]]
    longs = longs[: spec.risk.max_open_positions]            # cap concurrent positions
    if not longs:
        return []
    per = min(amount / len(longs), amount * spec.risk.max_position_pct * spec.risk.max_open_positions)
    return [
        {
            "from": QUOTE_TOKEN,
            "to": s["symbol"],
            "amount": round(per, 4),
            "price": s["price"],
            "reason": "entry signal active",
        }
        for s in longs
    ]


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------


@dataclass
class SwapResult:
    ok: bool
    detail: str


def _twak_bin() -> str | None:
    for cand in ("twak", "twak.cmd"):
        path = shutil.which(cand)
        if path:
            return path
    return None


def _cli_healthy() -> bool:
    """The npm `twak` CLI needs Node >= 22.14; older Node throws ERR_REQUIRE_ESM.
    Verify it actually runs before selecting it as a backend."""
    binary = _twak_bin()
    if not binary:
        return False
    try:
        proc = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=30)
        return proc.returncode == 0
    except Exception:
        return False


def select_backend() -> str:
    if settings.twak_access_id and settings.twak_hmac_secret:
        return "gateway"
    if _cli_healthy():
        return "cli"
    return "dryrun"


def _cli_swap(plan: dict, live: bool) -> SwapResult:
    binary = _twak_bin()
    args = [binary, "swap", str(plan["amount"]), plan["from"], plan["to"], "--network", "bsc"]
    if not live:
        args.append("--quote-only")
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=120)
        ok = proc.returncode == 0
        return SwapResult(ok, (proc.stdout or proc.stderr).strip()[:400])
    except Exception as e:
        return SwapResult(False, f"twak CLI error: {e}")


def _gateway_swap(plan: dict, live: bool) -> SwapResult:
    # Filled in once the exact portal gateway HMAC spec is confirmed.
    from .twak_gateway import gateway_swap  # lazy
    return gateway_swap(plan, live)


def execute_spec(spec: StrategySpec, live: bool = False, amount: float = 10.0) -> int:
    spec.validate()
    backend = select_backend()
    print(f"Darwin execute - strategy: {spec.name} [{spec.fingerprint()}]")
    print(f"  universe (allowlist): {spec.universe}")
    print(f"  backend: {backend}  |  mode: {'LIVE' if live else 'dry-run'}")

    plans = plan_swaps(spec, amount)
    if not plans:
        print("  no entry signals active right now - agent holds (nothing to execute).")
        return 0

    print(f"  {len(plans)} rule-gated swap(s) planned:")
    rc = 0
    for p in plans:
        line = f"    {p['from']} -> {p['to']}  ~{p['amount']} {p['from']}  (px {p['price']:.4g}, {p['reason']})"
        print(line)
        if backend == "dryrun":
            print("      [dry-run] would route via PancakeSwap on BSC through TWAK")
            continue
        result = _cli_swap(p, live) if backend == "cli" else _gateway_swap(p, live)
        print(f"      {'OK' if result.ok else 'FAIL'}: {result.detail}")
        rc = rc or (0 if result.ok else 1)
    return rc
