# Wallet Health Score — AI Context

This file provides context for AI coding agents (Cursor, Copilot, etc.) working on this repository.

---

## Project Overview

**Wallet Health Score** is an on-chain wallet health assessment service. It fetches blockchain data via Alchemy, runs an ETL pipeline, computes a 0–100 health score from five components (Activity, Diversification, Risk, Profitability, Stability), and exposes scores via a REST API and Next.js dashboard.

**Architecture:** ETL (Python + Airflow) → PostgreSQL + MinIO → FastAPI → Next.js

---

## Monorepo Structure

```
wallet-health-score/
├── etl/          # Data pipeline (Alchemy → MinIO → Postgres)
├── api/          # FastAPI REST API
├── web/          # Next.js frontend (App Router)
└── infra/        # Docker Compose, deployment configs
```

| Dir   | Purpose | Tech |
|-------|---------|------|
| `etl/` | Extract from Alchemy, store raw JSON in MinIO, transform and load into Postgres | Python, Airflow |
| `api/` | Serve scores, history, compare, trigger on-demand extraction | FastAPI |
| `web/` | Wallet search, score cards, history charts, comparison | Next.js, React |
| `infra/` | Local stack (Postgres, MinIO, Airflow, API, web) | Docker Compose |

---

## Key Files → Concepts

| File | Concept |
|------|---------|
| `etl/src/wallet_etl/clients/alchemy.py` | RPC client, pagination, Alchemy API |
| `etl/src/wallet_etl/storage/minio_store.py` | Object storage, S3-compatible raw JSON backup |
| `etl/src/wallet_etl/storage/postgres_store.py` | Schema, upserts |
| `etl/src/wallet_etl/pipeline/daily_job.py` | ETL flow, scoring logic (five components) |
| `etl/dags/wallet_score_daily.py` | Airflow DAG, Variables |
| `api/app/main.py` | FastAPI routes, background extraction jobs, weekly activity |
| `web/src/lib/api.ts` | API client, `NEXT_PUBLIC_API_URL` |
| `web/src/app/wallet/[address]/page.tsx` | Wallet detail, polling for extraction status |
| `web/src/components/activity-trend-chart.tsx` | Weekly activity trend (tx count + intensity) |
| `infra/docker-compose.yml` | Services, healthchecks, volumes |

---

## Database Schema (PostgreSQL)

- `wallets` — One row per address (PK = address)
- `transactions` — One row per tx (PK = hash)
- `positions` — One row per (address, token)
- `features_daily` — One row per (address, date) with scores + metrics (upserted daily)
- `extraction_jobs` — On-demand job tracking (status: pending/processing/completed/failed)

---

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/score/{address}` | Latest score + components |
| GET | `/history/{address}` | Score time-series (`features_daily` snapshots) |
| GET | `/activity/{address}?weeks=52` | Weekly tx counts + activity intensity (from `transactions`) |
| POST | `/compare` | Compare 2–10 wallets |
| POST | `/extract/{address}` | Trigger ETL (202 Accepted, poll status) |
| GET | `/extract/status/{job_id}` | Job status |

---

## Build & Run

```bash
# Start full stack
docker compose -f infra/docker-compose.yml up --build

# ETL (Python)
cd etl && uv run python -c "from wallet_etl.pipeline.daily_job import run_wallet_pipeline; run_wallet_pipeline(['0x...'])"

# API (standalone)
cd api && uvicorn app.main:app --reload

# Web (standalone)
cd web && npm run dev
```

Env vars: `.env` at repo root (see `.env.example`). Required: `DATABASE_URL`, `ALCHEMY_API_KEY`, `MINIO_*`, `NEXT_PUBLIC_API_URL` for web.

---

## Conventions

- **Python (etl/api):** Type hints, Pydantic for validation. Scoring logic lives in `daily_job.py`; functions like `calculate_activity_score` etc.
- **TypeScript/React:** App Router, `'use client'` for hooks/events, `lib/api.ts` for fetches. Components: shadcn/ui, Recharts.
- **Addresses:** Use `LOWER(address)` in SQL; frontend accepts checksummed or lowercase. Prefer lowercase at write boundaries.
- **Scoring:** Each component 0–1 in the API/DB; UI multiplies by 100 for display. Risk is inverted (higher = safer).
- **Activity trend vs score history:** The wallet page Activity Trend chart is built from the `transactions` event log (weekly rollups). Do not use sparse `features_daily` rows as a continuous activity chart — those are point-in-time score snapshots from ETL runs.
- **Tests:** Prefer TDD for scoring and API changes. Run `cd api && PYTHONPATH=. pytest` and `cd etl && PYTHONPATH=src pytest`.
- **Security:** Never log secrets; validate Ethereum addresses on write paths; do not commit `.env`.

---

## Deeper Docs

- `LEARNING.md` — Concepts, WHY behind design choices (local learning notes; may be untracked)
- `cursor.md` — Build guide, phases
- `PROJECT_OVERVIEW.md` — Architecture summary
- `START_HERE.md` — Deployment (Vercel, Railway, Neon)
- `Wallet_Score_Health_API_PRD.md` — Original PRD
- `E2E_TESTING.md` — Manual full-stack test checklist

---

## Notes for Agents

- Batch ETL runs via Airflow daily; on-demand via `POST /extract`.
- Raw Alchemy JSON stored in MinIO (`{date}/transactions/{address}.json`) for audit/reprocessing.
- `features_daily` is the source of truth for scores; idempotent by (address, date).
- On extraction: UI polls `/extract/status/{job_id}` every 5s until completed/failed.
- This repo does **not** use project-local Cursor ECC skills/hooks under `.cursor/` — keep agent config out of the repo unless explicitly requested.
