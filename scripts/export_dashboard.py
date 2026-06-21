"""Export the locked champion's real results to the dashboard data file.

Reads strategies/sample-champion.json, re-runs its backtest on live data, pulls
the evolution history + on-chain identity + live CMC Fear & Greed, and writes
web/public/data/darwin.json for the Next.js dashboard.

Run: python -m scripts.export_dashboard
"""
from __future__ import annotations

import json
from pathlib import Path

from darwin.config import RUNS_DIR, settings
from darwin.data_source import load_market_data, load_signals
from darwin.strategy.backtest import run_backtest
from darwin.strategy.spec import StrategySpec

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "public" / "data" / "darwin.json"
CHAMPION = ROOT / "strategies" / "sample-champion.json"


def _equity_points(equity, max_points: int = 140):
    pts = [(str(idx.date()), float(v)) for idx, v in equity.items()]
    if len(pts) > max_points:
        step = len(pts) // max_points
        pts = pts[::step]
    return [{"date": d, "value": round(v, 2)} for d, v in pts]


def main() -> None:
    spec = StrategySpec.from_json(CHAMPION.read_text())
    spec.validate()
    fp = spec.fingerprint()

    syn = not settings.has_cmc
    data = load_market_data(spec.universe, count=700, force_synthetic=syn)
    signals = load_signals(count=700, force_synthetic=syn)
    result = run_backtest(spec, data, signals=signals)
    m = result.metrics

    # Evolution history from the champion's run dir, if present.
    history = []
    hist_file = RUNS_DIR / f"run_{fp}" / "history.json"
    if hist_file.exists():
        history = json.loads(hist_file.read_text())

    # On-chain identity proof.
    identity = {}
    id_file = RUNS_DIR / "identity.json"
    if id_file.exists():
        raw = json.loads(id_file.read_text())
        tx = raw.get("transactionHash") or raw.get("tx") or ""
        identity = {
            "agentId": raw.get("agentId"),
            "txHash": tx,
            "registry": "0x8004A818BFB912233c491871b3d84c89A494BD9e",
            "wallet": "0xdfB7b67a623B179a49C7Df70FB5b5B160E7803F4",
            "network": "BSC testnet",
            "gasless": True,
            "explorer": f"https://testnet.bscscan.com/tx/{tx}" if tx else "",
        }

    # Live CMC Fear & Greed (latest + recent series).
    fg = {"value": None, "classification": "", "series": []}
    fgi = signals.get("fgi")
    if fgi is not None and len(fgi):
        last = float(fgi.iloc[-1])
        fg["value"] = round(last)
        fg["classification"] = (
            "Extreme Fear" if last < 25 else "Fear" if last < 45 else
            "Neutral" if last < 55 else "Greed" if last < 75 else "Extreme Greed"
        )
        tail = fgi.tail(90)
        fg["series"] = [{"date": str(i.date()), "value": round(float(v))} for i, v in tail.items()]
    fg["source"] = "synthetic" if syn else "CoinMarketCap"

    payload = {
        "champion": {
            "name": spec.name,
            "fingerprint": fp,
            "rationale": spec.rationale,
            "universe": spec.universe,
            "timeframe": spec.timeframe,
            "indicators": [i.__dict__ for i in spec.indicators],
            "entry": spec.entry,
            "exit": spec.exit,
            "risk": spec.risk.__dict__,
            "sizing": spec.sizing.__dict__,
        },
        "metrics": {
            "totalReturn": round(m.total_return, 4),
            "cagr": round(m.cagr, 4),
            "sharpe": round(m.sharpe, 2),
            "sortino": round(m.sortino, 2),
            "maxDrawdown": round(m.max_drawdown, 4),
            "calmar": round(m.calmar, 2),
            "winRate": round(m.win_rate, 3),
            "numTrades": m.num_trades,
            "exposure": round(m.exposure, 3),
            "ruleAdherence": round(m.rule_adherence, 3),
            "finalEquity": round(m.final_equity, 2),
        },
        "equity": _equity_points(result.equity),
        "history": history,
        "fearGreed": fg,
        "identity": identity,
        "meta": {
            "dataSource": "synthetic" if syn else "CoinMarketCap OHLCV (live)",
            "universe": spec.universe,
            "bars": len(result.equity),
            "generations": len(history),
            "sponsors": {
                "cmc": "live OHLCV + Fear & Greed",
                "bnb": "ERC-8004 identity (gasless)",
                "twak": "HMAC auth + BSC asset resolution",
            },
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"wrote {OUT}")
    print(f"  champion: {spec.name}")
    print(f"  metrics : ret={m.total_return:+.1%} sharpe={m.sharpe:.2f} maxDD={m.max_drawdown:.1%} trades={m.num_trades}")
    print(f"  equity pts: {len(payload['equity'])} | history gens: {len(history)} | F&G: {fg['value']} ({fg['classification']})")
    print(f"  identity: agentId={identity.get('agentId')} tx={identity.get('txHash','')[:18]}...")


if __name__ == "__main__":
    main()
