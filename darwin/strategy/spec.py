"""The Darwin Strategy Spec DSL.

A *spec* is a deterministic, backtestable description of a trading strategy.
It is plain JSON so Claude can generate and mutate it, and so a human (or judge)
can read and re-run it. The backtester (backtest.py) is the single source of
truth for what a spec *means*.

Design goals:
  * Deterministic — same spec + same data => same result, always.
  * LLM-friendly — a flat, explicit schema with a small operator vocabulary.
  * Risk-rule-first — user-defined risk rules are first-class, because the
    hackathon judges score *rule adherence* and *drawdown*, not just PnL.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

INDICATOR_TYPES = {"SMA", "EMA", "RSI", "ATR", "ROC", "PRICE", "MACD", "MACD_SIGNAL", "MACD_HIST"}
PRICE_SOURCES = {"open", "high", "low", "close", "volume"}
# Market-wide signals injected by the backtester (e.g. CMC Fear & Greed Index).
SIGNAL_SOURCES = {"fgi"}
OPERATORS = {">", "<", ">=", "<=", "cross_above", "cross_below"}
COMBINATORS = {"all", "any"}
SIZING_TYPES = {"equal_weight", "fixed_fraction"}


class SpecError(ValueError):
    """Raised when a spec is structurally invalid."""


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class Indicator:
    id: str
    type: str
    period: int = 14
    source: str = "close"
    # MACD parameters (used only by MACD / MACD_SIGNAL / MACD_HIST types).
    fast: int = 12
    slow: int = 26
    signal: int = 9

    def validate(self) -> None:
        if self.type not in INDICATOR_TYPES:
            raise SpecError(f"unknown indicator type: {self.type}")
        if self.type in ("MACD", "MACD_SIGNAL", "MACD_HIST"):
            if not (0 < self.fast < self.slow) or self.signal < 1:
                raise SpecError(f"indicator {self.id}: need 0 < fast < slow and signal >= 1")
        elif self.type != "PRICE" and self.period < 1:
            raise SpecError(f"indicator {self.id}: period must be >= 1")
        if self.source not in PRICE_SOURCES:
            raise SpecError(f"indicator {self.id}: bad source {self.source}")


@dataclass
class Risk:
    max_position_pct: float = 0.25      # max fraction of equity per position
    max_open_positions: int = 3
    stop_loss_pct: float = 0.08         # per-position hard stop
    take_profit_pct: float = 0.25       # per-position target
    max_drawdown_pct: float = 0.30      # portfolio kill-switch
    trailing_stop_pct: float = 0.0      # 0 = disabled

    def validate(self) -> None:
        if not 0 < self.max_position_pct <= 1:
            raise SpecError("max_position_pct must be in (0, 1]")
        if self.max_open_positions < 1:
            raise SpecError("max_open_positions must be >= 1")
        for name in ("stop_loss_pct", "take_profit_pct", "max_drawdown_pct"):
            v = getattr(self, name)
            if not 0 < v < 1:
                raise SpecError(f"{name} must be in (0, 1)")


@dataclass
class Sizing:
    type: str = "equal_weight"
    fraction: float = 0.2  # used when type == fixed_fraction

    def validate(self) -> None:
        if self.type not in SIZING_TYPES:
            raise SpecError(f"unknown sizing type: {self.type}")


@dataclass
class StrategySpec:
    name: str
    universe: list[str]
    timeframe: str = "1d"
    indicators: list[Indicator] = field(default_factory=list)
    entry: dict[str, Any] = field(default_factory=dict)
    exit: dict[str, Any] = field(default_factory=dict)
    risk: Risk = field(default_factory=Risk)
    sizing: Sizing = field(default_factory=Sizing)
    rationale: str = ""

    # ---- (de)serialization -------------------------------------------------

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "StrategySpec":
        try:
            inds = [Indicator(**i) for i in d.get("indicators", [])]
            risk = Risk(**d["risk"]) if isinstance(d.get("risk"), dict) else Risk()
            sizing = Sizing(**d["sizing"]) if isinstance(d.get("sizing"), dict) else Sizing()
            return cls(
                name=str(d["name"]),
                universe=list(d["universe"]),
                timeframe=str(d.get("timeframe", "1d")),
                indicators=inds,
                entry=d.get("entry", {}),
                exit=d.get("exit", {}),
                risk=risk,
                sizing=sizing,
                rationale=str(d.get("rationale", "")),
            )
        except (KeyError, TypeError) as e:
            raise SpecError(f"malformed spec: {e}") from e

    @classmethod
    def from_json(cls, s: str) -> "StrategySpec":
        return cls.from_dict(json.loads(s))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def fingerprint(self) -> str:
        """Stable hash of the strategy logic (ignores name/rationale)."""
        core = {
            "universe": sorted(self.universe),
            "timeframe": self.timeframe,
            "indicators": sorted((asdict(i) for i in self.indicators), key=lambda d: d["id"]),
            "entry": self.entry,
            "exit": self.exit,
            "risk": asdict(self.risk),
            "sizing": asdict(self.sizing),
        }
        blob = json.dumps(core, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:12]

    # ---- validation --------------------------------------------------------

    def validate(self) -> None:
        if not self.name:
            raise SpecError("spec needs a name")
        if not self.universe:
            raise SpecError("universe cannot be empty")
        for ind in self.indicators:
            ind.validate()
        self.risk.validate()
        self.sizing.validate()
        ids = {i.id for i in self.indicators}
        _validate_condition(self.entry, ids, "entry")
        _validate_condition(self.exit, ids, "exit")


def _validate_condition(node: dict[str, Any], ind_ids: set[str], where: str) -> None:
    if not node:
        raise SpecError(f"{where} condition is empty")
    if "all" in node or "any" in node:
        key = "all" if "all" in node else "any"
        children = node[key]
        if not isinstance(children, list) or not children:
            raise SpecError(f"{where}: {key} must be a non-empty list")
        for child in children:
            _validate_condition(child, ind_ids, where)
        return
    # leaf condition: {left, op, right}
    for k in ("left", "op", "right"):
        if k not in node:
            raise SpecError(f"{where}: leaf condition missing '{k}'")
    if node["op"] not in OPERATORS:
        raise SpecError(f"{where}: bad operator {node['op']}")
    for side in ("left", "right"):
        ref = node[side]
        if isinstance(ref, str) and ref not in ind_ids and ref not in PRICE_SOURCES and ref not in SIGNAL_SOURCES:
            raise SpecError(f"{where}: unknown reference '{ref}'")


# ---------------------------------------------------------------------------
# Schema guide handed to Claude
# ---------------------------------------------------------------------------

SPEC_GUIDE = """A StrategySpec is JSON with this shape:

{
  "name": "short human label",
  "universe": ["BTC", "ETH", "BNB"],        // CoinMarketCap symbols
  "timeframe": "1d",
  "indicators": [
    {"id": "sma_fast", "type": "SMA", "source": "close", "period": 10},
    {"id": "sma_slow", "type": "SMA", "source": "close", "period": 30},
    {"id": "rsi",      "type": "RSI", "period": 14},
    {"id": "macd",     "type": "MACD", "source": "close", "fast": 12, "slow": 26, "signal": 9},
    {"id": "macd_sig", "type": "MACD_SIGNAL", "source": "close", "fast": 12, "slow": 26, "signal": 9}
  ],
  "entry": {"all": [
    {"left": "sma_fast", "op": "cross_above", "right": "sma_slow"},
    {"left": "rsi", "op": "<", "right": 70}
  ]},
  "exit": {"any": [
    {"left": "sma_fast", "op": "cross_below", "right": "sma_slow"},
    {"left": "rsi", "op": ">", "right": 80}
  ]},
  "risk": {
    "max_position_pct": 0.25, "max_open_positions": 3,
    "stop_loss_pct": 0.08, "take_profit_pct": 0.25,
    "max_drawdown_pct": 0.30, "trailing_stop_pct": 0.0
  },
  "sizing": {"type": "equal_weight"},
  "rationale": "one sentence on the edge this strategy exploits"
}

Rules:
- indicator.type in {SMA, EMA, RSI, ATR, ROC, PRICE, MACD, MACD_SIGNAL, MACD_HIST}. PRICE just exposes a raw price source.
- MACD/MACD_SIGNAL/MACD_HIST use fast/slow/signal (default 12/26/9), not period. Cross MACD over MACD_SIGNAL for classic signals.
- A condition is either {"all":[...]}, {"any":[...]}, or a leaf {"left","op","right"}.
- op in {">","<",">=","<=","cross_above","cross_below"}.
- left/right are either an indicator id, a price source (open/high/low/close/volume), or a number.
- Strategies are LONG/FLAT only. Entry opens, exit (or a risk rule) closes.
- Keep it simple and economically sensible; the backtester is strict and deterministic.
"""
