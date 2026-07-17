"""Tests for Ethereum address-format validation on POST /extract/{address}.

NOTE: The validator (`_is_valid_eth_address`) and its call site already exist
in `api/app/main.py`. These tests are characterization tests that lock in the
existing behavior so future changes can't silently relax the validation.

The validation rule under test:
- Address must match the regex `^0x[a-fA-F0-9]{40}$`.
- Anything else must be rejected with HTTP 400 BEFORE any database access.
"""
from __future__ import annotations

from typing import Iterator
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from app.main import _is_valid_eth_address, app, pg_store


# Vitalik's well-known address, used purely as a known-good 0x-prefixed
# 40-hex-char string. Not used to make any network or DB call.
VALID_LOWER = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"
VALID_MIXED = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
VALID_UPPER_HEX = "0xD8DA6BF26964AF9D7EED9E03E53415D37AA96045"


# ---------------------------------------------------------------------------
# Unit tests on the validator helper
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "address",
    [
        VALID_LOWER,
        VALID_MIXED,
        VALID_UPPER_HEX,
        "0x" + "0" * 40,
        "0x" + "f" * 40,
        "0x" + "F" * 40,
        "0x" + "a1B2c3D4e5" * 4,
    ],
)
def test_validator_accepts_well_formed_addresses(address: str) -> None:
    assert _is_valid_eth_address(address) is True


@pytest.mark.parametrize(
    "address,reason",
    [
        ("", "empty string"),
        ("0x", "prefix only"),
        ("0x" + "a" * 39, "one char too short"),
        ("0x" + "a" * 41, "one char too long"),
        ("0x" + "g" * 40, "non-hex character g"),
        ("0x" + "z" * 40, "non-hex character z"),
        ("0x" + "G" * 40, "non-hex uppercase G"),
        ("a" * 40, "missing 0x prefix"),
        ("0X" + "a" * 40, "uppercase X in prefix"),
        ("1x" + "a" * 40, "wrong prefix digit"),
        (" 0x" + "a" * 40, "leading whitespace"),
        ("0x" + "a" * 40 + " ", "trailing whitespace"),
        ("0x" + "a" * 40 + "\n", "trailing newline"),
        ("0x" + "a" * 40 + "x", "extra trailing char"),
        ("0x" + "a" * 38 + "ZZ", "non-hex at end"),
        ("0x' OR '1'='1' --" + "a" * 24, "sql-injection-shaped string"),
        ("0x../../../etc/passwd" + "a" * 19, "path-traversal-shaped string"),
        ("not-an-address", "free text"),
        ("0x" + "0" * 39 + "Ω", "non-ascii unicode"),
    ],
)
def test_validator_rejects_malformed_addresses(address: str, reason: str) -> None:
    assert _is_valid_eth_address(address) is False, f"should reject: {reason}"


# ---------------------------------------------------------------------------
# Integration tests on POST /extract/{address}
# ---------------------------------------------------------------------------


class _RecordingStore:
    """Stand-in for pg_store that records calls and never touches a DB.

    If the validator works correctly, none of these methods should be invoked
    for malformed inputs.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []

    def get_latest_extraction_job(self, address: str):
        self.calls.append(("get_latest_extraction_job", (address,)))
        return None

    def create_extraction_job(self, address: str) -> dict:
        self.calls.append(("create_extraction_job", (address,)))
        return {
            "id": "00000000-0000-0000-0000-000000000000",
            "address": address,
            "status": "pending",
            "error_message": None,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }

    def update_extraction_job(self, *args, **kwargs) -> None:
        self.calls.append(("update_extraction_job", args))

    def ensure_extraction_jobs_table(self) -> None:
        self.calls.append(("ensure_extraction_jobs_table", ()))


@pytest.fixture
def recording_store(monkeypatch: pytest.MonkeyPatch) -> _RecordingStore:
    """Replace the module-level pg_store with a recording stub.

    Also stub the background ETL launcher so a "valid" address request doesn't
    spawn a real worker thread.
    """
    store = _RecordingStore()
    monkeypatch.setattr("app.main.pg_store", store)
    monkeypatch.setattr("app.main._run_etl_background", lambda job_id, address: None)
    return store


@pytest.fixture
def client(recording_store: _RecordingStore) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


# Inputs the FastAPI router can deliver as the {address} path segment without
# colliding with route boundaries (i.e. no leading/trailing whitespace inside
# the path; no '/'). These are URL-encoded where the raw value would be unsafe.
_REJECTED_PATH_INPUTS = [
    pytest.param("0x" + "a" * 39, id="too-short-by-one"),
    pytest.param("0x" + "a" * 41, id="too-long-by-one"),
    pytest.param("0x" + "g" * 40, id="non-hex-g"),
    pytest.param("0x" + "Z" * 40, id="non-hex-Z"),
    pytest.param("a" * 40, id="missing-0x-prefix"),
    pytest.param("0X" + "a" * 40, id="uppercase-X-prefix"),
    pytest.param("0x" + "a" * 40 + "x", id="extra-trailing-char"),
    pytest.param("not-an-address", id="free-text"),
    pytest.param(quote("0x' OR '1'='1' --" + "a" * 24, safe=""), id="sql-injection-shaped"),
    pytest.param(quote("0x" + "0" * 39 + "Ω", safe=""), id="non-ascii"),
]


@pytest.mark.parametrize("address_path", _REJECTED_PATH_INPUTS)
def test_post_extract_rejects_malformed_address_with_400(
    client: TestClient, recording_store: _RecordingStore, address_path: str
) -> None:
    response = client.post(f"/extract/{address_path}")

    assert response.status_code == 400, response.text
    body = response.json()
    assert body == {"detail": "Invalid Ethereum address format."}

    # Validation MUST short-circuit before any DB access.
    db_methods_invoked = [
        name for (name, _args) in recording_store.calls
        if name in {"get_latest_extraction_job", "create_extraction_job", "update_extraction_job"}
    ]
    assert db_methods_invoked == [], (
        f"DB methods should not be called for invalid input, got: {db_methods_invoked}"
    )


def test_post_extract_accepts_valid_lowercase_address(
    client: TestClient, recording_store: _RecordingStore
) -> None:
    response = client.post(f"/extract/{VALID_LOWER}")

    assert response.status_code == 202, response.text
    body = response.json()
    assert body["address"] == VALID_LOWER
    assert body["status"] == "pending"
    # Proves the request reached the DB layer (i.e. validation passed).
    assert ("create_extraction_job", (VALID_LOWER,)) in recording_store.calls


def test_post_extract_accepts_valid_mixed_case_address(
    client: TestClient, recording_store: _RecordingStore
) -> None:
    response = client.post(f"/extract/{VALID_MIXED}")

    assert response.status_code == 202, response.text
    body = response.json()
    assert body["address"] == VALID_MIXED
    assert ("create_extraction_job", (VALID_MIXED,)) in recording_store.calls
