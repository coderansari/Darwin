# 🧬 Darwin — an evolutionary trading-strategy foundry for BNB Chain

> **BNB Hack: AI Trading Agent Edition** — built for Track 2 (Strategy Skills).
> Also exercises the CoinMarketCap Agent Hub and the BNB AI Agent SDK.

A common approach for "AI strategy" tools is to prompt an LLM once and return a
single strategy. Darwin takes a different path: it evolves a *population*. It pulls
CoinMarketCap market data and signals, generates candidate *backtestable strategy
specs* with an LLM, scores each on a deterministic backtester (risk-adjusted return,
drawdown, and adherence to user-defined risk rules), and evolves the survivors across
generations into a champion — which can then execute on BSC via the Trust Wallet
Agent Kit and register an on-chain identity via the BNB AI Agent SDK.

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

## Highlights

- **Evolutionary, not single-shot** — population search over an LLM-authored strategy DSL; the GA *breeds* hybrids (e.g. "Golden Cross × RSI Reversion") instead of emitting one prompt-generated strategy.
- **Deterministic, lookahead-free backtester** — execution at next-bar open, no same-bar fills, PancakeSwap-realistic fees + slippage. Hardened against optimizer reward-hacking (over-trading, compounding flukes, rule-fighting) — see `darwin/strategy/backtest.py`.
- **Risk-aware fitness** — Sortino + Sharpe (clamped), drawdown penalty, squared rule-adherence, turnover and min-trade penalties. Champions are coherent, low-churn, and risk-respecting.
- **CMC signals in the rules** — blends RSI, MACD, and the CoinMarketCap Fear & Greed Index into entry/exit conditions.
- **Full stack** — CMC Agent Hub (data + signal), BNB AI Agent SDK (on-chain identity), Trust Wallet Agent Kit (execution).

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

### 🧠 CoinMarketCap AI Agent Hub
- `darwin/cmc/client.py`: historical **OHLCV** (`/v2/cryptocurrency/ohlcv/historical`), latest quotes, and CMC's proprietary **Fear & Greed Index** (`/v3/fear-and-greed`).
- The Fear & Greed Index is a first-class **signal source** (`fgi`) in the strategy DSL — strategies gate entries/exits on sentiment regime.
- Strategies are authored as a **CMC Skill** (`skill/SKILL.md`) — the marketplace-native deliverable format.

### 🛠️ BNB AI Agent SDK
- `darwin/identity/bnb.py`: registers Darwin's verifiable **ERC-8004 on-chain identity** on BSC testnet via the official `bnbagent` SDK (gas-sponsored).
- **Live on-chain proof:** agentId `1467`, registry `0x8004A818BFB912233c491871b3d84c89A494BD9e` —
  [tx on BSC testnet](https://testnet.bscscan.com/tx/0x8f3c609817ab889d7160d3b4583e4d757bae873456b885d219cf3163ed8fdc7a).

### 🔐 Trust Wallet Agent Kit
- `darwin/execute/twak_gateway.py`: a **live HMAC-authenticated** client for the TWAK API gateway (`tws.trustwallet.com`). It signs requests correctly (RFC-2822 date, sorted-query `METHOD;PATH;QUERY;ACCESS_ID;NONCE;DATE`), resolves BSC assets live via `/v1/search/assets`, and structures PancakeSwap route requests (`/amber-api/v1/route`).
- *Status:* auth + live BSC asset resolution work with portal credentials; the swap-route computation currently returns a server-side error on the free portal tier, so `execute` shows a dry-run plan. The "Best Use of TWAK" prize is Track-1-scoped (live autonomous execution), so here TWAK is a supporting integration rather than the focus.

## Repo layout

```
darwin/
  strategy/   spec DSL, indicators (incl. MACD), backtester, metrics
  cmc/        CoinMarketCap client (OHLCV, quotes, Fear & Greed)
  evolve/     seeds, deterministic GA operators, LLM operators, engine
  execute/    TWAK gateway + execution adapter
  identity/   BNB ERC-8004 on-chain identity
  report.py   readable run reports
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
