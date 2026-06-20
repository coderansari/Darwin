"""Darwin command-line interface.

  python -m darwin.cli evolve  --universe BTC,ETH,BNB,SOL --generations 8
  python -m darwin.cli backtest --spec runs/<run>/champion.json
  python -m darwin.cli execute  --spec runs/<run>/champion.json [--live]
  python -m darwin.cli register --name darwin-foundry

`evolve` uses live CoinMarketCap data + Claude when keys are present, and falls
back to deterministic synthetic data + operators otherwise — so it always runs.
"""
from __future__ import annotations

import argparse
import sys

from . import report
from .config import settings
from .data_source import load_market_data, load_signals
from .evolve.engine import EvolutionConfig, Evolver
from .evolve.generate import StrategyGenerator, market_context
from .strategy.backtest import run_backtest
from .strategy.spec import StrategySpec


def _print(msg: str) -> None:
    print(msg, flush=True)


def _fg_class(v: float) -> str:
    if v < 25:
        return "Extreme Fear"
    if v < 45:
        return "Fear"
    if v < 55:
        return "Neutral"
    if v < 75:
        return "Greed"
    return "Extreme Greed"


def cmd_evolve(args: argparse.Namespace) -> int:
    universe = [s.strip().upper() for s in args.universe.split(",") if s.strip()]
    force_syn = args.synthetic or not settings.has_cmc

    _print(f"Darwin - evolving on {universe} ({'synthetic' if force_syn else 'CoinMarketCap'} data)")
    data = load_market_data(universe, count=args.bars, timeframe=args.timeframe, force_synthetic=force_syn)

    # CMC Fear & Greed signal (proprietary CMC data) -> regime context + condition source.
    signals = load_signals(count=args.bars, timeframe=args.timeframe, force_synthetic=force_syn)
    fgi_now = float(signals["fgi"].iloc[-1])
    fg_latest = {"value": int(round(fgi_now)), "value_classification": _fg_class(fgi_now)}
    src = "synthetic" if force_syn else "CMC"
    _print(f"  Fear & Greed ({src}): {fg_latest['value']} ({fg_latest['value_classification']})")

    generator = None if args.no_llm else StrategyGenerator()
    llm_state = "on" if (generator and generator.enabled) else "off"
    _print(f"  Claude operators: {llm_state}  |  model: {settings.model if llm_state=='on' else '-'}")

    context = market_context(data, fg_latest)
    cfg = EvolutionConfig(
        generations=args.generations, pop_size=args.pop, elite=args.elite, seed=args.seed
    )
    evolver = Evolver(data, signals=signals, generator=generator, config=cfg)

    def on_gen(gen, partial, ranked):
        h = partial.history[-1]
        _print(f"  gen {gen}: best={h['best_fitness']:+.3f} mean={h['mean_fitness']:+.3f} | {h['best']}")

    _print("")
    result = evolver.evolve(universe, context=context, on_generation=on_gen)

    meta = {
        "data_source": "synthetic" if force_syn else "CoinMarketCap",
        "bars": args.bars,
        "llm": llm_state,
    }
    run_dir = report.render(result, meta=meta)
    _print("")
    _print(f"CHAMPION: {result.champion.summary()}")
    _print(f"Report:   {run_dir / 'report.md'}")
    _print(f"Spec:     {run_dir / 'champion.json'}")
    return 0


def cmd_backtest(args: argparse.Namespace) -> int:
    spec = StrategySpec.from_json(open(args.spec, encoding="utf-8").read())
    force_syn = args.synthetic or not settings.has_cmc
    data = load_market_data(spec.universe, count=args.bars, timeframe=spec.timeframe, force_synthetic=force_syn)
    result = run_backtest(spec, data)
    _print(result.summary())
    for k, v in result.metrics.as_dict().items():
        _print(f"  {k}: {v}")
    return 0


def cmd_execute(args: argparse.Namespace) -> int:
    from .execute.twak import execute_spec  # lazy: optional dependency surface

    spec = StrategySpec.from_json(open(args.spec, encoding="utf-8").read())
    return execute_spec(spec, live=args.live, amount=args.amount)


def cmd_register(args: argparse.Namespace) -> int:
    from .identity.bnb import register_agent

    return register_agent(name=args.name, description=args.description)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="darwin", description="Evolutionary trading-strategy foundry")
    sub = p.add_subparsers(dest="command", required=True)

    e = sub.add_parser("evolve", help="evolve a champion strategy")
    e.add_argument("--universe", default="BTC,ETH,BNB,SOL")
    e.add_argument("--bars", type=int, default=500)
    e.add_argument("--timeframe", default="1d")
    e.add_argument("--generations", type=int, default=8)
    e.add_argument("--pop", type=int, default=20)
    e.add_argument("--elite", type=int, default=3)
    e.add_argument("--seed", type=int, default=42)
    e.add_argument("--synthetic", action="store_true", help="force synthetic data")
    e.add_argument("--no-llm", action="store_true", help="disable Claude operators")
    e.set_defaults(func=cmd_evolve)

    b = sub.add_parser("backtest", help="backtest a single spec file")
    b.add_argument("--spec", required=True)
    b.add_argument("--bars", type=int, default=500)
    b.add_argument("--synthetic", action="store_true")
    b.set_defaults(func=cmd_backtest)

    x = sub.add_parser("execute", help="execute the champion via Trust Wallet Agent Kit")
    x.add_argument("--spec", required=True)
    x.add_argument("--amount", type=float, default=10.0, help="quote notional (e.g. USDT)")
    x.add_argument("--live", action="store_true", help="actually send the swap (default: dry-run)")
    x.set_defaults(func=cmd_execute)

    r = sub.add_parser("register", help="register the agent identity on BNB Chain (ERC-8004)")
    r.add_argument("--name", default="darwin-foundry")
    r.add_argument("--description", default="Darwin evolutionary trading-strategy agent")
    r.set_defaults(func=cmd_register)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
