"""Claude-powered strategy generation operators.

Gracefully degrades: if no ANTHROPIC_API_KEY is configured, `enabled` is False and
the engine runs on deterministic operators + the seed library alone. So Darwin
always produces a result; Claude makes it smarter, not mandatory.
"""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from ..config import settings
from ..strategy.metrics import Metrics
from ..strategy.spec import SpecError, StrategySpec
from . import prompts


def _extract_json(text: str):
    """Pull the first JSON array or object out of a model response."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    start = min(
        (i for i in (text.find("["), text.find("{")) if i != -1),
        default=-1,
    )
    if start == -1:
        raise ValueError("no JSON found in response")
    # Balance brackets to find the matching close.
    open_ch = text[start]
    close_ch = "]" if open_ch == "[" else "}"
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    return json.loads(text[start:])  # last-ditch


def market_context(data: dict[str, pd.DataFrame], fear_greed: dict | None = None) -> str:
    lines = ["Per-symbol recent stats (most recent window):"]
    for sym, df in data.items():
        if df.empty or len(df) < 31:
            lines.append(f"  {sym}: insufficient history")
            continue
        close = df["close"]
        ret_7d = close.iloc[-1] / close.iloc[-8] - 1.0
        ret_30d = close.iloc[-1] / close.iloc[-31] - 1.0
        vol = float(close.pct_change().tail(30).std(ddof=0) * np.sqrt(365))
        lines.append(
            f"  {sym}: price={close.iloc[-1]:.4g}  7d={ret_7d:+.1%}  "
            f"30d={ret_30d:+.1%}  ann_vol={vol:.0%}"
        )
    if fear_greed:
        lines.append(
            f"CMC Fear & Greed Index: {fear_greed.get('value')} "
            f"({fear_greed.get('value_classification')})"
        )
    return "\n".join(lines)


class StrategyGenerator:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.model
        self._client = None
        if self.api_key:
            from anthropic import Anthropic  # lazy import

            kwargs = {"api_key": self.api_key}
            if settings.anthropic_base_url:           # e.g. DGRID gateway
                kwargs["base_url"] = settings.anthropic_base_url
            self._client = Anthropic(**kwargs)

    @property
    def enabled(self) -> bool:
        return self._client is not None

    # ---- low-level call ----------------------------------------------------

    def _call(self, user: str, max_tokens: int = 4096, temperature: float = 1.0) -> str:
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=prompts.SYSTEM,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in msg.content if block.type == "text")

    def _parse_one(self, text: str) -> StrategySpec | None:
        try:
            spec = StrategySpec.from_dict(_extract_json(text))
            spec.validate()
            return spec
        except (SpecError, ValueError, KeyError, TypeError):
            return None

    # ---- operators ---------------------------------------------------------

    def generate_population(self, context: str, n: int, universe: list[str]) -> list[StrategySpec]:
        if not self.enabled:
            return []
        text = self._call(prompts.population_prompt(context, n, universe), max_tokens=8000)
        raw = _extract_json(text)
        items = raw if isinstance(raw, list) else [raw]
        out: list[StrategySpec] = []
        for item in items:
            try:
                spec = StrategySpec.from_dict(item)
                spec.validate()
                out.append(spec)
            except (SpecError, KeyError, TypeError):
                continue
        return out

    def claude_mutate(self, spec: StrategySpec, metrics: Metrics, context: str) -> StrategySpec | None:
        if not self.enabled:
            return None
        text = self._call(prompts.mutate_prompt(spec, metrics, context), temperature=0.8)
        return self._parse_one(text)

    def claude_crossover(self, a: StrategySpec, b: StrategySpec, context: str) -> StrategySpec | None:
        if not self.enabled:
            return None
        text = self._call(prompts.crossover_prompt(a, b, context), temperature=0.8)
        return self._parse_one(text)
