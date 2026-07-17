"""Tests for order-independent first/last transfer timestamps.

Alchemy returns transfers in ascending order by default. The old pipeline
indexed ``transactions[0]`` as newest and ``[-1]`` as oldest, which inverted
wallet age and first_seen/last_seen whenever order was ascending. These tests
lock min/max semantics so list position cannot silently break scoring.
"""
from __future__ import annotations

from datetime import datetime, timezone

from wallet_etl.pipeline.daily_job import (
    _transaction_timestamp_bounds,
    calculate_stability_score,
)


def _tx(ts: str) -> dict:
    return {"metadata": {"blockTimestamp": ts}, "category": "external", "value": 0}


ASC_OLD = "2020-01-01T00:00:00Z"
ASC_MID = "2022-06-15T12:00:00Z"
ASC_NEW = "2024-12-01T00:00:00Z"


def test_bounds_asc_order_earliest_is_first_element():
    txs = [_tx(ASC_OLD), _tx(ASC_MID), _tx(ASC_NEW)]
    earliest, latest = _transaction_timestamp_bounds(txs)
    assert earliest == datetime(2020, 1, 1, tzinfo=timezone.utc)
    assert latest == datetime(2024, 12, 1, tzinfo=timezone.utc)


def test_bounds_desc_order_same_result():
    txs = [_tx(ASC_NEW), _tx(ASC_MID), _tx(ASC_OLD)]
    earliest, latest = _transaction_timestamp_bounds(txs)
    assert earliest == datetime(2020, 1, 1, tzinfo=timezone.utc)
    assert latest == datetime(2024, 12, 1, tzinfo=timezone.utc)


def test_bounds_empty_and_missing_metadata():
    assert _transaction_timestamp_bounds([]) == (None, None)
    assert _transaction_timestamp_bounds([{"metadata": {}}]) == (None, None)
    assert _transaction_timestamp_bounds([{}]) == (None, None)


def test_stability_wallet_age_uses_earliest_not_list_end():
    """With asc order, indexing [-1] would yield age ≈ 0; min must yield multi-year age."""
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    txs = [_tx(ASC_OLD), _tx(ASC_NEW)]
    _, metrics = calculate_stability_score(txs, positions=[], now=now)
    # 2020-01-01 → 2025-01-01 ≈ 1826 days
    assert metrics["wallet_age_days"] >= 1800
