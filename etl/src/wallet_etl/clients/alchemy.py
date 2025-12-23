"""Thin wrapper around the Alchemy API.

Only the interface is implemented for now so downstream pipeline code can
stabilise while we add real API integration in later iterations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import logging
import requests

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AlchemyClient:
    api_key: str
    session: requests.Session = field(default_factory=requests.Session)

    base_url: str = "https://eth-mainnet.g.alchemy.com/v2"


    def _json_rpc_request(self, method: str, params: list[Any]) -> dict[str, Any]:
        url = f"{self.base_url}/{self.api_key}"
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        response = self.session.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()

    def fetch_transactions(self, address: str, from_block: str = "0x0") -> list[dict[str, Any]]:
        """Fetch all transactions for a wallet using alchemy_getAssetTransfers.
        
        Args:
            address: Wallet address to fetch transactions for
            from_block: Starting block in hex (default "0x0" for all history)
        """
        logger.info("Fetching transactions for address=%s from block=%s via Alchemy", address, from_block)
        all_transactions = []
        page_key = None
        while True:
            params = [
                {
                    "fromBlock": from_block,
                    "toBlock": "latest",
                    "fromAddress": address.lower(),
                    "category": ["external", "internal", "erc20", "erc721", "erc1155"],
                    "withMetadata": True,
                    "excludeZeroValue": False,
                    "maxCount": "0x3e8",  # 1000 in hex
                }
            ]
            if page_key:
                params[0]["pageKey"] = page_key

            response = self._json_rpc_request("alchemy_getAssetTransfers", params)
            if "error" in response:
                raise RuntimeError(f"Alchemy API error: {response['error']['message']}")

            transactions = response.get("result", {}).get("transfers", [])
            all_transactions.extend(transactions)

            page_key = response.get("result", {}).get("pageKey")
            if not page_key:
                break
        logger.info("Found %d transactions for address %s", len(all_transactions), address)
        return all_transactions

    def fetch_token_balances(self, address: str) -> list[dict[str, Any]]:
        """Fetch token balances for a wallet."""
        logger.info("Fetching token balances for address=%s via Alchemy", address)
        response = self._json_rpc_request("alchemy_getTokenBalances", [address, "erc20"])
        if "error" in response:
            raise RuntimeError(f"Alchemy API error: {response['error']['message']}")

        balances = response.get("result", {}).get("tokenBalances", [])
        logger.info("Found %d token balances for address %s", len(balances), address)
        return balances
