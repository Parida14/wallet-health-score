import os
import re
import logging
import threading
import traceback
from typing import List, Optional
from datetime import datetime, timezone

import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")


# --- Database Connection ---
class PostgresStore:
    def __init__(self, dsn: str):
        self.dsn = dsn

    def _connect(self):
        return psycopg2.connect(self.dsn)

    def get_latest_score(self, address: str) -> dict | None:
        query = """
            SELECT
                address, date, activity_score, diversification_score, risk_score,
                profitability_score, stability_score, total_score, metrics
            FROM features_daily
            WHERE LOWER(address) = LOWER(%s)
            ORDER BY date DESC
            LIMIT 1;
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, (address,))
            row = cur.fetchone()
            if not row:
                return None
            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))

    def get_score_history(self, address: str, limit: int = 30) -> List[dict]:
        query = """
            SELECT
                address, date, activity_score, diversification_score, risk_score,
                profitability_score, stability_score, total_score, metrics
            FROM features_daily
            WHERE LOWER(address) = LOWER(%s)
            ORDER BY date DESC
            LIMIT %s;
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, (address, limit))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]

    # --- Extraction Job Methods ---

    def ensure_extraction_jobs_table(self) -> None:
        """Create the extraction_jobs table if it does not exist."""
        ddl = """
        CREATE TABLE IF NOT EXISTS extraction_jobs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            address TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_extraction_jobs_address
            ON extraction_jobs (address, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_extraction_jobs_status
            ON extraction_jobs (status);
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(ddl)
            conn.commit()

    def create_extraction_job(self, address: str) -> dict:
        """Insert a new extraction job and return it."""
        query = """
            INSERT INTO extraction_jobs (address, status)
            VALUES (%s, 'pending')
            RETURNING id, address, status, error_message, created_at, updated_at;
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, (address,))
            row = cur.fetchone()
            cols = [desc[0] for desc in cur.description]
            conn.commit()
            return dict(zip(cols, row))

    def update_extraction_job(self, job_id: str, status: str, error_message: Optional[str] = None) -> None:
        """Update the status of an extraction job."""
        query = """
            UPDATE extraction_jobs
            SET status = %s, error_message = %s, updated_at = NOW()
            WHERE id = %s;
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, (status, error_message, job_id))
            conn.commit()

    def get_extraction_job(self, job_id: str) -> dict | None:
        """Get an extraction job by its ID."""
        query = """
            SELECT id, address, status, error_message, created_at, updated_at
            FROM extraction_jobs
            WHERE id = %s;
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, (job_id,))
            row = cur.fetchone()
            if not row:
                return None
            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))

    def get_latest_extraction_job(self, address: str) -> dict | None:
        """Get the most recent extraction job for an address."""
        query = """
            SELECT id, address, status, error_message, created_at, updated_at
            FROM extraction_jobs
            WHERE LOWER(address) = LOWER(%s)
            ORDER BY created_at DESC
            LIMIT 1;
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, (address,))
            row = cur.fetchone()
            if not row:
                return None
            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))


DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://wallet_admin:wallet_pass@localhost:5432/wallet_scores"
)
pg_store = PostgresStore(DATABASE_URL)


# --- API Models ---
class ScoreComponents(BaseModel):
    activity: float
    diversification: float
    risk: float
    profitability: float
    stability: float


class WalletMetrics(BaseModel):
    transactions_count: int = 0
    recent_transactions_count: int = 0
    positions_count: int = 0


class WalletScoreResponse(BaseModel):
    address: str
    wallet_score: float
    components: ScoreComponents
    last_updated: str
    metrics: WalletMetrics


class CompareRequest(BaseModel):
    addresses: List[str] = Field(..., min_length=2, max_length=10, description="List of wallet addresses to compare")


class CompareResponse(BaseModel):
    wallets: List[WalletScoreResponse]
    comparison: dict = Field(default_factory=dict, description="Comparison statistics")


class ExtractionJobResponse(BaseModel):
    id: str
    address: str
    status: str
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


def _transform_score_data(data: dict) -> dict:
    """Transform flat database row into nested API response format."""
    metrics = data.get("metrics") or {}
    return {
        "address": data["address"],
        "wallet_score": float(data["total_score"]),
        "components": {
            "activity": float(data["activity_score"]),
            "diversification": float(data["diversification_score"]),
            "risk": float(data["risk_score"]),
            "profitability": float(data["profitability_score"]),
            "stability": float(data["stability_score"]),
        },
        "last_updated": str(data["date"]),
        "metrics": {
            "transactions_count": metrics.get("transactions_count", 0),
            "recent_transactions_count": metrics.get("recent_tx_count", 0),
            "positions_count": metrics.get("positions_count", 0),
        },
    }


def _transform_job(data: dict) -> dict:
    """Transform extraction job row into API response format."""
    return {
        "id": str(data["id"]),
        "address": data["address"],
        "status": data["status"],
        "error_message": data.get("error_message"),
        "created_at": str(data["created_at"]),
        "updated_at": str(data["updated_at"]),
    }


def _is_valid_eth_address(address: str) -> bool:
    """Validate Ethereum address format."""
    return bool(re.match(r"^0x[a-fA-F0-9]{40}$", address))


# --- Background ETL Worker ---

def _run_etl_background(job_id: str, address: str) -> None:
    """Run the ETL pipeline in a background thread and update job status."""
    try:
        pg_store.update_extraction_job(job_id, "processing")
        logger.info("Starting ETL pipeline for job=%s address=%s", job_id, address)

        # Import the ETL pipeline (mounted at /app/etl_src in Docker)
        from wallet_etl.pipeline.daily_job import run_wallet_pipeline

        run_wallet_pipeline([address])

        pg_store.update_extraction_job(job_id, "completed")
        logger.info("ETL pipeline completed for job=%s address=%s", job_id, address)
    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {exc}"
        logger.error("ETL pipeline failed for job=%s address=%s: %s", job_id, address, error_msg)
        logger.error(traceback.format_exc())
        pg_store.update_extraction_job(job_id, "failed", error_message=error_msg)


# --- API ---
app = FastAPI(title="Wallet Health Score API", version="0.1.0")

# Configure CORS to allow frontend requests
# Read allowed origins from environment variable for production
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "").split(",") if os.environ.get("ALLOWED_ORIGINS") else []
default_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins + default_origins if allowed_origins else default_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Ensure required tables exist on startup."""
    try:
        pg_store.ensure_extraction_jobs_table()
        logger.info("extraction_jobs table ensured")
    except Exception as exc:
        logger.warning("Could not ensure extraction_jobs table: %s", exc)


@app.get("/health", tags=["system"])
def read_health() -> dict[str, str]:
    """Simple health endpoint to verify the API container boots."""
    return {"status": "ok"}


@app.get("/score/{address}", response_model=WalletScoreResponse, tags=["scoring"])
def get_wallet_score(address: str):
    """Get the latest health score for a given wallet address."""
    score_data = pg_store.get_latest_score(address)
    if not score_data:
        raise HTTPException(status_code=404, detail="Wallet score not found.")
    return _transform_score_data(score_data)


@app.get("/history/{address}", response_model=List[WalletScoreResponse], tags=["scoring"])
def get_wallet_history(address: str, days: int = 30):
    """Get the historical health scores for a given wallet address."""
    history_data = pg_store.get_score_history(address, limit=days)
    if not history_data:
        raise HTTPException(status_code=404, detail="Wallet history not found.")
    return [_transform_score_data(d) for d in history_data]


@app.post("/compare", response_model=CompareResponse, tags=["scoring"])
def compare_wallets(request: CompareRequest):
    """Compare health scores across multiple wallet addresses."""
    wallets_data = []
    missing_addresses = []

    for addr in request.addresses:
        score_data = pg_store.get_latest_score(addr)
        if score_data:
            wallets_data.append(_transform_score_data(score_data))
        else:
            missing_addresses.append(addr)

    if not wallets_data:
        raise HTTPException(
            status_code=404,
            detail=f"No scores found for any of the provided addresses: {missing_addresses}"
        )

    # Calculate comparison statistics
    scores = [w["wallet_score"] for w in wallets_data]
    comparison = {
        "total_wallets_found": len(wallets_data),
        "missing_wallets": missing_addresses,
        "average_score": sum(scores) / len(scores) if scores else 0,
        "highest_score": max(scores) if scores else 0,
        "lowest_score": min(scores) if scores else 0,
        "ranking": sorted(
            [{"address": w["address"], "score": w["wallet_score"]} for w in wallets_data],
            key=lambda x: x["score"],
            reverse=True
        )
    }

    return {"wallets": wallets_data, "comparison": comparison}


# --- Extraction Endpoints ---

@app.post(
    "/extract/{address}",
    response_model=ExtractionJobResponse,
    status_code=202,
    tags=["extraction"],
)
def extract_wallet(address: str):
    """
    Trigger on-demand extraction of wallet transactions and score calculation.

    Creates a background job that:
    1. Fetches transaction history from Alchemy
    2. Stores raw data in MinIO
    3. Calculates health scores
    4. Stores results in PostgreSQL

    Returns a job object that can be polled for status.
    """
    if not _is_valid_eth_address(address):
        raise HTTPException(status_code=400, detail="Invalid Ethereum address format.")

    # Check if there's already a pending/processing job for this address
    existing_job = pg_store.get_latest_extraction_job(address)
    if existing_job and existing_job["status"] in ("pending", "processing"):
        return JSONResponse(
            status_code=202,
            content=_transform_job(existing_job),
        )

    # Create a new job
    job = pg_store.create_extraction_job(address)
    job_id = str(job["id"])

    # Spawn background thread
    thread = threading.Thread(
        target=_run_etl_background,
        args=(job_id, address),
        daemon=True,
    )
    thread.start()

    return JSONResponse(status_code=202, content=_transform_job(job))


@app.get(
    "/extract/status/{job_id}",
    response_model=ExtractionJobResponse,
    tags=["extraction"],
)
def get_extraction_status(job_id: str):
    """Get the status of an extraction job by its ID."""
    job = pg_store.get_extraction_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Extraction job not found.")
    return _transform_job(job)


@app.get(
    "/extract/status/address/{address}",
    response_model=ExtractionJobResponse,
    tags=["extraction"],
)
def get_extraction_status_by_address(address: str):
    """Get the latest extraction job status for a given wallet address."""
    job = pg_store.get_latest_extraction_job(address)
    if not job:
        raise HTTPException(status_code=404, detail="No extraction job found for this address.")
    return _transform_job(job)
