# End-to-end testing (fresh clone)

How to run and manually test the Wallet Health Score app on a new machine (e.g. new Mac Mini) after cloning the repo. The app has **no automated E2E tests** (no Playwright/Cypress); this guide is for running the stack and verifying flows in the browser.

## Prerequisites

- **Node.js 20+** (for the web app; check with `node -v`)
- **Docker & Docker Compose** (for Postgres, API, MinIO, Airflow, and optionally the web app)
- **(Optional)** Python 3.11+ if you want to run the API or ETL locally instead of in Docker

You do **not** need a Python venv to run `docker compose up`—containers run in isolation. Use a venv only when running Python on your host (e.g. API with `uvicorn` or ETL scripts; see Option 2).

## Option 1: Full stack with Docker (recommended)

Runs Postgres, MinIO, Airflow, API, and the Next.js web app. Best for a full E2E check.

### 1. Environment file

From the **repo root**:

```bash
cp .env.example .env
```

Edit `.env` and set at least:

- **`AIRFLOW_FERNET_KEY`** – required for Airflow. Generate one:
  ```bash
  python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
  Paste the output into `.env` as `AIRFLOW_FERNET_KEY=...`.

- **`ALCHEMY_API_KEY`** – optional for E2E; only needed if you run ETL jobs that pull chain data. You can leave it empty to test the UI and API with existing/seed data.

### 2. Start the stack

From the **repo root**:

```bash
# From repo root. Use docker-compose (hyphen) if you use Colima; use "docker compose" (space) if you have the Docker Compose V2 plugin.
docker-compose -f infra/docker-compose.yml up --build
```

Wait until all services are up (Postgres healthy, API and web listening). Typical ports:

- **Web**: http://localhost:3000  
- **API**: http://localhost:8000  
- **API docs**: http://localhost:8000/docs  
- **Airflow**: http://localhost:8080  
- **MinIO console**: http://localhost:9001  

### 3. Initialize the database (first time only)

The API expects Postgres tables from the ETL schema. Run the SQL migrations once (with Postgres already running). **Run these from the project root** so the `etl/sql/...` paths resolve:

```bash
# From project root (e.g. .../wallet-health-score)
# Default connection (matches .env.example)
export PGHOST=localhost PGPORT=5432 PGDATABASE=wallet_scores PGPASSWORD=wallet_pass PGUSER=wallet_admin

psql -h localhost -U wallet_admin -d wallet_scores -f etl/sql/001_init_schema.sql
psql -h localhost -U wallet_admin -d wallet_scores -f etl/sql/002_extraction_jobs.sql
```

You need `psql` on your machine (e.g. `brew install libpq` then `brew link --force libpq`, or Postgres client tools).

If your `.env` uses different Postgres credentials, set `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` accordingly.

### 4. (Optional) Seed a test wallet

So that “look up wallet” returns data instead of “no data”:

```bash
psql -h localhost -U wallet_admin -d wallet_scores -c "
INSERT INTO wallets (address, chain) VALUES ('0xd8da6bf26964af9d7eed9e03e53415d37aa96045', 'eth_mainnet')
ON CONFLICT (address) DO NOTHING;
INSERT INTO features_daily (address, date, activity_score, diversification_score, risk_score, profitability_score, stability_score, total_score)
VALUES ('0xd8da6bf26964af9d7eed9e03e53415d37aa96045', CURRENT_DATE, 0.75, 0.80, 0.60, 0.70, 0.85, 0.74)
ON CONFLICT (address, date) DO NOTHING;
"
```

That address is the sample “vitalik.eth” from the web README.

### 5. Test in the browser

1. Open **http://localhost:3000**.
2. Enter a wallet address (e.g. `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`) and submit.
3. If you ran the seed step, you should see score and charts; otherwise you may see “no data” until ETL has run for that address.
4. Try **Compare** (multiple wallets) and any other flows you care about.

### 6. Sanity-check the API

- **Health**: `curl http://localhost:8000/health`  
- **Score for seeded address**: `curl http://localhost:8000/score/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`  
- **API docs**: open http://localhost:8000/docs and try endpoints.

---

## Option 2: Web + API only (local dev, no Docker for app)

Use Docker only for Postgres (and optionally MinIO), run the API and Next.js app on your machine. Useful for fast iteration.

### 1. Start Postgres (and MinIO if needed)

From repo root, with `.env` in place:

```bash
docker-compose -f infra/docker-compose.yml up -d postgres minio
```

Run the same SQL as in Option 1 (steps 3 and optionally 4).

### 2. Run the API

```bash
cd api
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL="postgresql://wallet_admin:wallet_pass@localhost:5432/wallet_scores"
# Optional, if your code uses MinIO:
export MINIO_ENDPOINT=http://localhost:9000 MINIO_ACCESS_KEY=minioadmin MINIO_SECRET_KEY=minioadmin123
uvicorn app.main:app --reload --port 8000
```

### 3. Run the web app

In another terminal:

```bash
cd web
npm install
npm run dev
```

Open http://localhost:3000. Ensure `NEXT_PUBLIC_API_URL` is unset or set to `http://localhost:8000` (see `web/README.md` and `web/.env.example` if you use one).

### 4. Test

Same as Option 1: use the UI and optionally `curl`/docs to verify the API.

---

## Quick checklist (E2E)

- [ ] Stack (or at least Postgres + API + web) is up.
- [ ] DB schema applied (`001_init_schema.sql`, `002_extraction_jobs.sql`).
- [ ] Optional seed inserted for one test address.
- [ ] http://localhost:3000 loads.
- [ ] Wallet search returns either data (for seeded address) or a clear “no data”/error.
- [ ] http://localhost:8000/health returns OK.
- [ ] http://localhost:8000/docs loads and score/history/compare endpoints respond as expected.

## Troubleshooting

- **“Connection refused” to API** – Ensure the API container (or local uvicorn) is running and listening on the port the frontend uses (`NEXT_PUBLIC_API_URL`, default 8000).
- **“No data” for every wallet** – Run the seed step (Option 1 step 4) or run the ETL for that address (Airflow/minio and Alchemy key required).
- **Airflow won’t start** – Set `AIRFLOW_FERNET_KEY` in `.env` (see step 1 of Option 1).
- **Postgres connection errors** – Confirm `.env` matches the `psql`/`DATABASE_URL` settings (user, password, db, port).

For more on env vars and secrets, see **infra/SECRETS.md**. For deployment, see **START_HERE.md** and **web/README.md**.
