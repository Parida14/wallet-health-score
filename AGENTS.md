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
| `api/app/main.py` | FastAPI routes, background extraction jobs |
| `web/src/lib/api.ts` | API client, `NEXT_PUBLIC_API_URL` |
| `web/src/app/wallet/[address]/page.tsx` | Wallet detail, polling for extraction status |
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
| GET | `/history/{address}` | Score time-series |
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
- **Addresses:** Use `LOWER(address)` in SQL; frontend accepts checksummed or lowercase.
- **Scoring:** Each component 0–1; total = mean × 100. Risk is inverted (higher = safer).

---

## ECC Conventions Inherited

This project follows the ECC plugin conventions from
~/Developer/everything-claude-code:
- Agent-first: delegate to specialized roles
- TDD with 80%+ coverage required
- Security-first: never log secrets, validate all inputs
- Plan complex features before writing code

### Skill Routing (project-specific)

Invoke these by name in chat. Skills live in `.cursor/skills/`.

| Goal | Skill to invoke |
|------|-----------------|
| Research before coding (Alchemy quirks, lib docs, prior art) | `search-first` |
| Add a new score component or fix a bug | `tdd-workflow` |
| Pre-commit / pre-deploy gate (lint, typecheck, tests, security) | `verification-loop` |
| Security audit of an endpoint or pipeline | `security-review` |
| Design a measurable test for the scoring algorithm | `eval-harness` |
| New FastAPI endpoint conventions | `api-design` + `backend-patterns` |
| Browser flow tests against the Next.js app | `e2e-testing` |
| Look up live API docs for Alchemy, FastAPI, Next.js, dbt | `documentation-lookup` |
| When approaching context limits | `strategic-compact` |

### Agent Routing (proactive delegation)

| Trigger | Use |
|---------|-----|
| Complex feature ("add gas-efficiency score component") | planner → tdd-guide → code-reviewer |
| Architectural decision ("how do we scale to 100K wallets/day") | architect |
| Just modified Python in `etl/` or `api/` | python-reviewer |
| Just modified TS in `web/` | typescript-reviewer |
| Touching `postgres_store.py` or any SQL | database-reviewer |
| Build/import error | build-error-resolver |
| Before merging to `main` | security-reviewer + verification-loop skill |

### MCP Servers Enabled

`.cursor/mcp.json` is intentionally trimmed to **3 servers**: `github`, `context7`, `memory`. Adding more burns context-window tokens. Audit before adding (rule of thumb: <10 MCPs, <80 tools active).

### Hooks Enabled

`.cursor/hooks.json` is the ECC default *minus* the tmux dev-server blocker (we don't use tmux here). Keep these on:
- **`block-no-verify`** — prevents `git commit --no-verify` from skipping pre-commit hooks
- **`before-submit-prompt`** — scans prompts for `sk-…`, `ghp_…`, `AKIA…` secret patterns
- **`before-tab-file-read`** — blocks Tab autocomplete from reading `.env`, `.key`, `.pem`
- **`after-file-edit`** — auto-format, typecheck, console.log audit

---

## Deeper Docs

- `LEARNING.md` — Concepts, WHY behind design choices
- `cursor.md` — Build guide, phases
- `PROJECT_OVERVIEW.md` — Architecture summary
- `START_HERE.md` — Deployment (Vercel, Railway, Neon)
- `Wallet_Score_Health_API_PRD.md` — Original PRD

---

## Notes for Agents

- Batch ETL runs via Airflow daily; on-demand via `POST /extract`.
- Raw Alchemy JSON stored in MinIO (`{date}/transactions/{address}.json`) for audit/reprocessing.
- `features_daily` is the source of truth for scores; idempotent by (address, date).
- On extraction: UI polls `/extract/status/{job_id}` every 5s until completed/failed.
