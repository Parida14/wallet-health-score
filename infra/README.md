# Infrastructure

Infrastructure as code, local development tooling, and deployment assets.

## Local Stack

Spin up the local dependencies (Postgres, MinIO, Airflow, API placeholder) using Docker Compose:

```bash
docker compose -f infra/docker-compose.yml up --build
```

Environment variables are sourced from the root `.env` file (see `.env.example`).

## Layout

- `docker-compose.yml` — local services
- Future additions: Terraform / Pulumi stacks, shared infra scripts, etc.
