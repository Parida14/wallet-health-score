# ETL Service

Phase 1 data pipeline responsible for ingesting on-chain activity, storing raw payloads, and computing daily wallet features.

## Layout

- `requirements.txt` — Python dependencies for local runs and Airflow workers.
- `src/wallet_etl` — reusable clients, storage helpers, and pipeline orchestration.
- `dags/` — Airflow DAG definitions (mounted into the Airflow container).
- `sql/` — Postgres schema migration scripts.

## Installing Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r etl/requirements.txt
```

Copy `.env.example` to `.env` and export environment variables before running ad-hoc jobs.

## Running (Ad-hoc)

```bash
export $(cat .env | xargs)  # or use direnv
python -m wallet_etl.pipeline.daily_job --address 0xabc... --address 0xdef...
```

For scheduled runs, use Airflow via `docker compose -f infra/docker-compose.yml up` and configure the `WALLET_PIPELINE_ADDRESSES` Airflow Variable.
