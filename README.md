# 🧬 Darwin — an evolutionary trading-strategy foundry for BNB Chain

> **BNB Hack: AI Trading Agent Edition** — Track 2 (Strategy Skills)
> Targeting: Track 2 placement · **Best Use of CMC Agent Hub** · **Best Use of BNB AI Agent SDK**

Most "AI strategy" tools do one thing: prompt an LLM once and print a strategy.
**Darwin breeds a population of them.** It pulls CoinMarketCap market data and
signals, generates a population of *backtestable strategy specs* with Claude,
scores each on a deterministic backtester using the **judges' exact rubric**
(risk-adjusted return, drawdown, **rule adherence**), and **evolves** the
survivors across generations into a champion — which it can then execute on BSC
via the Trust Wallet Agent Kit and register on-chain via the BNB AI Agent SDK.

```
                    ┌──────────────────────── DARWIN ────────────────────────┐
  CoinMarketCap ──► │  data + Fear&Greed ─► Claude seeds ─┐                   │
  (OHLCV, F&G,      │                                     ▼                   │
   trending)        │   ┌──── evolution loop (GA) ─────────────────┐         │
                    │   │ population ─► deterministic backtest ─►   │         │
                    │   │   fitness (Sortino, drawdown, adherence)  │         │
                    │   │      ▲                          │         │         │
                    │   │  Claude mutate/crossover ◄──────┘ select  │         │
                    │   └───────────────────────────────────────────┘        │
                    │                     │ champion spec                     │
                    │      ┌──────────────┼──────────────────┐               │
                    │      ▼              ▼                   ▼               │
                    │  report.md   TWAK gateway swap   BNB ERC-8004 identity │
                    └────────────────────────────────────────────────────────┘
                         Track 2          (TWAK)              (BNB SDK)
```

## Live result

Evolved on **live CoinMarketCap data** (2yr OHLCV + Fear & Greed) with Claude
(via an Anthropic-compatible gateway) as the evolution operator:

> **Champion: Dual-MA Trend Follower (Regime-Filtered) × ROC Momentum Pulse**
> +13.1% return · CAGR +6.6% · **Sharpe 1.58** · **max drawdown −1.1%** · 21 trades · **100% rule-adherence**
> — bred by the GA across 7 generations (gen 0 → 6: 48 trades/−12% DD refined down to 21 trades/−1.1% DD).

See `strategies/sample-champion.json` + `strategies/sample-champion-report.md`.

## Why this wins

- **Originality** — evolutionary search over an LLM-authored strategy DSL, not single-shot generation. The GA *breeds* hybrids (e.g. "Golden Cross × RSI Reversion").
- **Technical execution** — a real, deterministic, **lookahead-free** backtester with PancakeSwap-realistic costs. It survives adversarial scrutiny: we caught and killed a classic GA reward-hacking exploit (same-bar fills + zero costs) — see `darwin/strategy/backtest.py`.
- **Optimizes the rubric** — fitness rewards Sortino + capped return, penalizes drawdown, **squares rule-adherence**, and penalizes turnover. The winners are coherent, low-churn, risk-respecting strategies.
- **Real CMC signal usage** — blends RSI, **MACD**, and the **CMC Fear & Greed Index** into entry/exit rules (the Track-2 example archetype, shipped as a seed).
- **Full sponsor stack** — CMC Agent Hub (data + signal), BNB AI Agent SDK (on-chain identity), Trust Wallet Agent Kit (execution).

## Quickstart

```bash
python -m venv .venv && . .venv/Scripts/activate     # Windows: . .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in your keys (see below)

# Evolve a champion (works offline on synthetic data with no keys):
python -m darwin.cli evolve --universe BTC,ETH,BNB,SOL --generations 8

# Backtest any spec:
python -m darwin.cli backtest --spec strategies/sample-champion.json

# Dry-run execution (evaluates the live signal, plans a rule-gated swap):
python -m darwin.cli execute --spec strategies/sample-champion.json

# Register the agent's on-chain identity (BSC testnet, gas-sponsored):
python -m darwin.cli register --name darwin-foundry
```

`.env` keys (all optional — Darwin falls back to deterministic synthetic data/operators so it always runs):

| Key | Unlocks |
| --- | --- |
| `ANTHROPIC_API_KEY` | live Claude strategy generation + evolution |
| `CMC_PRO_API_KEY` | live CoinMarketCap OHLCV + Fear & Greed signal |
| `BSC_PRIVATE_KEY` | BNB on-chain identity registration (use a **testnet** key) |
| `TWAK_ACCESS_ID` / `TWAK_HMAC_SECRET` | Trust Wallet gateway swap routes |

## The three sponsor integrations

### 🧠 CoinMarketCap AI Agent Hub — *Best Use of Agent Hub*
- `darwin/cmc/client.py`: historical **OHLCV** (`/v2/cryptocurrency/ohlcv/historical`), latest quotes, and CMC's proprietary **Fear & Greed Index** (`/v3/fear-and-greed`).
- The Fear & Greed Index is a first-class **signal source** (`fgi`) in the strategy DSL — strategies gate entries/exits on sentiment regime.
- Strategies are authored as a **CMC Skill** (`skill/SKILL.md`) — the marketplace-native deliverable format.

### 🛠️ BNB AI Agent SDK — *Best Use of BNB AI Agent SDK*
- `darwin/identity/bnb.py`: registers Darwin's verifiable **ERC-8004 on-chain identity** on BSC testnet via the official `bnbagent` SDK (gas-sponsored). The agent's identity references the strategy it evolved.

### 🔐 Trust Wallet Agent Kit
- `darwin/execute/twak_gateway.py`: a **live HMAC-authenticated** client for the TWAK API gateway (`tws.trustwallet.com`). It signs requests correctly (RFC-2822 date, sorted-query `METHOD;PATH;QUERY;ACCESS_ID;NONCE;DATE`), resolves BSC assets live via `/v1/search/assets`, and structures PancakeSwap route requests (`/amber-api/v1/route`).
- *Status:* auth + live BSC asset resolution are confirmed working with portal creds; the swap-route computation is gated by Trust Wallet's backend (entitlement on the free portal tier). `execute` falls back cleanly. The "Best Use of TWAK" special prize is Track-1-scoped (live autonomous execution), so it isn't our target — but the integration is real.

## How it maps to Track 2 judging

| Criterion | Darwin |
| --- | --- |
| **Technical execution** | deterministic, lookahead-free backtester; real CMC + BNB on-chain integration; reproducible runs |
| **Originality** | evolutionary population search over an LLM-authored DSL; breeds strategy hybrids |
| **Real-world relevance** | a quant/agent-builder gets a backtested, rule-respecting spec ready to execute; the Skill is installable |
| **Demo** | one command evolves a champion and emits a full report; see `DEMO.md` |

## Repo layout

```
darwin/
  strategy/   spec DSL, indicators (incl. MACD), backtester, metrics
  cmc/        CoinMarketCap client (OHLCV, quotes, Fear & Greed)
  evolve/     seeds, deterministic GA operators, Claude operators, engine
  execute/    TWAK gateway + execution adapter
  identity/   BNB ERC-8004 on-chain identity
  report.py   judge-ready run reports
  cli.py      evolve / backtest / execute / register
skill/        SKILL.md — the installable CMC Skill (Track 2 deliverable)
strategies/   a sample evolved champion + its report
scripts/      smoke + evolution tests, demo
```

## Tests

```bash
python -m scripts.smoke_test     # deterministic core on synthetic data
python -m scripts.evolve_test    # offline GA convergence
```

Built with Claude Code. AI tooling encouraged — *"we care that it works, not how it was written."*
