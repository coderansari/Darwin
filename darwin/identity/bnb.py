"""Register Darwin's verifiable on-chain identity via the BNB AI Agent SDK.

Uses the official `bnbagent` package (ERC-8004 identity registry) on BSC testnet,
where registration is gas-sponsored. This gives the autonomous Darwin agent a
discoverable, verifiable on-chain identity — the foundation ERC-8004 provides for
agent reputation and agent-to-agent commerce (ERC-8183).

Verified against bnbagent 0.3.6:
  EVMWalletProvider(password, private_key=...)
  ERC8004Agent(wallet_provider, network="bsc-testnet")
    .generate_agent_uri(name, description, endpoints=[AgentEndpoint(...)]) -> uri
    .register_agent(agent_uri, metadata=None) -> {"agentId", "transactionHash", ...}
    .get_local_agent_info(name) -> dict | None
"""
from __future__ import annotations

import json

from ..config import RUNS_DIR, settings

IDENTITY_FILE = RUNS_DIR / "identity.json"
DEFAULT_ENDPOINT = "https://github.com/coderansari/Darwin"


def _build_agent():
    from bnbagent import ERC8004Agent, EVMWalletProvider  # lazy import

    wallet = EVMWalletProvider(
        password=settings.wallet_password,
        private_key=settings.bsc_private_key,
        wallets_dir=str(RUNS_DIR / "wallet"),
    )
    agent = ERC8004Agent(wallet_provider=wallet, network="bsc-testnet")
    return agent


def register_agent(
    name: str = "darwin-foundry",
    description: str = "Darwin evolutionary trading-strategy agent",
    endpoint: str | None = None,
) -> int:
    """Register (or look up) the agent's ERC-8004 identity on BSC testnet."""
    if not settings.has_wallet:
        print("[identity] BSC_PRIVATE_KEY not set - add a funded BSC testnet key to .env")
        return 1

    try:
        from bnbagent import AgentEndpoint
    except ImportError:
        print("[identity] bnbagent not installed — run: pip install bnbagent")
        return 1

    try:
        agent = _build_agent()
        print(f"[identity] agent wallet: {agent.wallet_address}")
        print(f"[identity] ERC-8004 registry: {agent.contract_address}")

        existing = agent.get_local_agent_info(name)
        if existing:
            print(f"[identity] already registered: {json.dumps(existing, default=str)}")
            IDENTITY_FILE.write_text(json.dumps(existing, indent=2, default=str))
            return 0

        endpoints = [
            AgentEndpoint(
                name="darwin",
                endpoint=endpoint or DEFAULT_ENDPOINT,
                version="0.1.0",
                capabilities=["trading-strategy-evolution", "backtesting"],
            )
        ]
        uri = agent.generate_agent_uri(name=name, description=description, endpoints=endpoints)
        print(f"[identity] agent URI: {uri}")
        print("[identity] registering on BSC testnet (gas-sponsored)...")
        result = agent.register_agent(uri)

        print(f"[identity] registered! agentId={result.get('agentId')} "
              f"tx={result.get('transactionHash')}")
        IDENTITY_FILE.write_text(json.dumps(result, indent=2, default=str))
        print(f"[identity] saved -> {IDENTITY_FILE}")
        return 0
    except Exception as e:  # surface, don't crash
        print(f"[identity] registration failed: {type(e).__name__}: {e}")
        return 1


def get_identity(name: str = "darwin-foundry") -> dict | None:
    try:
        return _build_agent().get_local_agent_info(name)
    except Exception as e:
        print(f"[identity] lookup failed: {e}")
        return None
