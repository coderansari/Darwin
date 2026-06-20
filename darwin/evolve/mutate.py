"""Deterministic genetic operators — mutation & crossover with no LLM calls.

These run every generation (fast, free, reproducible). Claude operators in
generate.py augment them with creative jumps. Every operator returns a *valid*
spec or falls back to the parent, so the population never contains junk.
"""
from __future__ import annotations

import copy
from typing import Any

import numpy as np

from ..strategy.spec import OPERATORS, StrategySpec, SpecError

_COMPARATORS = [">", "<", ">=", "<="]
_CROSSES = ["cross_above", "cross_below"]


def _safe(d: dict[str, Any], parent: StrategySpec) -> StrategySpec:
    try:
        spec = StrategySpec.from_dict(d)
        spec.validate()
        return spec
    except (SpecError, KeyError, TypeError):
        return parent


def _walk_leaves(node: dict[str, Any]):
    """Yield leaf condition dicts in a condition tree."""
    if "all" in node or "any" in node:
        key = "all" if "all" in node else "any"
        for child in node[key]:
            yield from _walk_leaves(child)
    elif "op" in node:
        yield node


# ---------------------------------------------------------------------------
# Mutation operators
# ---------------------------------------------------------------------------


def mutate_period(spec: StrategySpec, rng: np.random.Generator) -> StrategySpec:
    d = spec.to_dict()
    if not d["indicators"]:
        return spec
    i = int(rng.integers(0, len(d["indicators"])))
    delta = int(rng.integers(-6, 7))
    d["indicators"][i]["period"] = max(2, d["indicators"][i]["period"] + delta)
    return _safe(d, spec)


def mutate_threshold(spec: StrategySpec, rng: np.random.Generator) -> StrategySpec:
    d = spec.to_dict()
    leaves = [lf for cond in (d["entry"], d["exit"]) for lf in _walk_leaves(cond)]
    numeric = [lf for lf in leaves if isinstance(lf.get("right"), (int, float))]
    if not numeric:
        return spec
    leaf = numeric[int(rng.integers(0, len(numeric)))]
    val = float(leaf["right"])
    scale = abs(val) if abs(val) > 1 else 1.0
    leaf["right"] = round(val + float(rng.normal(0, 0.15)) * scale, 3)
    return _safe(d, spec)


def mutate_operator(spec: StrategySpec, rng: np.random.Generator) -> StrategySpec:
    d = spec.to_dict()
    leaves = [lf for cond in (d["entry"], d["exit"]) for lf in _walk_leaves(cond)]
    if not leaves:
        return spec
    leaf = leaves[int(rng.integers(0, len(leaves)))]
    op = leaf["op"]
    if op in _COMPARATORS:
        leaf["op"] = _COMPARATORS[int(rng.integers(0, len(_COMPARATORS)))]
    elif op in _CROSSES:
        leaf["op"] = _CROSSES[1 - _CROSSES.index(op)]
    return _safe(d, spec)


def mutate_risk(spec: StrategySpec, rng: np.random.Generator) -> StrategySpec:
    d = spec.to_dict()
    r = d["risk"]
    knob = rng.choice(["stop_loss_pct", "take_profit_pct", "max_drawdown_pct",
                       "max_position_pct", "trailing_stop_pct"])
    if knob == "trailing_stop_pct":
        r[knob] = round(float(np.clip(r[knob] + rng.normal(0, 0.03), 0.0, 0.4)), 3)
    elif knob == "max_position_pct":
        r[knob] = round(float(np.clip(r[knob] + rng.normal(0, 0.05), 0.05, 1.0)), 3)
    else:
        r[knob] = round(float(np.clip(r[knob] + rng.normal(0, 0.03), 0.02, 0.6)), 3)
    return _safe(d, spec)


def mutate_combinator(spec: StrategySpec, rng: np.random.Generator) -> StrategySpec:
    d = spec.to_dict()
    cond = d["entry"]
    if "all" in cond:
        d["entry"] = {"any": cond["all"]}
    elif "any" in cond:
        d["entry"] = {"all": cond["any"]}
    return _safe(d, spec)


_MUTATORS = [mutate_period, mutate_threshold, mutate_operator, mutate_risk, mutate_combinator]


def mutate(spec: StrategySpec, rng: np.random.Generator, n_ops: int = 1) -> StrategySpec:
    """Apply 1..n random mutation operators."""
    out = spec
    for _ in range(n_ops):
        op = _MUTATORS[int(rng.integers(0, len(_MUTATORS)))]
        out = op(out, rng)
    # Force a new name so lineage is visible.
    d = out.to_dict()
    d["name"] = f"{d['name'].split(' #')[0]} #{int(rng.integers(1000, 9999))}"
    return _safe(d, out)


# ---------------------------------------------------------------------------
# Crossover
# ---------------------------------------------------------------------------


def crossover(a: StrategySpec, b: StrategySpec, rng: np.random.Generator) -> StrategySpec:
    """Risk/sizing-gene crossover: keep parent A's entry/exit logic (so all
    indicator references stay valid) and inherit parent B's risk + sizing genes.
    Optionally swap the exit block if B's exit only references A's indicators."""
    child = a.to_dict()
    child["risk"] = copy.deepcopy(b.to_dict()["risk"])
    child["sizing"] = copy.deepcopy(b.to_dict()["sizing"])

    a_ids = {i["id"] for i in child["indicators"]} | {"open", "high", "low", "close", "volume"}
    b_dict = b.to_dict()
    b_exit_refs = {
        side for lf in _walk_leaves(b_dict["exit"]) for side in (lf["left"], lf["right"])
        if isinstance(side, str)
    }
    if b_exit_refs <= a_ids and rng.random() < 0.5:
        child["exit"] = copy.deepcopy(b_dict["exit"])

    child["name"] = f"{a.name.split(' #')[0]} x {b.name.split(' #')[0]} #{int(rng.integers(1000, 9999))}"
    return _safe(child, a)
