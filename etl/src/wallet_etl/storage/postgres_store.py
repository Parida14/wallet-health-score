"""Helpers for writing normalized data to Postgres."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Mapping

import logging
import psycopg2
from psycopg2.extras import execute_batch

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PostgresStore:
    dsn: str

    def _connect(self):
        return psycopg2.connect(self.dsn)

    def upsert_wallets(self, rows: Iterable[Mapping[str, object]]) -> None:
        rows = list(rows)
        if not rows:
            return

        logger.info("Upserting %d wallet rows", len(rows))
        query = """
            INSERT INTO wallets (address, chain, first_seen, last_seen, tags, updated_at)
            VALUES (%(address)s, %(chain)s, %(first_seen)s, %(last_seen)s, %(tags)s, %(updated_at)s)
            ON CONFLICT (address) DO UPDATE
            SET
                chain = EXCLUDED.chain,
                first_seen = LEAST(COALESCE(wallets.first_seen, EXCLUDED.first_seen), EXCLUDED.first_seen),
                last_seen = GREATEST(COALESCE(wallets.last_seen, EXCLUDED.last_seen), EXCLUDED.last_seen),
                tags = EXCLUDED.tags,
                updated_at = NOW();
        """
        timestamp = datetime.utcnow()
        enriched = [dict(row, updated_at=timestamp) for row in rows]
        with self._connect() as conn, conn.cursor() as cur:
            execute_batch(cur, query, enriched, page_size=100)

    def insert_transactions(self, rows: Iterable[Mapping[str, object]]) -> None:
        rows = list(rows)
        if not rows:
            return
        logger.info("Inserting %d transactions", len(rows))
        query = """
            INSERT INTO transactions (
                hash,
                address,
                block_number,
                timestamp,
                gas_spent_usd,
                tx_type,
                contracts_involved,
                raw_payload
            )
            VALUES (
                %(hash)s,
                %(address)s,
                %(block_number)s,
                %(timestamp)s,
                %(gas_spent_usd)s,
                %(tx_type)s,
                %(contracts_involved)s,
                %(raw_payload)s
            )
            ON CONFLICT (hash) DO NOTHING;
        """
        with self._connect() as conn, conn.cursor() as cur:
            execute_batch(cur, query, rows, page_size=200)

    def upsert_positions(self, rows: Iterable[Mapping[str, object]]) -> None:
        rows = list(rows)
        if not rows:
            return
        logger.info("Upserting %d positions", len(rows))
        query = """
            INSERT INTO positions (
                address,
                token,
                protocol,
                balance,
                usd_value,
                last_updated,
                raw_payload
            )
            VALUES (
                %(address)s,
                %(token)s,
                %(protocol)s,
                %(balance)s,
                %(usd_value)s,
                %(last_updated)s,
                %(raw_payload)s
            )
            ON CONFLICT (address, token, COALESCE(protocol, '')) DO UPDATE
            SET
                balance = EXCLUDED.balance,
                usd_value = EXCLUDED.usd_value,
                last_updated = EXCLUDED.last_updated,
                raw_payload = EXCLUDED.raw_payload;
        """
        with self._connect() as conn, conn.cursor() as cur:
            execute_batch(cur, query, rows, page_size=200)

    def upsert_features_daily(self, rows: Iterable[Mapping[str, object]]) -> None:
        rows = list(rows)
        if not rows:
            return
        logger.info("Upserting %d feature rows", len(rows))
        query = """
            INSERT INTO features_daily (
                address,
                date,
                activity_score,
                diversification_score,
                risk_score,
                profitability_score,
                stability_score,
                total_score,
                metrics
            )
            VALUES (
                %(address)s,
                %(date)s,
                %(activity_score)s,
                %(diversification_score)s,
                %(risk_score)s,
                %(profitability_score)s,
                %(stability_score)s,
                %(total_score)s,
                %(metrics)s
            )
            ON CONFLICT (address, date) DO UPDATE
            SET
                activity_score = EXCLUDED.activity_score,
                diversification_score = EXCLUDED.diversification_score,
                risk_score = EXCLUDED.risk_score,
                profitability_score = EXCLUDED.profitability_score,
                stability_score = EXCLUDED.stability_score,
                total_score = EXCLUDED.total_score,
                metrics = EXCLUDED.metrics;
        """
        with self._connect() as conn, conn.cursor() as cur:
            execute_batch(cur, query, rows, page_size=100)
