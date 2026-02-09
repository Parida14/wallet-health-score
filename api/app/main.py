import os
from typing import List

import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


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


# --- API ---
app = FastAPI(title="Wallet Health Score API", version="0.1.0")

# Configure CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
