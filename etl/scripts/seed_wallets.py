#!/usr/bin/env python3
"""
Seed script to populate the database with real wallet data.

This script fetches blockchain data for well-known Ethereum addresses
and populates the database with their health scores.

Usage:
    # From the etl directory:
    python -m scripts.seed_wallets

    # Or with specific wallets:
    python -m scripts.seed_wallets --address 0x123... --address 0x456...

    # Quick mode (fewer wallets for faster testing):
    python -m scripts.seed_wallets --quick

Requirements:
    - Docker services running (postgres, minio)
    - ALCHEMY_API_KEY in .env file or environment variable
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    
    # Look for .env in etl directory, infra directory, or project root
    etl_dir = Path(__file__).parent.parent
    possible_env_paths = [
        etl_dir / '.env',
        etl_dir.parent / 'infra' / '.env',
        etl_dir.parent / '.env',
    ]
    
    for env_path in possible_env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass  # python-dotenv not installed, rely on environment variables

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wallet_etl.pipeline.daily_job import run_wallet_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Well-known Ethereum addresses for seeding
# These are public addresses that can be used for testing
SAMPLE_WALLETS = [
    # Vitalik Buterin's main wallet
    {
        "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "label": "vitalik.eth",
        "description": "Vitalik Buterin",
    },
    # Ethereum Foundation
    {
        "address": "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe",
        "label": "Ethereum Foundation",
        "description": "Ethereum Foundation Multisig",
    },
    # Uniswap Treasury
    {
        "address": "0x1a9C8182C09F50C8318d769245beA52c32BE35BC",
        "label": "Uniswap Treasury",
        "description": "Uniswap Protocol Treasury",
    },
    # Binance Hot Wallet
    {
        "address": "0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503",
        "label": "Binance Hot Wallet",
        "description": "Binance Exchange Hot Wallet",
    },
    # Binance Cold Wallet
    {
        "address": "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8",
        "label": "Binance Cold Wallet",
        "description": "Binance Exchange Cold Storage",
    },
    # Coinbase Cold Wallet
    {
        "address": "0xA090e606E30bD747d4E6245a1517EbE430F0057e",
        "label": "Coinbase Cold Wallet",
        "description": "Coinbase Exchange Cold Storage",
    },
    # Kraken Hot Wallet
    {
        "address": "0x2910543Af39abA0Cd09dBb2D50200b3E800A63D2",
        "label": "Kraken Hot Wallet",
        "description": "Kraken Exchange Hot Wallet",
    },
    # Arbitrum Bridge
    {
        "address": "0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a",
        "label": "Arbitrum Bridge",
        "description": "Arbitrum One Bridge Contract",
    },
    # Optimism Bridge
    {
        "address": "0x99C9fc46f92E8a1c0deC1b1747d010903E884bE1",
        "label": "Optimism Bridge",
        "description": "Optimism Gateway Bridge",
    },
    # Lido DAO Treasury
    {
        "address": "0x3e40D73EB977Dc6a537aF587D48316feE66E9C8c",
        "label": "Lido DAO",
        "description": "Lido DAO Treasury",
    },
]

# Quick mode wallets (subset for faster testing)
QUICK_WALLETS = SAMPLE_WALLETS[:3]


def seed_wallets(addresses: list[str] | None = None, quick: bool = False) -> None:
    """
    Seed the database with wallet data.
    
    Args:
        addresses: Optional list of specific addresses to seed.
                   If None, uses SAMPLE_WALLETS.
        quick: If True, only seeds a few wallets for quick testing.
    """
    # Check for Alchemy API key
    api_key = os.environ.get("ALCHEMY_API_KEY")
    if not api_key:
        logger.error(
            "ALCHEMY_API_KEY environment variable is not set. "
            "Please set it before running this script."
        )
        logger.info(
            "You can get a free API key from https://www.alchemy.com/"
        )
        sys.exit(1)
    
    # Determine which wallets to seed
    if addresses:
        wallet_addresses = addresses
        logger.info(f"Seeding {len(wallet_addresses)} custom wallet(s)")
    elif quick:
        wallet_addresses = [w["address"] for w in QUICK_WALLETS]
        logger.info(f"Quick mode: Seeding {len(wallet_addresses)} wallet(s)")
    else:
        wallet_addresses = [w["address"] for w in SAMPLE_WALLETS]
        logger.info(f"Seeding {len(wallet_addresses)} sample wallet(s)")
    
    # Log the wallets being seeded
    for addr in wallet_addresses:
        # Find label if available
        wallet_info = next(
            (w for w in SAMPLE_WALLETS if w["address"].lower() == addr.lower()),
            None
        )
        if wallet_info:
            logger.info(f"  - {wallet_info['label']}: {addr}")
        else:
            logger.info(f"  - {addr}")
    
    # Run the ETL pipeline
    logger.info("Starting ETL pipeline...")
    try:
        run_wallet_pipeline(wallet_addresses)
        logger.info("Seeding completed successfully!")
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        raise


def main() -> None:
    """Main entry point for the seed script."""
    parser = argparse.ArgumentParser(
        description="Seed the database with wallet health scores.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Seed all sample wallets:
    python -m scripts.seed_wallets

    # Quick mode (3 wallets):
    python -m scripts.seed_wallets --quick

    # Seed specific wallets:
    python -m scripts.seed_wallets --address 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

    # List available sample wallets:
    python -m scripts.seed_wallets --list
        """
    )
    parser.add_argument(
        "--address",
        action="append",
        dest="addresses",
        help="Specific wallet address to seed (can be used multiple times)",
        default=[],
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: only seed 3 wallets for faster testing",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available sample wallets and exit",
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable sample wallets:\n")
        print(f"{'Label':<25} {'Description':<35} Address")
        print("-" * 100)
        for wallet in SAMPLE_WALLETS:
            print(f"{wallet['label']:<25} {wallet['description']:<35} {wallet['address']}")
        print()
        return
    
    addresses = args.addresses if args.addresses else None
    seed_wallets(addresses=addresses, quick=args.quick)


if __name__ == "__main__":
    main()
