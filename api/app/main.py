import os
from datetime import date
from typing import List

import psycopg2
from fastapi import FastAPI, HTTPException
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
            WHERE address = %s
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
            WHERE address = %s
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
    activity: float = Field(..., alias="activity_score")
    diversification: float = Field(..., alias="diversification_score")
    risk: float = Field(..., alias="risk_score")
    profitability: float = Field(..., alias="profitability_score")
    stability: float = Field(..., alias="stability_score")

    model_config = {"populate_by_name": True}


class WalletScoreResponse(BaseModel):
    address: str
    wallet_score: float = Field(..., alias="total_score")
    components: ScoreComponents
    last_updated: date = Field(..., alias="date")
    metrics: dict

    model_config = {"populate_by_name": True}


class CompareRequest(BaseModel):
    addresses: List[str] = Field(..., min_length=2, max_length=10, description="List of wallet addresses to compare")


class CompareResponse(BaseModel):
    wallets: List[WalletScoreResponse]
    comparison: dict = Field(default_factory=dict, description="Comparison statistics")


# --- API ---
app = FastAPI(title="Wallet Health Score API", version="0.1.0")


@app.get("/health", tags=["system"])
def read_health() -> dict[str, str]:
    """Simple health endpoint to verify the API container boots."""
    return {"status": "ok"}


@app.get("/score/{address}", response_model=WalletScoreResponse, tags=["scoring"])
def get_wallet_score(address: str):
    """Get the latest health score for a given wallet address."""
    score_data = pg_store.get_latest_score(address.lower())
    if not score_data:
        raise HTTPException(status_code=404, detail="Wallet score not found.")
    return score_data


@app.get("/history/{address}", response_model=List[WalletScoreResponse], tags=["scoring"])
def get_wallet_history(address: str, days: int = 30):
    """Get the historical health scores for a given wallet address."""
    history_data = pg_store.get_score_history(address.lower(), limit=days)
    if not history_data:
        raise HTTPException(status_code=404, detail="Wallet history not found.")
    return history_data


@app.post("/compare", response_model=CompareResponse, tags=["scoring"])
def compare_wallets(request: CompareRequest):
    """Compare health scores across multiple wallet addresses."""
    wallets_data = []
    missing_addresses = []

    for addr in request.addresses:
        score_data = pg_store.get_latest_score(addr.lower())
        if score_data:
            wallets_data.append(score_data)
        else:
            missing_addresses.append(addr)

    if not wallets_data:
        raise HTTPException(
            status_code=404,
            detail=f"No scores found for any of the provided addresses: {missing_addresses}"
        )

    # Calculate comparison statistics
    scores = [w["total_score"] for w in wallets_data]
    comparison = {
        "total_wallets_found": len(wallets_data),
        "missing_wallets": missing_addresses,
        "average_score": sum(scores) / len(scores) if scores else 0,
        "highest_score": max(scores) if scores else 0,
        "lowest_score": min(scores) if scores else 0,
        "ranking": sorted(
            [{"address": w["address"], "score": w["total_score"]} for w in wallets_data],
            key=lambda x: x["score"],
            reverse=True
        )
    }

    return {"wallets": wallets_data, "comparison": comparison}
