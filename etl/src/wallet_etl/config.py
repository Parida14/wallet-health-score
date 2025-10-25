"""Central configuration for ETL jobs."""

from dataclasses import dataclass
import os


@dataclass(slots=True)
class Settings:
    database_url: str = os.environ.get(
        "DATABASE_URL",
        "postgresql://wallet_admin:wallet_pass@localhost:5432/wallet_scores",
    )
    minio_endpoint: str = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")
    minio_access_key: str = os.environ.get("MINIO_ACCESS_KEY", "")
    minio_secret_key: str = os.environ.get("MINIO_SECRET_KEY", "")
    minio_bucket: str = os.environ.get("MINIO_BUCKET", "wallet-raw")
    alchemy_api_key: str = os.environ.get("ALCHEMY_API_KEY", "")


settings = Settings()
