# Secrets & Credentials Guide

Phase 0/1 services rely on a mix of local environment variables and external API keys. Follow this checklist before running the stack or the ETL jobs.

## 1. Local Infrastructure (.env)

Clone `.env.example` to `.env` at the repo root and adjust the values:

| Variable | Purpose | Notes |
| --- | --- | --- |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT` | Local Postgres auth | Change the password from the default. |
| `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_API_PORT`, `MINIO_CONSOLE_PORT`, `MINIO_BUCKET` | MinIO console/API | Password must be ≥ 8 chars. Bucket defaults to `wallet-raw`. |
| `AIRFLOW_UID`, `AIRFLOW_GID` | File permissions for Airflow container | Leave defaults unless on Linux with conflicting UID/GID. |
| `AIRFLOW_FERNET_KEY` | Encrypts Airflow connections/variables | Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. |
| `AIRFLOW_WEBSERVER_PORT` | Port binding for Airflow UI | Change if 8080 is occupied. |
| `API_PORT` | FastAPI port | Needed for reverse proxies later. |
| `ALCHEMY_API_KEY`, `COVALENT_API_KEY`, `COVALENT_CHAIN_ID` | External data providers | Chain ID defaults to `eth-mainnet`. |

> Always store the `.env` file outside of version control. Add or verify `.env` is listed in `.gitignore`.

## 2. Airflow Connections & Variables

After `docker compose` brings up Airflow, log into the web UI (`http://localhost:${AIRFLOW_WEBSERVER_PORT}`) with the default admin user printed in the container logs. Create these connections:

| Conn ID | Conn Type | Details |
| --- | --- | --- |
| `postgres_wallet_readwrite` | Postgres | Host `postgres`, schema `${POSTGRES_DB}`, login `${POSTGRES_USER}`, password `${POSTGRES_PASSWORD}`, port `5432`. |
| `minio_default` | S3 | Extra JSON: `{"aws_access_key_id": "...", "aws_secret_access_key": "...", "host": "http://minio:9000", "region_name": "us-east-1"}`. |
| `alchemy_http` | HTTP | Host `https://eth-mainnet.g.alchemy.com`, extra headers `{"X-Alchemy-Token": "${ALCHEMY_API_KEY}"}`. |
| `covalent_http` | HTTP | Host `https://api.covalenthq.com`, extra params `{"key": "${COVALENT_API_KEY}"}`. |

Store external API keys as Airflow **Variables** (`ALCHEMY_API_KEY`, `COVALENT_API_KEY`) or as Secrets Backend entries if you enable one later.

## 3. External Provider Credentials

| Provider | Credential | How to obtain | Scope |
| --- | --- | --- | --- |
| Alchemy | API Key | Create free app at <https://dashboard.alchemy.com/> | ETH Mainnet JSON-RPC & data APIs. |
| Covalent | API Key | Sign up at <https://www.covalenthq.com/platform/> | Token balances, transactions, pricing. |
| Dune (optional) | API Token | <https://dune.com/app/new/> | Backup analytics source. |
| Etherscan (optional) | API Key | <https://etherscan.io/myapikey> | Fallback for transactions if needed. |

Keep provider keys out of `.env` if you plan to share the file; prefer authenticated secret stores (1Password, Doppler, Vault) and inject at runtime.

## 4. GitHub Actions Secrets

For CI/CD, mirror the sensitive values in repository secrets:

- `POSTGRES_PASSWORD`
- `MINIO_ROOT_PASSWORD`
- `AIRFLOW_FERNET_KEY`
- `ALCHEMY_API_KEY`
- `COVALENT_API_KEY`

Reference them in future workflow steps using `${{ secrets.NAME }}`. The current CI workflow only compiles/lints, but future jobs (tests, migrations) will need them.

## 5. Production/Staging (Future)

When moving past local development:

- Use managed Postgres (e.g., Railway, Fly.io, RDS) with dedicated credentials per environment.
- Rotate MinIO access keys or switch to S3-compatible storage with IAM users.
- Enable Airflow Secrets Backend (AWS Secrets Manager, GCP Secret Manager, or Hashicorp Vault) to centralize credentials.
- Store FastAPI `API_KEY` values in a separate secrets file or management service, not in source.
- Document rotation cadence (quarterly minimum) and owners.

Keeping secrets organized early avoids rework once we deploy the MVP API and data pipelines.
