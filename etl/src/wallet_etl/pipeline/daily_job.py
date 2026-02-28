"""Main entrypoint for the daily wallet ETL pipeline."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable
from collections import Counter

import logging

from wallet_etl.clients.alchemy import AlchemyClient
from wallet_etl.config import settings
from wallet_etl.storage.minio_store import MinioStore
from wallet_etl.storage.postgres_store import PostgresStore

logger = logging.getLogger(__name__)

# Known stablecoin contract addresses (lowercase)
STABLECOINS = {
    "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
    "0x6b175474e89094c44da98b954eedeac495271d0f",  # DAI
    "0x4fabb145d64652a948d72533023f6e7a623c7c53",  # BUSD
    "0x0000000000085d4780b73119b644ae5ecd22b376",  # TUSD
    "0x8e870d67f660d95d5be530380d0ec0bd388289e1",  # USDP
    "0x956f47f50a910163d8bf957cf5846d573e7f87ca",  # FEI
    "0x853d955acef822db058eb8505911ed77f175b99e",  # FRAX
    "0x5f98805a4e8be255a32880fdec7f6728c6568ba0",  # LUSD
    "0x57ab1ec28d129707052df4df418d58a2d46d5f51",  # sUSD
}

# Known high-risk/volatile token indicators
HIGH_RISK_INDICATORS = {"meme", "shib", "doge", "pepe", "floki", "inu", "elon", "moon", "safe"}


def _coerce_timestamp(value) -> datetime:
    """Convert various timestamp formats to datetime."""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    value_str = str(value)
    if value_str.endswith("Z"):
        value_str = value_str.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(value_str)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _parse_balance(val) -> int:
    """Parse token balance from various formats."""
    if val is None:
        return 0
    if isinstance(val, int):
        return val
    val_str = str(val)
    if val_str.startswith("0x"):
        return int(val_str, 16)
    return int(val_str)


def _parse_value(val) -> float:
    """Parse ETH/token value from transaction."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    return 0.0


def calculate_activity_score(transactions: list[dict], now: datetime) -> tuple[float, dict]:
    """
    Calculate activity score based on recent transaction frequency.
    
    Metrics:
    - Recent transactions (last 30 days)
    - Unique contracts interacted with
    - Transaction frequency consistency
    
    Returns: (score 0-1, metrics dict)
    """
    recent_tx = [
        tx for tx in transactions
        if _coerce_timestamp(tx["metadata"]["blockTimestamp"]) > now - timedelta(days=30)
    ]
    
    # Count unique contracts
    contracts = set()
    for tx in recent_tx:
        contract = tx.get("rawContract", {}).get("address")
        if contract:
            contracts.add(contract.lower())
    
    # Calculate sub-scores
    tx_count_score = min(len(recent_tx) / 10.0, 1.0)  # 10+ tx = max
    contract_diversity = min(len(contracts) / 5.0, 1.0)  # 5+ contracts = max
    
    # Weighted combination
    activity_score = (tx_count_score * 0.6) + (contract_diversity * 0.4)
    
    return activity_score, {
        "recent_tx_count": len(recent_tx),
        "unique_contracts_30d": len(contracts),
    }


def calculate_diversification_score(positions: list[dict]) -> tuple[float, dict]:
    """
    Calculate diversification score based on portfolio spread.
    
    Metrics:
    - Number of unique tokens held
    - Balance distribution (Herfindahl index inverse)
    
    Returns: (score 0-1, metrics dict)
    """
    # Filter positions with non-zero balance
    active_positions = [
        p for p in positions 
        if _parse_balance(p.get("tokenBalance", 0)) > 0
    ]
    
    num_tokens = len(active_positions)
    
    # Token count score
    token_count_score = min(num_tokens / 10.0, 1.0)  # 10+ tokens = max
    
    # Calculate concentration (simplified - would need USD values for accurate HHI)
    # For now, just reward having multiple tokens
    concentration_score = min(num_tokens / 20.0, 1.0) if num_tokens > 1 else 0.0
    
    diversification_score = (token_count_score * 0.7) + (concentration_score * 0.3)
    
    return diversification_score, {
        "unique_tokens": num_tokens,
    }


def calculate_risk_score(transactions: list[dict], positions: list[dict], now: datetime) -> tuple[float, dict]:
    """
    Calculate risk score (higher = less risky = healthier).
    
    Metrics:
    - Stablecoin ratio (higher = less risk)
    - Volatile/meme token exposure (lower = less risk)
    - Transaction value volatility
    - Interaction with known risky patterns
    
    Returns: (score 0-1, metrics dict)
    """
    active_positions = [
        p for p in positions 
        if _parse_balance(p.get("tokenBalance", 0)) > 0
    ]
    
    if not active_positions:
        return 0.5, {"stablecoin_ratio": 0, "high_risk_tokens": 0}
    
    # Count stablecoin positions
    stablecoin_count = 0
    high_risk_count = 0
    
    for pos in active_positions:
        contract = pos.get("contractAddress", "").lower()
        
        if contract in STABLECOINS:
            stablecoin_count += 1
        
        # Check for high-risk token indicators in contract address or metadata
        # (In production, you'd check against a proper token registry)
        if any(indicator in contract.lower() for indicator in HIGH_RISK_INDICATORS):
            high_risk_count += 1
    
    total_tokens = len(active_positions)
    stablecoin_ratio = stablecoin_count / total_tokens if total_tokens > 0 else 0
    high_risk_ratio = high_risk_count / total_tokens if total_tokens > 0 else 0
    
    # Analyze transaction patterns for risky behavior
    recent_tx = [
        tx for tx in transactions
        if _coerce_timestamp(tx["metadata"]["blockTimestamp"]) > now - timedelta(days=30)
    ]
    
    # Check for large single transactions (potential rug pulls or panic sells)
    tx_values = [_parse_value(tx.get("value")) for tx in recent_tx]
    large_tx_ratio = 0.0
    if tx_values:
        avg_value = sum(tx_values) / len(tx_values)
        large_txs = sum(1 for v in tx_values if v > avg_value * 10) if avg_value > 0 else 0
        large_tx_ratio = large_txs / len(tx_values) if tx_values else 0
    
    # Calculate risk score (inverted - higher score = less risky)
    # Stablecoins reduce risk, high-risk tokens increase risk
    stablecoin_bonus = stablecoin_ratio * 0.4  # Up to 0.4 points for stablecoins
    risk_penalty = high_risk_ratio * 0.3  # Up to 0.3 penalty for risky tokens
    volatility_penalty = large_tx_ratio * 0.2  # Up to 0.2 penalty for volatile behavior
    
    # Base score of 0.5, adjusted by factors
    risk_score = 0.5 + stablecoin_bonus - risk_penalty - volatility_penalty
    risk_score = max(0.0, min(1.0, risk_score))  # Clamp to 0-1
    
    return risk_score, {
        "stablecoin_ratio": round(stablecoin_ratio, 3),
        "high_risk_tokens": high_risk_count,
        "stablecoin_count": stablecoin_count,
    }


def calculate_profitability_score(transactions: list[dict], now: datetime) -> tuple[float, dict]:
    """
    Calculate profitability score based on transaction patterns.
    
    Note: True PnL calculation requires price data at transaction time.
    This is a simplified heuristic based on observable patterns.
    
    Metrics:
    - Net flow direction (more outgoing ETH = potentially profitable trades)
    - Transaction success rate
    - Value per transaction trend
    
    Returns: (score 0-1, metrics dict)
    """
    if not transactions:
        return 0.5, {"net_flow": 0, "avg_value": 0}
    
    # Analyze recent transactions
    recent_tx = [
        tx for tx in transactions
        if _coerce_timestamp(tx["metadata"]["blockTimestamp"]) > now - timedelta(days=90)
    ]
    
    if not recent_tx:
        return 0.5, {"net_flow": 0, "avg_value": 0}
    
    # Calculate net flow (positive = net receiver, negative = net sender)
    # In a profitable trader's wallet, they often send more than receive
    # (selling tokens for ETH, then sending ETH out)
    total_received = 0.0
    total_sent = 0.0
    
    for tx in recent_tx:
        value = _parse_value(tx.get("value", 0))
        category = tx.get("category", "")
        
        # Determine direction based on transaction type
        if category in ["external", "internal"]:
            # Simplified: assume received if value > 0 for most tx types
            total_received += value
    
    # Calculate metrics
    total_volume = total_received + total_sent
    avg_value = total_volume / len(recent_tx) if recent_tx else 0
    
    # Activity level as proxy for trading (more tx = more active trader)
    activity_level = min(len(recent_tx) / 50.0, 1.0)  # 50+ tx in 90d = very active
    
    # Transaction frequency consistency (regular activity is positive)
    if len(recent_tx) >= 2:
        timestamps = sorted([_coerce_timestamp(tx["metadata"]["blockTimestamp"]) for tx in recent_tx])
        gaps = [(timestamps[i+1] - timestamps[i]).days for i in range(len(timestamps)-1)]
        avg_gap = sum(gaps) / len(gaps) if gaps else 30
        consistency = min(1.0, 7.0 / (avg_gap + 1))  # Weekly activity = good
    else:
        consistency = 0.3
    
    # Profitability score based on activity and consistency
    # (Without price data, we use proxies)
    profitability_score = (activity_level * 0.5) + (consistency * 0.5)
    profitability_score = max(0.0, min(1.0, profitability_score))
    
    return profitability_score, {
        "tx_count_90d": len(recent_tx),
        "avg_tx_value": round(avg_value, 4),
        "activity_consistency": round(consistency, 3),
    }


def calculate_stability_score(transactions: list[dict], positions: list[dict], now: datetime) -> tuple[float, dict]:
    """
    Calculate stability score based on holding behavior.
    
    Metrics:
    - Stablecoin holdings ratio
    - Wallet age (older = more stable)
    - Holding duration patterns
    - Low panic-sell indicators
    
    Returns: (score 0-1, metrics dict)
    """
    active_positions = [
        p for p in positions 
        if _parse_balance(p.get("tokenBalance", 0)) > 0
    ]
    
    # Stablecoin ratio (already calculated but included for stability emphasis)
    stablecoin_count = sum(
        1 for p in active_positions 
        if p.get("contractAddress", "").lower() in STABLECOINS
    )
    stablecoin_ratio = stablecoin_count / len(active_positions) if active_positions else 0
    
    # Wallet age (based on first transaction)
    wallet_age_days = 0
    if transactions:
        try:
            first_tx_time = _coerce_timestamp(transactions[-1]["metadata"]["blockTimestamp"])
            wallet_age_days = (now - first_tx_time).days
        except (KeyError, IndexError):
            wallet_age_days = 0
    
    # Age score: wallets > 2 years are considered mature
    age_score = min(wallet_age_days / 730.0, 1.0)  # 730 days = 2 years
    
    # Analyze holding behavior - look for panic sell patterns
    # (Multiple large sells in short timeframe)
    recent_tx = [
        tx for tx in transactions
        if _coerce_timestamp(tx["metadata"]["blockTimestamp"]) > now - timedelta(days=30)
    ]
    
    # Count sells (simplified: ERC20 transfers out)
    sell_count = sum(
        1 for tx in recent_tx 
        if tx.get("category") in ["erc20", "external"] and _parse_value(tx.get("value", 0)) > 0
    )
    
    # Panic indicator: many sells relative to total activity
    if len(recent_tx) > 0:
        sell_ratio = sell_count / len(recent_tx)
        panic_indicator = 1.0 - min(sell_ratio * 2, 1.0)  # High sells = low score
    else:
        panic_indicator = 0.7  # No activity = neutral
    
    # Combine factors
    stability_score = (
        stablecoin_ratio * 0.3 +  # Stablecoin holdings
        age_score * 0.4 +         # Wallet maturity
        panic_indicator * 0.3     # Holding behavior
    )
    stability_score = max(0.0, min(1.0, stability_score))
    
    return stability_score, {
        "stablecoin_ratio": round(stablecoin_ratio, 3),
        "wallet_age_days": wallet_age_days,
        "recent_sell_count": sell_count,
    }


def calculate_scores(address: str, *, transactions: list[dict], positions: list[dict]) -> dict:
    """
    Calculate comprehensive wallet health scores.
    
    Five components, each scored 0-1:
    - Activity: Transaction frequency and engagement
    - Diversification: Portfolio spread across tokens
    - Risk: Exposure to volatile/risky assets (inverted: higher = safer)
    - Profitability: Trading patterns and gains indicators
    - Stability: Holding behavior and wallet maturity
    
    Total score = weighted average (equal weights of 0.2 each)
    """
    logger.info("Calculating scores for %s", address)
    now = datetime.now(timezone.utc)
    
    # Calculate each component
    activity_score, activity_metrics = calculate_activity_score(transactions, now)
    diversification_score, div_metrics = calculate_diversification_score(positions)
    risk_score, risk_metrics = calculate_risk_score(transactions, positions, now)
    profitability_score, profit_metrics = calculate_profitability_score(transactions, now)
    stability_score, stability_metrics = calculate_stability_score(transactions, positions, now)
    
    scores = {
        "activity_score": round(activity_score, 4),
        "diversification_score": round(diversification_score, 4),
        "risk_score": round(risk_score, 4),
        "profitability_score": round(profitability_score, 4),
        "stability_score": round(stability_score, 4),
    }
    
    # Weighted average (equal weights)
    weights = {
        "activity_score": 0.2,
        "diversification_score": 0.2,
        "risk_score": 0.2,
        "profitability_score": 0.2,
        "stability_score": 0.2,
    }
    total_score = sum(scores[k] * weights[k] for k in scores)
    
    # Combine all metrics
    metrics = {
        "transactions_count": len(transactions),
        "positions_count": div_metrics["unique_tokens"],
        **activity_metrics,
        **div_metrics,
        **risk_metrics,
        **profit_metrics,
        **stability_metrics,
    }
    
    return {
        **scores,
        "total_score": round(total_score, 4),
        "metrics": metrics,
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
