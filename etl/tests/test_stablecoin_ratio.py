"""Tests for ``calculate_stablecoin_ratio`` and its wiring into the
``calculate_diversification_score`` sub-components.

Behavior under test:
- ``calculate_stablecoin_ratio(positions)`` returns a float in ``[0.0, 1.0]``
  representing the share of portfolio value held in known stablecoins
  (USDT/USDC/DAI/BUSD/TUSD/USDP/FEI/FRAX/LUSD/sUSD).
- When every active position carries a numeric ``usd_value > 0``, the ratio
  is value-weighted using ``usd_value``.
- Otherwise (the current production reality, where pricing is not yet wired
  in), the ratio falls back to a token-balance-share weighting using the
  raw ``tokenBalance`` field. This is deterministic and well-defined for
  same-asset comparisons, and degrades gracefully without USD prices.
- Positions with zero or missing balance are ignored.
- Empty input returns 0.0 (no exposure when there is no portfolio).
- Contract addresses are matched case-insensitively against ``STABLECOINS``.

The wiring tests assert that ``calculate_diversification_score`` exposes the
new ratio via its returned metrics dict and keeps the score within
``[0.0, 1.0]`` after adding the sub-component.
"""
from __future__ import annotations

import pytest

from wallet_etl.pipeline.daily_job import (
    STABLECOINS,
    calculate_diversification_score,
    calculate_stablecoin_ratio,
)


# Pull a few real stablecoin addresses out of the canonical set so the tests
# break loudly if the constant is renamed or its membership shifts.
USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
USDT = "0xdac17f958d2ee523a2206206994597c13d831ec7"
DAI = "0x6b175474e89094c44da98b954eedeac495271d0f"
WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"  # not a stablecoin
LINK = "0x514910771af9ca656af840dff83e8264ecf986ca"  # not a stablecoin


def _pos(contract: str, balance: int | str = 1, usd_value: float | None = None) -> dict:
    """Build a position dict in the shape used by the daily ETL."""
    p: dict = {"contractAddress": contract, "tokenBalance": balance}
    if usd_value is not None:
        p["usd_value"] = usd_value
    return p


# ---------------------------------------------------------------------------
# Sanity: known stablecoin addresses are still part of the canonical set.
# Acts as a contract test guarding against accidental drift.
# ---------------------------------------------------------------------------


def test_canonical_stablecoin_addresses_present() -> None:
    assert USDC in STABLECOINS
    assert USDT in STABLECOINS
    assert DAI in STABLECOINS


# ---------------------------------------------------------------------------
# calculate_stablecoin_ratio — required cases from the brief
# ---------------------------------------------------------------------------


def test_empty_positions_returns_zero() -> None:
    assert calculate_stablecoin_ratio([]) == 0.0


def test_all_stablecoin_returns_one() -> None:
    positions = [_pos(USDC, balance=100), _pos(USDT, balance=50), _pos(DAI, balance=25)]
    assert calculate_stablecoin_ratio(positions) == 1.0


def test_no_stablecoin_returns_zero() -> None:
    positions = [_pos(WETH, balance=10), _pos(LINK, balance=20)]
    assert calculate_stablecoin_ratio(positions) == 0.0


def test_mixed_falls_back_to_balance_share_when_no_usd_values() -> None:
    # 100 USDC stable + 100 WETH non-stable, no usd_value supplied.
    # Fallback weighting is a balance-share, so equal raw balances => 0.5.
    positions = [_pos(USDC, balance=100), _pos(WETH, balance=100)]
    assert calculate_stablecoin_ratio(positions) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Edge cases that defend the documented behavior contract.
# ---------------------------------------------------------------------------


def test_usd_value_weighting_when_all_positions_priced() -> None:
    # 1000 USD of USDC + 9000 USD of WETH => 10% stablecoin exposure by value.
    positions = [
        _pos(USDC, balance=1000, usd_value=1000.0),
        _pos(WETH, balance=4, usd_value=9000.0),
    ]
    assert calculate_stablecoin_ratio(positions) == pytest.approx(0.1)


def test_partial_usd_values_falls_back_to_balance_share() -> None:
    # If even one active position is missing usd_value, the function must
    # NOT mix-and-match (which would silently double-count). It falls back
    # to balance-share weighting consistently.
    positions = [
        _pos(USDC, balance=100, usd_value=100.0),
        _pos(WETH, balance=100),  # missing usd_value
    ]
    # Balance-share path: 100 / (100 + 100) = 0.5
    assert calculate_stablecoin_ratio(positions) == pytest.approx(0.5)


def test_zero_balance_positions_are_ignored() -> None:
    # A 0-balance USDC position should not count as "exposure".
    positions = [_pos(USDC, balance=0), _pos(WETH, balance=10)]
    assert calculate_stablecoin_ratio(positions) == 0.0


def test_missing_balance_positions_are_ignored() -> None:
    positions = [{"contractAddress": USDC}, _pos(WETH, balance=10)]
    assert calculate_stablecoin_ratio(positions) == 0.0


def test_uppercase_contract_addresses_are_normalized() -> None:
    positions = [_pos(USDC.upper(), balance=100), _pos(WETH, balance=100)]
    assert calculate_stablecoin_ratio(positions) == pytest.approx(0.5)


def test_hex_string_balances_are_parsed() -> None:
    # 0x64 == 100 decimal. Both positions have equal balance => 0.5.
    positions = [_pos(USDC, balance="0x64"), _pos(WETH, balance="0x64")]
    assert calculate_stablecoin_ratio(positions) == pytest.approx(0.5)


def test_only_zero_usd_values_falls_back_to_balance_share() -> None:
    # All positions priced at 0 is not a meaningful signal; we treat it the
    # same as missing pricing and fall back to balance-share weighting so the
    # function never returns NaN or divides by zero.
    positions = [
        _pos(USDC, balance=100, usd_value=0.0),
        _pos(WETH, balance=300, usd_value=0.0),
    ]
    assert calculate_stablecoin_ratio(positions) == pytest.approx(0.25)


def test_result_is_always_within_unit_interval() -> None:
    # Property-ish: across a few representative shapes, the result must
    # never escape [0, 1].
    cases: list[list[dict]] = [
        [],
        [_pos(USDC, balance=1)],
        [_pos(WETH, balance=1)],
        [_pos(USDC, balance=1), _pos(WETH, balance=1)],
        [_pos(USDC, balance=1, usd_value=10.0), _pos(WETH, balance=1, usd_value=90.0)],
    ]
    for positions in cases:
        ratio = calculate_stablecoin_ratio(positions)
        assert 0.0 <= ratio <= 1.0, f"ratio out of range for {positions!r}: {ratio}"


# ---------------------------------------------------------------------------
# Wiring tests: calculate_diversification_score must surface the new metric
# and remain a valid 0-1 score after adding the sub-component.
# ---------------------------------------------------------------------------


def test_diversification_metrics_include_stablecoin_exposure_ratio() -> None:
    positions = [_pos(USDC, balance=100), _pos(WETH, balance=100), _pos(LINK, balance=100)]
    _, metrics = calculate_diversification_score(positions)
    assert "stablecoin_exposure_ratio" in metrics
    # Three equal-balance positions, one stablecoin => ~1/3.
    assert metrics["stablecoin_exposure_ratio"] == pytest.approx(1 / 3, abs=1e-3)


def test_diversification_score_remains_within_unit_interval() -> None:
    portfolios: list[list[dict]] = [
        [],
        [_pos(USDC, balance=100)],
        [_pos(USDC, balance=100), _pos(USDT, balance=100), _pos(DAI, balance=100)],
        [_pos(WETH, balance=1) for _ in range(15)],
        [_pos(USDC, balance=30), _pos(WETH, balance=70)],
    ]
    for positions in portfolios:
        score, _ = calculate_diversification_score(positions)
        assert 0.0 <= score <= 1.0, f"score out of range for {positions!r}: {score}"


def test_diversification_unique_token_metric_unchanged() -> None:
    # Pre-existing metric must keep working — guards against regression in
    # the wiring change.
    positions = [_pos(USDC, balance=100), _pos(WETH, balance=100), _pos(LINK, balance=0)]
    _, metrics = calculate_diversification_score(positions)
    assert metrics["unique_tokens"] == 2  # LINK has zero balance, excluded
