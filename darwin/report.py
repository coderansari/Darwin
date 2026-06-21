"""Render evolution results into human + judge friendly artifacts.

Writes a run directory containing:
  champion.json      — the winning StrategySpec
  report.md          — readable summary with metrics, equity sparkline, lineage
  leaderboard.json   — hall of fame with metrics
  equity.csv         — champion equity curve
  history.json       — per-generation fitness progression
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import RUNS_DIR
from .evolve.engine import EvolutionResult
from .strategy.backtest import BacktestResult

_BLOCKS = "▁▂▃▄▅▆▇█"


def sparkline(series: pd.Series, width: int = 60) -> str:
    if series.empty:
        return ""
    s = series.to_numpy(dtype=float)
    if len(s) > width:
        idx = (pd.Series(range(len(s))).iloc[:: max(1, len(s) // width)]).to_list()
        s = s[idx]
    lo, hi = float(s.min()), float(s.max())
    if hi - lo < 1e-9:
        return _BLOCKS[0] * len(s)
    return "".join(_BLOCKS[min(len(_BLOCKS) - 1, int((v - lo) / (hi - lo) * (len(_BLOCKS) - 1)))] for v in s)


def _metrics_table(r: BacktestResult) -> str:
    m = r.metrics
    rows = [
        ("Total return", f"{m.total_return:+.1%}"),
        ("CAGR", f"{m.cagr:+.1%}"),
        ("Sharpe", f"{m.sharpe:.2f}"),
        ("Sortino", f"{m.sortino:.2f}"),
        ("Max drawdown", f"{m.max_drawdown:.1%}"),
        ("Calmar", f"{m.calmar:.2f}"),
        ("Win rate", f"{m.win_rate:.0%}"),
        ("Trades", f"{m.num_trades}"),
        ("Exposure", f"{m.exposure:.0%}"),
        ("Rule adherence", f"{m.rule_adherence:.0%}"),
        ("Fitness", f"{r.fitness:.3f}"),
    ]
    out = ["| Metric | Value |", "| --- | --- |"]
    out += [f"| {k} | {v} |" for k, v in rows]
    return "\n".join(out)


def _oos_table(oos) -> str:
    """In-sample (train) vs out-of-sample (validation / held-out TEST) comparison."""
    rows = [("train (in-sample)", oos.train), ("validation", oos.validation), ("TEST (held-out)", oos.test)]
    out = [
        "| Window | Return | Sharpe | Sortino | Max DD | Trades | Adherence |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for label, r in rows:
        m = r.metrics
        out.append(
            f"| {label} | {m.total_return:+.1%} | {m.sharpe:.2f} | {m.sortino:.2f} | "
            f"{m.max_drawdown:.1%} | {m.num_trades} | {m.rule_adherence:.0%} |"
        )
    return "\n".join(out)


def render(result: EvolutionResult, meta: dict | None = None, run_dir: Path | None = None, oos=None) -> Path:
    meta = meta or {}
    # When an OOS report is supplied, the champion is the validation-selected spec
    # scored over the full continuous series.
    champ = oos.full if (oos is not None and oos.full is not None) else result.champion
    run_dir = run_dir or (RUNS_DIR / f"run_{champ.spec.fingerprint()}")
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "champion.json").write_text(champ.spec.to_json())
    champ.equity.to_csv(run_dir / "equity.csv", header=True)
    (run_dir / "history.json").write_text(json.dumps(result.history, indent=2))
    if oos is not None:
        (run_dir / "oos.json").write_text(
            json.dumps(
                {
                    "split_dates": [str(d.date()) for d in oos.split_dates],
                    "train": oos.train.metrics.as_dict(),
                    "validation": oos.validation.metrics.as_dict(),
                    "test": oos.test.metrics.as_dict(),
                },
                indent=2,
            )
        )
    (run_dir / "leaderboard.json").write_text(
        json.dumps(
            [{"summary": r.summary(), "spec": r.spec.to_dict(), "metrics": r.metrics.as_dict()}
             for r in result.hall_of_fame],
            indent=2,
        )
    )

    hist_line = " → ".join(f"{h['best_fitness']:+.2f}" for h in result.history)
    md = f"""# Darwin — Champion Strategy Report

**{champ.spec.name}**  `[{champ.spec.fingerprint()}]`

> {champ.spec.rationale or "—"}

- Universe: `{', '.join(champ.spec.universe)}`  ·  Timeframe: `{champ.spec.timeframe}`
- Data: {meta.get('data_source', 'unknown')}  ·  Bars: {meta.get('bars', '?')}
- Evolution: {result.generations} generations · {result.evaluated} unique specs evaluated
- Claude operators: {meta.get('llm', 'off')}

## Performance

{_metrics_table(champ)}

Equity curve:
```
{sparkline(champ.equity)}
${champ.equity.iloc[0]:,.0f}  →  ${champ.equity.iloc[-1]:,.0f}
```
""" + (
        f"\n## Out-of-sample validation\n\nEvolved on the train window, **selected on "
        f"validation**, and reported on a **held-out TEST window the GA never saw** "
        f"(split at {oos.split_dates[0].date()} / {oos.split_dates[1].date()}).\n\n"
        f"{_oos_table(oos)}\n"
        if oos is not None else ""
    ) + f"""
## Fitness progression (best per generation)
`{hist_line}`

## Hall of fame
""" + "\n".join(f"{i+1}. {r.summary()}" for i, r in enumerate(result.hall_of_fame[:5]))

    md += "\n\n## Champion spec (backtestable, executable)\n```json\n" + champ.spec.to_json() + "\n```\n"
    (run_dir / "report.md").write_text(md, encoding="utf-8")
    return run_dir
