"""Tests for weekly activity aggregation helpers and GET /activity/{address}."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import (
    _build_weekly_activity_series,
    _clamp_weeks,
    _monday_on_or_before,
    _weekly_activity_score,
    app,
    pg_store,
)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_clamp_weeks_bounds():
    assert _clamp_weeks(0) == 1
    assert _clamp_weeks(-5) == 1
    assert _clamp_weeks(52) == 52
    assert _clamp_weeks(104) == 104
    assert _clamp_weeks(200) == 104


def test_monday_on_or_before():
    # 2026-07-16 is a Thursday → Monday is 2026-07-13
    assert _monday_on_or_before(date(2026, 7, 16)) == date(2026, 7, 13)
    assert _monday_on_or_before(date(2026, 7, 13)) == date(2026, 7, 13)


def test_weekly_activity_score_matches_activity_limb():
    assert _weekly_activity_score(0) == 0.0
    assert _weekly_activity_score(5) == 0.5
    assert _weekly_activity_score(10) == 1.0
    assert _weekly_activity_score(50) == 1.0


def test_build_series_zero_fills_missing_weeks():
    as_of = date(2026, 7, 16)  # Thursday → end Monday 2026-07-13
    counts = {
        date(2026, 7, 6): 3,  # prior Monday
        date(2026, 7, 13): 12,
    }
    series = _build_weekly_activity_series(counts, weeks=4, as_of=as_of)

    assert len(series) == 4
    assert [p["week_start"] for p in series] == [
        "2026-06-22",
        "2026-06-29",
        "2026-07-06",
        "2026-07-13",
    ]
    assert series[0]["tx_count"] == 0
    assert series[0]["activity_score"] == 0.0
    assert series[1]["tx_count"] == 0
    assert series[2]["tx_count"] == 3
    assert series[2]["activity_score"] == 0.3
    assert series[3]["tx_count"] == 12
    assert series[3]["activity_score"] == 1.0
    # week_end is Sunday
    assert series[3]["week_end"] == "2026-07-19"


def test_build_series_empty_counts_all_zeros():
    series = _build_weekly_activity_series({}, weeks=3, as_of=date(2026, 7, 13))
    assert len(series) == 3
    assert all(p["tx_count"] == 0 for p in series)
    assert all(p["activity_score"] == 0.0 for p in series)


# ---------------------------------------------------------------------------
# Endpoint (DB mocked)
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


def test_activity_endpoint_404_when_wallet_missing(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(pg_store, "wallet_exists", lambda _addr: False)
    resp = client.get("/activity/0xd8da6bf26964af9d7eed9e03e53415d37aa96045?weeks=4")
    assert resp.status_code == 404


def test_activity_endpoint_clamps_and_returns_counts(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(pg_store, "wallet_exists", lambda _addr: True)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 7, 16, 12, 0, 0, tzinfo=timezone.utc)

    monkeypatch.setattr("app.main.datetime", FixedDateTime)

    captured: dict = {}

    def fake_counts(address: str, since: date) -> dict[date, int]:
        captured["since"] = since
        captured["address"] = address
        return {date(2026, 7, 13): 7}

    monkeypatch.setattr(pg_store, "get_weekly_tx_counts", fake_counts)

    resp = client.get("/activity/0x1111111111111111111111111111111111111111?weeks=999")
    assert resp.status_code == 200
    body = resp.json()
    assert body["weeks"] == 104
    assert len(body["series"]) == 104
    assert body["series"][-1]["week_start"] == "2026-07-13"
    assert body["series"][-1]["tx_count"] == 7
    assert body["series"][-1]["activity_score"] == 0.7
    assert captured["since"] == date(2024, 7, 22)  # end Monday - 103 weeks


def test_activity_endpoint_empty_txs_returns_zero_series(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(pg_store, "wallet_exists", lambda _addr: True)
    monkeypatch.setattr(pg_store, "get_weekly_tx_counts", lambda *_a, **_k: {})

    resp = client.get("/activity/0xd8da6bf26964af9d7eed9e03e53415d37aa96045?weeks=12")
    assert resp.status_code == 200
    body = resp.json()
    assert body["weeks"] == 12
    assert len(body["series"]) == 12
    assert all(p["tx_count"] == 0 for p in body["series"])
