"""Central configuration for ETL jobs."""

from dataclasses import dataclass
import os

# Try to load .env file if python-dotenv is available
try:
    from pathlib import Path
    from dotenv import load_dotenv
    
    # Look for .env in multiple locations
    etl_dir = Path(__file__).parent.parent.parent
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
    pass  # python-dotenv not installed


@dataclass(slots=True)
class Settings:
    database_url: str = os.environ.get(
        "DATABASE_URL",
        "postgresql://wallet_admin:wallet_pass@localhost:5432/wallet_scores",
    )
    minio_endpoint: str = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")
    # Support both naming conventions for MinIO credentials
    minio_access_key: str = os.environ.get(
        "MINIO_ACCESS_KEY", 
        os.environ.get("MINIO_ROOT_USER", "minioadmin")
    )
    minio_secret_key: str = os.environ.get(
        "MINIO_SECRET_KEY",
        os.environ.get("MINIO_ROOT_PASSWORD", "minioadmin123")
    )
    minio_bucket: str = os.environ.get("MINIO_BUCKET", "wallet-raw")
    alchemy_api_key: str = os.environ.get("ALCHEMY_API_KEY", "")


settings = Settings()
