"""Darwin — an evolutionary trading-strategy foundry for BNB Chain.

Pulls CoinMarketCap data, breeds a population of backtestable strategy specs
with Claude, scores them on a risk-adjusted / drawdown / rule-adherence rubric,
and evolves the survivors into a champion spec that can be executed on BSC via
the Trust Wallet Agent Kit and registered on-chain via the BNB AI Agent SDK.
"""

__version__ = "0.1.0"
