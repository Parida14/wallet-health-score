from fastapi import FastAPI


app = FastAPI(title="Wallet Health Score API", version="0.1.0")


@app.get("/health", tags=["system"])
def read_health() -> dict[str, str]:
    """Simple health endpoint to verify the API container boots."""
    return {"status": "ok"}
