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

    def _request(self, method: str, path: str, *, params: dict[str, Any] | None = None) -> Any:
        if not self.api_key:
            raise RuntimeError("Missing Alchemy API key. Set ALCHEMY_API_KEY before running ETL jobs.")

        url = f"{self.base_url}/{self.api_key}/{path}"
        response = self.session.request(method, url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def fetch_transactions(self, address: str, *, page_size: int = 100) -> list[dict[str, Any]]:
        """Fetch recent transactions for a wallet. Placeholder implementation."""
        logger.info("Fetching transactions for address=%s via Alchemy (stub)", address)
        # TODO: Implement real pagination logic using Alchemy Transfers API.
        _ = page_size  # keep signature stable until implemented
        return []
