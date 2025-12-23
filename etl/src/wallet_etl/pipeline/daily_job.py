"""Main entrypoint for the daily wallet ETL pipeline."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
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
    """Calculate wallet health scores based on transactions and positions."""
    logger.info("Calculating scores for %s", address)

    # Activity Score (based on recent transactions)
    now = datetime.now(timezone.utc)
    recent_tx = [
        tx
        for tx in transactions
        if _coerce_timestamp(tx["metadata"]["blockTimestamp"]) > now - timedelta(days=30)
    ]
    activity_score = min(len(recent_tx) / 10.0, 1.0)  # Normalize: 10+ tx in 30d = max score

    # Diversification Score (based on number of tokens)
    num_tokens = len([p for p in positions if int(p.get("tokenBalance", 0)) > 0])
    diversification_score = min(num_tokens / 10.0, 1.0)  # Normalize: 10+ tokens = max score

    # Placeholder scores
    risk_score = 0.5
    profitability_score = 0.5
    stability_score = 0.5

    scores = {
        "activity_score": activity_score,
        "diversification_score": diversification_score,
        "risk_score": risk_score,
        "profitability_score": profitability_score,
        "stability_score": stability_score,
    }

    # Weighted average
    weights = {
        "activity_score": 0.2,
        "diversification_score": 0.2,
        "risk_score": 0.2,
        "profitability_score": 0.2,
        "stability_score": 0.2,
    }
    total_score = sum(scores[k] * weights[k] for k in scores)

    return {
        **scores,
        "total_score": total_score,
        "metrics": {
            "transactions_count": len(transactions),
            "recent_transactions_count": len(recent_tx),
            "positions_count": num_tokens,
        },
    }


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
        positions = alchemy.fetch_token_balances(address)

        raw_key_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
        minio_store.put_json(f"{raw_key_prefix}/transactions/{address}.json", transactions)
        minio_store.put_json(f"{raw_key_prefix}/positions/{address}.json", positions)

        now = datetime.now(timezone.utc)
        if transactions:
            first_tx_ts = _coerce_timestamp(transactions[-1]["metadata"]["blockTimestamp"])
            last_tx_ts = _coerce_timestamp(transactions[0]["metadata"]["blockTimestamp"])
        else:
            first_tx_ts = last_tx_ts = now

        pg_store.upsert_wallets(
            [
                {
                    "address": address,
                    "chain": "eth_mainnet",
                    "first_seen": first_tx_ts,
                    "last_seen": last_tx_ts,
                    "tags": [],
                }
            ]
        )

        tx_rows = []
        for tx in transactions:
            tx_hash = tx.get("hash")
            ts_value = tx.get("metadata", {}).get("blockTimestamp")
            if not tx_hash or ts_value is None:
                continue
            ts = _coerce_timestamp(ts_value)
            tx_rows.append(
                {
                    "hash": tx_hash,
                    "address": address,
                    "block_number": int(tx.get("blockNum"), 16) if tx.get("blockNum") else None,
                    "timestamp": ts,
                    "gas_spent_usd": tx.get("metadata", {}).get("gasUsedUSD"),
                    "tx_type": tx.get("category"),
                    "contracts_involved": [tx.get("rawContract", {}).get("address")],
                    "raw_payload": tx,
                }
            )
        pg_store.insert_transactions(tx_rows)

        position_rows = []
        for pos in positions:
            token = pos.get("contractAddress")
            if not token:
                continue
            balance_int = int(pos.get("tokenBalance"), 16) if pos.get("tokenBalance") else 0
            position_rows.append(
                {
                    "address": address,
                    "token": token,
                    "protocol": None,  # Not available from this endpoint
                    "balance": balance_int,
                    "usd_value": None,  # Requires separate pricing call
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
