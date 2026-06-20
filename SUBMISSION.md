# Submission Checklist — BNB Hack, Track 2

## Targets
- **Track 2 (Strategy Skills)** placement — primary
- **Best Use of CMC Agent Hub** (cross-track special) — OHLCV + Fear & Greed signal + Skill format
- **Best Use of BNB AI Agent SDK** (cross-track special) — ERC-8004 on-chain identity

## Requirements (from the brief)
- [x] **Public repo** — this repository
- [x] **Reproducible** — `requirements.txt`, `.env.example`, `python -m scripts.demo` runs with no keys
- [ ] **Demo link or video** — record using `DEMO.md` (2–3 min)
- [x] **Skill + strategy spec** — `skill/SKILL.md` + `strategies/sample-champion.json`
- [x] **No token launches** — none
- [ ] **Submit on DoraHacks** — paste repo + demo + the blurb below

## Before submitting (your steps)
1. Fill `.env` with `ANTHROPIC_API_KEY`, `CMC_PRO_API_KEY` (and `BSC_PRIVATE_KEY`, TWAK creds for the integrations).
2. Run a **live** champion: `python -m darwin.cli evolve --universe BTC,ETH,BNB,SOL --generations 8`
   — commit the resulting `runs/<id>/report.md` as proof of live results.
3. (Optional, strengthens BNB special) `python -m darwin.cli register` and capture the BSC testnet tx hash.
4. Push to GitHub (public), record the demo, submit on DoraHacks.

## DoraHacks strategy blurb (draft — edit freely)

> **Darwin** is an evolutionary trading-strategy foundry. Instead of prompting an
> LLM once for a strategy, it breeds a *population*: Claude generates candidate
> strategy specs grounded in CoinMarketCap data (OHLCV + the Fear & Greed Index),
> a deterministic, lookahead-free backtester scores each on the judging rubric
> (risk-adjusted return, drawdown, and rule adherence) with PancakeSwap-realistic
> costs, and a genetic algorithm — using both deterministic operators and
> Claude-guided mutation/crossover — evolves the survivors over generations into a
> champion. The champion is a readable, backtestable JSON spec blending RSI, MACD,
> and Fear & Greed into entry/exit rules. It registers its own ERC-8004 on-chain
> identity via the BNB AI Agent SDK and can fetch live PancakeSwap execution routes
> through the Trust Wallet Agent Kit. We deliberately hardened the fitness function
> against reward-hacking (over-trading, compounding flukes, rule-fighting), so the
> strategies it crowns are coherent and risk-respecting — not curve-fit noise.
