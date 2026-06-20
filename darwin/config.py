"""Central configuration. Loads from .env (never hardcode secrets)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data" / "cache"
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
for _d in (DATA_DIR, REPORTS_DIR, RUNS_DIR):
    _d.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    # Optional custom endpoint for an Anthropic-compatible gateway (e.g. DGRID).
    anthropic_base_url: str = os.getenv("ANTHROPIC_BASE_URL", "")
    model: str = os.getenv("DARWIN_MODEL", "claude-sonnet-4-6")
    cmc_api_key: str = os.getenv("CMC_PRO_API_KEY", "")
    bsc_private_key: str = os.getenv("BSC_PRIVATE_KEY", "")
    bsc_rpc_url: str = os.getenv("BSC_RPC_URL", "https://data-seed-prebsc-1-s1.bnbchain.org:8545")
    bsc_chain_id: int = int(os.getenv("BSC_CHAIN_ID", "97") or "97")
    # Local encrypted-keystore password for the BNB Agent SDK wallet provider.
    wallet_password: str = os.getenv("WALLET_PASSWORD", "darwin-testnet")
    # Trust Wallet portal API gateway credentials (portal.trustwallet.com).
    twak_access_id: str = os.getenv("TWAK_ACCESS_ID", "")
    twak_hmac_secret: str = os.getenv("TWAK_HMAC_SECRET", "")

    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def has_cmc(self) -> bool:
        return bool(self.cmc_api_key)

    @property
    def has_wallet(self) -> bool:
        return bool(self.bsc_private_key)


settings = Settings()
