"""Wrapper around Covalent API endpoints we rely on for balances/pricing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import logging
import requests

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CovalentClient:
    api_key: str
    chain_id: str
    session: requests.Session = field(default_factory=requests.Session)

    base_url: str = "https://api.covalenthq.com/v1"

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        if not self.api_key:
            raise RuntimeError("Missing Covalent API key. Set COVALENT_API_KEY before running ETL jobs.")

        if params is None:
            params = {}
        params["key"] = self.api_key

        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.request(method, url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def fetch_token_balances(self, address: str) -> list[dict[str, Any]]:
        """Fetch token balances for an address. Placeholder until full integration."""
        logger.info(
            "Fetching token balances for address=%s chain=%s via Covalent (stub)",
            address,
            self.chain_id,
        )
        return []
