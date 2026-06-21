<div align="center">

# 🧬 Darwin

### An evolutionary trading-strategy foundry for BNB Chain

*Most "AI strategy" tools prompt an LLM once and hand you a single strategy.*
**Darwin evolves a population — and proves the survivor out-of-sample.**

[![Track 2](https://img.shields.io/badge/BNB_Hack-Track_2_·_Strategy_Skills-F0B90B?style=flat-square)](https://coinmarketcap.com/api/hackathon/)
[![CoinMarketCap](https://img.shields.io/badge/CoinMarketCap-Agent_Hub-blue?style=flat-square)](https://coinmarketcap.com/api/)
[![On-chain](https://img.shields.io/badge/BNB-ERC--8004_agent_%231467-success?style=flat-square)](https://testnet.bscscan.com/tx/0x8f3c609817ab889d7160d3b4583e4d757bae873456b885d219cf3163ed8fdc7a)
[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)](LICENSE)

**[▶ Live dashboard](https://darwin-foundry.vercel.app)**  ·  **[On-chain proof](https://testnet.bscscan.com/tx/0x8f3c609817ab889d7160d3b4583e4d757bae873456b885d219cf3163ed8fdc7a)**  ·  **[Champion spec](strategies/sample-champion.json)**

</div>

---

## What it is

Darwin pulls **CoinMarketCap** market data and signals, has **Claude** author candidate
*backtestable strategy specs*, scores each on a **deterministic, lookahead-free backtester**
(risk-adjusted return, drawdown, and adherence to user-defined risk rules), and **evolves**
the survivors across generations into a champion. The champion is **forward-tested on a
held-out window it never saw**, exposed as a callable **CMC Skill (MCP)**, given a verifiable
**on-chain identity** on BNB Chain, and can plan a rule-gated swap via the **Trust Wallet Agent Kit**.

The Track 2 deliverable is a **backtestable spec, not a live agent** — and that is exactly
what Darwin produces: a readable, reproducible, executable JSON strategy with a full report.

```
                    ┌──────────────────────── DARWIN ────────────────────────┐
  CoinMarketCap ──► │  OHLCV + Fear&Greed + momentum/breadth ─► Claude seeds  │
  (data + signals)  │                                     │                   │
                    │   ┌──── evolution loop (GA) ────────▼───────────┐       │
                    │   │ population ─► deterministic backtest ─►      │       │
                    │   │   fitness (Sortino, drawdown, rule adherence)│       │
                    │   │      ▲                              │ select │       │
                    │   │  Claude mutate / crossover ◄────────┘        │       │
                    │   └──────────────────────────────────────────────┘      │
                    │            │ champion spec                               │
                    │   ┌────────┼─────────────────┬──────────────────┐       │
                    │   ▼        ▼                  ▼                  ▼       │
                    │  out-of-   MCP skill    TWAK gateway swap   BNB ERC-8004 │
                    │  sample    (find_skill)   (rule-gated)       identity    │
                    │  report                                                  │
                    └──────────────────────────────────────────────────────────┘
                       credibility   marketplace      (TWAK)        (BNB SDK)
```

---

## Why this should win Track 2

Track 2 is judged like quant research — *returns, drawdown, risk-adjusted performance, and
rule adherence, on a held-out market window.* Here is how Darwin answers each:

| Judging dimension | How Darwin answers it |
| --- | --- |
| **Held-out / not overfit** | Designs on a train window, **forward-tests on a held-out window it never saw** (`darwin/validation.py`). Warmup-aware, no look-ahead. Most entries report 100% in-sample numbers — Darwin shows the split. |
| **Risk-adjusted performance** | Fitness blends Sortino + Sharpe (clamped), a multiplicative drawdown penalty, and turnover penalties — so champions are coherent and low-churn, not lucky one-trade flukes. |
| **Drawdown** | The backtester runs a real risk engine (per-position stops/take-profits, trailing stops, a portfolio max-drawdown kill-switch). Champion: **−1.1% full-period / −1.0% out-of-sample** max drawdown. |
| **Rule adherence** | User risk rules are first-class and scored: adherence is **squared** in fitness, so a strategy that fights its own rules is crushed. Champion holds **100% adherence in- and out-of-sample.** |
| **CMC-native** | Uses CMC OHLCV + the proprietary **Fear & Greed Index**, plus CMC-derived **market momentum** and **breadth** regime signals — strategies gate on regime, not just price. |
| **Deliverable format** | A backtestable JSON spec **and** a callable **MCP Skill** (`evolve_strategy` / `backtest_spec`) any agent or the CMC Agent Hub can invoke. |

---

## The result

Evolved on **live CoinMarketCap data** (≈2yr daily OHLCV + Fear & Greed) with Claude as the
evolution operator:

> ### Dual-MA Trend Follower (Regime-Filtered) × ROC Momentum Pulse
> **+13.1%** return · CAGR **+6.6%** · **Sharpe 1.58** · **max drawdown −1.1%** · 21 trades · **100% rule-adherence**
> *bred by the GA across 7 generations (gen 0 → 6: 48 trades / −12% DD refined down to 21 trades / −1.1% DD).*

**Forward-tested out-of-sample** — designed on the first half of history, then run on a
**held-out window it never saw**:

| | In-sample (design) | Out-of-sample (held-out) |
| --- | --- | --- |
| Return | +12.8% | +0.1% |
| Sharpe | 2.01 | 0.05 |
| **Max drawdown** | −0.6% | **−1.0%** |
| **Rule adherence** | 100% | **100%** |
| Trades | 23 | 7 |

We report this honestly: out-of-sample, in a market regime it had never seen, the champion
**preserved capital, stayed inside its risk rules, and did not overtrade or blow up.** That
discipline — not a too-good-to-be-true return — is the signal of a strategy that isn't curve-fit.

→ `strategies/sample-champion.json` · `strategies/sample-champion-report.md` · or click **[the live dashboard](https://darwin-foundry.vercel.app)**.

---

## How it works

**1. Evolutionary, not single-shot.** A genetic algorithm searches over an LLM-authored
strategy DSL. Deterministic operators (mutate/crossover) run every generation for free and
reproducibly; Claude injects creative diversity and metric-guided "insight" mutations of the
champion. The GA *breeds* hybrids (e.g. "Golden Cross × RSI Reversion"). *(`darwin/evolve/`)*

**2. Deterministic, lookahead-free backtester.** Signals form on the close of bar *t−1*,
orders execute at the open of bar *t*, stops/take-profits check bar *t*'s high/low, equity
marks at the close — no same-bar fills, no look-ahead. PancakeSwap-realistic fees (0.25%) +
slippage on every leg. Hardened against optimizer reward-hacking. *(`darwin/strategy/backtest.py`)*

**3. Out-of-sample validation.** `run_backtest(trade_from=…)` lets a held-out window warm up
its indicators on prior bars but only count trades and equity from the window's start — a true
forward test with no cold-start and no leakage. Evolution selects the champion on a *validation*
window over the **full evaluated pool**; the *test* window is never used to select. *(`darwin/validation.py`)*

**4. Risk-aware fitness.** Sortino + Sharpe (clamped to resist flukes), a drawdown penalty,
**squared** rule-adherence, and turnover / min-trade penalties. *(`darwin/strategy/backtest.py:fitness_score`)*

### The strategy spec (DSL)

A spec is plain, executable JSON — readable by a human, generatable by an LLM, and the
backtester is the single source of truth for what it means:

```json
{
  "name": "MACD + RSI + Fear&Greed",
  "universe": ["BTC", "ETH", "BNB"],
  "timeframe": "1d",
  "indicators": [
    {"id": "macd", "type": "MACD", "fast": 12, "slow": 26, "signal": 9},
    {"id": "rsi",  "type": "RSI",  "period": 14}
  ],
  "entry": {"all": [
    {"left": "macd", "op": "cross_above", "right": "macd_sig"},
    {"left": "breadth", "op": ">", "right": 50},
    {"left": "fgi", "op": ">", "right": 30}
  ]},
  "exit": {"any": [{"left": "fgi", "op": ">", "right": 82}]},
  "risk": {"stop_loss_pct": 0.07, "take_profit_pct": 0.22, "max_drawdown_pct": 0.30, "trailing_stop_pct": 0.10},
  "sizing": {"type": "equal_weight"},
  "rationale": "MACD momentum, confirmed by market breadth and non-fearful sentiment"
}
```

Signals available to any condition: `fgi` (CMC Fear & Greed), `mom` (cross-sectional market
momentum), `breadth` (% of the universe above its 50-bar trend), plus indicators and prices.

---

## A callable Marketplace skill (MCP)

Darwin isn't just a CLI — it's a **CoinMarketCap Skill**. Any MCP client (Claude Desktop,
Cursor, the CMC Agent Hub's `find_skill` router) can call it and get agent-ready, backtestable output:

```bash
pip install "mcp>=1.2.0"
python -m darwin.mcp_server          # exposes the tools below over MCP (stdio)
```

| Tool | What it does |
| --- | --- |
| `evolve_strategy` | Evolve a champion from CMC data with train / validation / **held-out test** scoring. |
| `backtest_spec` | Backtest any StrategySpec — deterministic, lookahead-free, fees + slippage. |
| `spec_schema` | Return the StrategySpec DSL guide. |

Packaging: `skill/SKILL.md` (frontmatter + `allowed-tools`), `skill/skill.json` (marketplace
manifest), `skill/mcp_config.json` (wires both the Darwin server and the CMC Data MCP).

---

## Quickstart

```bash
python -m venv .venv && . .venv/Scripts/activate     # macOS/Linux: . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                                  # fill in keys (all optional — see below)

# Evolve a champion (works fully offline on deterministic synthetic data with no keys):
python -m darwin.cli evolve --universe BTC,ETH,BNB,SOL --generations 8

# Backtest any spec:
python -m darwin.cli backtest --spec strategies/sample-champion.json

# Dry-run execution (evaluates the live signal, plans a rule-gated swap):
python -m darwin.cli execute --spec strategies/sample-champion.json

# Register the agent's on-chain identity (BSC testnet, gas-sponsored):
python -m darwin.cli register --name darwin-foundry

# Serve Darwin as a callable CMC Skill over MCP:
pip install "mcp>=1.2.0" && python -m darwin.mcp_server
```

`.env` keys — **all optional.** With none set, Darwin falls back to deterministic synthetic
data + operators, so it *always* runs; keys upgrade it to live:

| Key | Unlocks |
| --- | --- |
| `ANTHROPIC_API_KEY` (+ optional `ANTHROPIC_BASE_URL`, `DARWIN_MODEL`) | live Claude strategy generation + evolution |
| `CMC_PRO_API_KEY` | live CoinMarketCap OHLCV + Fear & Greed |
| `BSC_PRIVATE_KEY` | BNB on-chain identity registration (use a **testnet** key) |
| `TWAK_ACCESS_ID` / `TWAK_HMAC_SECRET` | Trust Wallet gateway swap routes |

---

## The live dashboard

A premium, mobile-first dashboard renders the locked champion on real data — equity curve with
the out-of-sample boundary marked, the in-sample-vs-held-out comparison, the evolution timeline,
live CMC Fear & Greed, and the on-chain identity. It also has a live **"Evolve live"** button
that runs Claude as the GA's mutate operator on the spot.

```bash
cd web && npm install && npm run dev     # http://localhost:3000
```

Deploys to Vercel (root directory `web`). Built with Next.js + Tailwind + Recharts. See `web/README.md`.

---

## The three sponsor integrations

### 🧠 CoinMarketCap AI Agent Hub
- `darwin/cmc/client.py`: historical **OHLCV** (`/v2/cryptocurrency/ohlcv/historical`), quotes, and the proprietary **Fear & Greed Index** (`/v3/fear-and-greed`).
- Fear & Greed is a first-class **signal** (`fgi`); Darwin also derives **`mom`** (market momentum) and **`breadth`** from CMC OHLCV — so strategies gate on market regime, not just price.
- Packaged as an installable **CMC Skill** (`skill/`) and a callable MCP server — the marketplace-native deliverable.

### 🛠️ BNB AI Agent SDK
- `darwin/identity/bnb.py`: registers Darwin's verifiable **ERC-8004 on-chain identity** on BSC testnet via the official `bnbagent` SDK (gas-sponsored).
- **Live on-chain proof:** agentId `1467`, registry `0x8004A818BFB912233c491871b3d84c89A494BD9e` — [tx on BSC testnet ↗](https://testnet.bscscan.com/tx/0x8f3c609817ab889d7160d3b4583e4d757bae873456b885d219cf3163ed8fdc7a).

### 🔐 Trust Wallet Agent Kit
- `darwin/execute/twak_gateway.py`: a **live HMAC-authenticated** client for the TWAK gateway (`tws.trustwallet.com`) — correct request signing (RFC-2822 date, sorted-query `METHOD;PATH;QUERY;ACCESS_ID;NONCE;DATE`), live BSC asset resolution (`/v1/search/assets`), and PancakeSwap route requests (`/amber-api/v1/route`).
- *Status:* auth + live asset resolution work on portal credentials; swap-route computation returns a server-side error on the free portal tier, so `execute` shows a dry-run plan. TWAK is a supporting integration here (live autonomous execution is Track 1's focus).

---

## What's real vs simulated (transparency)

| | Status |
| --- | --- |
| Evolution, backtester, fitness, out-of-sample split | ✅ real, deterministic, reproducible |
| Champion result + OOS numbers | ✅ from live CMC data (offline synthetic fallback if no key) |
| CMC OHLCV + Fear & Greed | ✅ live API |
| On-chain ERC-8004 identity | ✅ real BSC-testnet transaction (agent #1467) |
| MCP skill (`evolve_strategy` / `backtest_spec`) | ✅ callable |
| TWAK swap execution | ⚠️ auth + asset resolution live; route computation gated on portal tier → dry-run plan |

---

## Repo layout

```
darwin/
  strategy/      spec DSL, indicators (incl. MACD), backtester, metrics
  cmc/           CoinMarketCap client (OHLCV, quotes, Fear & Greed)
  evolve/        seeds, deterministic GA operators, LLM operators, engine
  validation.py  out-of-sample train/validation/test + holdout (no look-ahead)
  execute/       TWAK gateway + execution adapter
  identity/      BNB ERC-8004 on-chain identity
  mcp_server.py  Darwin as a callable MCP Skill
  cli.py         evolve / backtest / execute / register
skill/           SKILL.md + skill.json + mcp_config.json — the CMC Skill package
strategies/      a sample evolved champion + its report
scripts/         smoke / evolution / out-of-sample tests, dashboard export
web/             the live Next.js dashboard
```

## Tests

```bash
python -m scripts.smoke_test     # deterministic core on synthetic data
python -m scripts.evolve_test    # offline GA convergence (asserts a usable champion)
python -m scripts.oos_test       # out-of-sample split is sound + lookahead-free
```

---

<div align="center">

**Built for BNB Hack 2026 · Track 2 (Strategy Skills).**  ·  MIT licensed.

</div>
