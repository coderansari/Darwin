# Darwin Strategy Spec — DSL Reference

A spec is JSON validated by `darwin/strategy/spec.py`. It is deterministic: the
same spec + same data always produces the same backtest.

## Top-level fields

| Field | Type | Notes |
| --- | --- | --- |
| `name` | string | human label |
| `universe` | string[] | CoinMarketCap symbols, e.g. `["BTC","ETH","BNB"]` |
| `timeframe` | string | `1d`, `1h`, `1w` |
| `indicators` | Indicator[] | see below |
| `entry` | Condition | opens a long when true |
| `exit` | Condition | closes the long when true |
| `risk` | Risk | user-defined rules (enforced by the backtester) |
| `sizing` | Sizing | `equal_weight` or `fixed_fraction` |
| `rationale` | string | the edge being exploited |

## Indicators

| type | params | output |
| --- | --- | --- |
| `SMA` | `period`, `source` | simple moving average |
| `EMA` | `period`, `source` | exponential moving average |
| `RSI` | `period` | 0–100 momentum oscillator |
| `ROC` | `period`, `source` | rate of change (%) |
| `ATR` | `period` | average true range |
| `MACD` | `fast`, `slow`, `signal`, `source` | MACD line (EMA_fast − EMA_slow) |
| `MACD_SIGNAL` | `fast`, `slow`, `signal`, `source` | signal line (EMA of MACD) |
| `MACD_HIST` | `fast`, `slow`, `signal`, `source` | MACD − signal |
| `PRICE` | `source` | raw price source |

`source` ∈ {`open`, `high`, `low`, `close`, `volume`}. Defaults: `period=14`,
`fast=12`, `slow=26`, `signal=9`, `source="close"`.

## Signals (market-wide)

| name | meaning |
| --- | --- |
| `fgi` | CoinMarketCap Fear & Greed Index, 0–100 |

Use a signal anywhere an indicator id is allowed, e.g. `{"left":"fgi","op":"<","right":25}`.

## Conditions

A condition is one of:
- `{"all": [ ...conditions ]}` — logical AND
- `{"any": [ ...conditions ]}` — logical OR
- `{"left": <ref>, "op": <op>, "right": <ref>}` — a leaf

`<ref>` is an indicator id, a signal name, a price source, or a number.
`<op>` ∈ {`>`, `<`, `>=`, `<=`, `cross_above`, `cross_below`}.

## Risk (enforced, not advisory)

| field | meaning |
| --- | --- |
| `max_position_pct` | max fraction of equity per position |
| `max_open_positions` | concurrent position cap |
| `stop_loss_pct` | per-position hard stop |
| `take_profit_pct` | per-position target |
| `max_drawdown_pct` | portfolio kill-switch (flatten + halt) |
| `trailing_stop_pct` | trailing stop (0 disables) |

The backtester enforces these rules, so a Darwin strategy adheres to its
user-defined rules **by construction** — the same engine gates live execution.

## Execution model (lookahead-free)

- Signals evaluated on the close of bar `t-1`.
- Orders execute at the open of bar `t`.
- Stops / take-profits check bar `t`'s high/low (never on the entry bar — no
  intrabar lookahead).
- Costs: 0.25% PancakeSwap fee + slippage on every entry and exit.
