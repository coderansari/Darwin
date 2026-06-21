"""Darwin as an MCP server — the CoinMarketCap *Skill* surface.

This is what makes Darwin a first-class CMC Skill rather than a CLI: any
MCP-compatible client (Claude Desktop, Cursor, the CMC Agent Hub's `find_skill`
router) can call these tools and get an agent-ready, **backtestable** strategy
spec with out-of-sample metrics — exactly the Track 2 deliverable.

It pairs with the CMC Data MCP: Darwin consumes CoinMarketCap OHLCV + Fear & Greed
(plus its own derived market regime signals) and emits a validated StrategySpec.

Run:  python -m darwin.mcp_server          # stdio transport

Requires the optional `skill` extra:  pip install "mcp>=1.2.0"
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .config import settings
from .data_source import derive_market_signals, load_market_data, load_signals
from .evolve.engine import EvolutionConfig, Evolver
from .evolve.generate import StrategyGenerator, market_context
from .strategy.backtest import run_backtest
from .strategy.spec import SPEC_GUIDE, StrategySpec
from .validation import DEFAULT_SPLITS, evaluate_oos, select_by_validation, train_split

mcp = FastMCP("darwin")


def _metrics(m) -> dict:
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.as_dict().items()}


@mcp.tool()
def evolve_strategy(
    universe: str = "BTC,ETH,BNB,SOL",
    generations: int = 6,
    bars: int = 400,
    use_llm: bool = False,
    synthetic: bool = False,
) -> dict:
    """Evolve a backtestable trading-strategy spec from CoinMarketCap market data.

    Darwin evolves a population on a TRAIN window, selects the champion on a
    VALIDATION window, and reports performance on a held-out TEST window — so the
    result is robust, not curve-fit. Returns the champion StrategySpec plus
    in-sample (train) vs out-of-sample (validation/test) metrics.

    Args:
        universe: comma-separated CMC symbols, e.g. "BTC,ETH,BNB,SOL".
        generations: GA generations to run.
        bars: history length (daily bars).
        use_llm: if true, use Claude as the generation/mutation operator.
        synthetic: force deterministic offline data (no API calls).
    """
    uni = [s.strip().upper() for s in universe.split(",") if s.strip()]
    syn = synthetic or not settings.has_cmc
    data = load_market_data(uni, count=bars, force_synthetic=syn)
    signals = load_signals(count=bars, force_synthetic=syn)
    signals.update(derive_market_signals(data))

    gen = StrategyGenerator() if use_llm else None
    ctx = market_context(data, None)
    tr_d, tr_s, _, _ = train_split(data, signals, DEFAULT_SPLITS)
    ev = Evolver(
        tr_d, signals=tr_s, generator=gen,
        config=EvolutionConfig(generations=generations, pop_size=16),
    )
    res = ev.evolve(uni, context=ctx)
    cands = [r.spec for r in res.hall_of_fame] or [res.champion.spec]
    champ, _ = select_by_validation(cands, data, signals, DEFAULT_SPLITS)
    oos = evaluate_oos(champ, data, signals, DEFAULT_SPLITS)
    return {
        "champion": champ.to_dict(),
        "metrics": {
            "train": _metrics(oos.train.metrics),
            "validation": _metrics(oos.validation.metrics),
            "test": _metrics(oos.test.metrics),
        },
        "split_dates": [str(d.date()) for d in oos.split_dates],
        "note": "test metrics are out-of-sample (held out from selection).",
    }


@mcp.tool()
def backtest_spec(spec_json: str, bars: int = 400, synthetic: bool = False) -> dict:
    """Backtest a StrategySpec (JSON string) on CoinMarketCap data; return metrics.

    Deterministic, lookahead-free, with PancakeSwap-realistic fees + slippage.
    """
    spec = StrategySpec.from_json(spec_json)
    spec.validate()
    syn = synthetic or not settings.has_cmc
    data = load_market_data(spec.universe, count=bars, timeframe=spec.timeframe, force_synthetic=syn)
    signals = load_signals(count=bars, timeframe=spec.timeframe, force_synthetic=syn)
    signals.update(derive_market_signals(data))
    r = run_backtest(spec, data, signals=signals)
    return {"summary": r.summary(), "metrics": _metrics(r.metrics)}


@mcp.tool()
def spec_schema() -> str:
    """Return the Darwin StrategySpec DSL guide — the exact JSON shape a valid,
    backtestable strategy must follow (indicators, signals, conditions, risk)."""
    return SPEC_GUIDE


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
