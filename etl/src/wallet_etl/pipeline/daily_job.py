"""Main entrypoint for the daily wallet ETL pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

import logging

from wallet_etl.clients.alchemy import AlchemyClient
from wallet_etl.config import settings
from wallet_etl.storage.minio_store import MinioStore
from wallet_etl.storage.postgres_store import PostgresStore

logger = logging.getLogger(__name__)


def _coerce_timestamp(value) -> datetime:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    value_str = str(value)
    if value_str.endswith("Z"):
        value_str = value_str.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(value_str)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def calculate_scores(address: str, *, transactions: list[dict], positions: list[dict]) -> dict:
    """Placeholder scoring logic until metrics are implemented."""
    logger.info("Calculating placeholder scores for %s", address)
    totals = {
        "activity_score": 0.0,
        "diversification_score": 0.0,
        "risk_score": 0.0,
        "profitability_score": 0.0,
        "stability_score": 0.0,
    }
    totals["total_score"] = sum(totals.values()) / 5 if totals else 0.0
    totals["metrics"] = {
        "transactions_count": len(transactions),
        "positions_count": len(positions),
    }
    return totals


def run_wallet_pipeline(addresses: Iterable[str]) -> None:
    address_list = list(addresses)
    logger.info("Running wallet ETL pipeline for %d addresses", len(address_list))

    alchemy = AlchemyClient(api_key=settings.alchemy_api_key)
    minio_store = MinioStore(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket=settings.minio_bucket,
    )
    pg_store = PostgresStore(settings.database_url)

    minio_store.ensure_bucket()

    for address in address_list:
        logger.info("Processing address %s", address)
        transactions = alchemy.fetch_transactions(address)
        positions: list[dict] = []

        raw_key_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
        minio_store.put_json(f"{raw_key_prefix}/transactions/{address}.json", transactions)
        minio_store.put_json(f"{raw_key_prefix}/positions/{address}.json", positions)

        now = datetime.now(timezone.utc)
        pg_store.upsert_wallets(
            [
                {
                    "address": address,
                    "chain": "eth_mainnet",
                    "first_seen": now,
                    "last_seen": now,
                    "tags": [],
                }
            ]
        )

        tx_rows = []
        for tx in transactions:
            tx_hash = tx.get("hash")
            ts_value = tx.get("timestamp")
            if not tx_hash or ts_value is None:
                continue
            ts = _coerce_timestamp(ts_value)
            tx_rows.append(
                {
                    "hash": tx_hash,
                    "address": address,
                    "block_number": tx.get("blockNumber"),
                    "timestamp": ts,
                    "gas_spent_usd": tx.get("gasUsedUSD"),
                    "tx_type": tx.get("category"),
                    "contracts_involved": tx.get("rawContract", {}).get("addresses", []),
                    "raw_payload": tx,
                }
            )
        pg_store.insert_transactions(tx_rows)

        position_rows = []
        for pos in positions:
            token = pos.get("contract_address")
            if not token:
                continue
            position_rows.append(
                {
                    "address": address,
                    "token": token,
                    "protocol": pos.get("protocol_name"),
                    "balance": pos.get("balance"),
                    "usd_value": pos.get("quote"),
                    "last_updated": now,
                    "raw_payload": pos,
                }
            )
        pg_store.upsert_positions(position_rows)

        scores = calculate_scores(address, transactions=transactions, positions=positions)
        pg_store.upsert_features_daily(
            [
                {
                    "address": address,
                    "date": now.date(),
                    "activity_score": scores["activity_score"],
                    "diversification_score": scores["diversification_score"],
                    "risk_score": scores["risk_score"],
                    "profitability_score": scores["profitability_score"],
                    "stability_score": scores["stability_score"],
                    "total_score": scores["total_score"],
                    "metrics": scores["metrics"],
                }
            ]
        )

    logger.info("Wallet ETL pipeline completed")


def main() -> None:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Run wallet ETL pipeline for provided addresses.")
    parser.add_argument("--address", action="append", dest="addresses", help="Wallet address to process", default=[])
    args = parser.parse_args()

    addresses = args.addresses
    if not addresses:
        print("No addresses supplied. Use --address 0x123... to target wallets.", file=sys.stderr)
        sys.exit(1)

    run_wallet_pipeline(addresses)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    main()
