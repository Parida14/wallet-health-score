from fastapi import FastAPI

app = FastAPI(title="Wallet Health API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


