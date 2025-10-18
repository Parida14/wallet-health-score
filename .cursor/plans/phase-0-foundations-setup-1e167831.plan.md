<!-- 1e167831-abc7-4d7c-a3c7-582b018b54ab 7becf2d5-c329-4a97-89e9-68e79c45cea4 -->
# Phase 0 - Foundations Setup

## Monorepo Structure

Create a pnpm + Turborepo monorepo with the following structure:

```
/
├── apps/
│   ├── web/          # Next.js 15 App Router + shadcn/ui
│   ├── api/          # FastAPI + Redis cache
│   └── etl/          # Python + Airflow DAGs
├── packages/
│   ├── database/     # Shared DB schemas & migrations
│   └── types/        # Shared TypeScript types
├── infra/
│   └── docker/       # Docker Compose configs
├── .github/
│   └── workflows/    # GitHub Actions CI/CD
├── pnpm-workspace.yaml
├── turbo.json
├── package.json
└── README.md
```

## Core Setup Tasks

### 1. Root Configuration

- Initialize pnpm workspace with `pnpm-workspace.yaml`
- Configure Turborepo in `turbo.json` for build/dev/lint pipelines
- Root `package.json` with workspace scripts
- `.gitignore` for node_modules, .env files, Python cache, etc.
- `.env.example` template for all required environment variables

### 2. Docker Compose Services

Create `infra/docker/docker-compose.yml` with:

- **Postgres 16**: Database for structured data (wallets, transactions, positions, features)
- **MinIO**: S3-compatible object storage for raw JSON blobs
- **Redis**: Caching layer for API responses
- **Apache Airflow**: ETL orchestration (webserver, scheduler, worker)
- **pgAdmin** (optional): Database management UI

All services configured with:

- Named volumes for persistence
- Health checks
- Network configuration
- Environment variables from `.env`

### 3. Web App (`apps/web`)

- Initialize Next.js 15 with App Router and TypeScript
- Install dependencies: `shadcn/ui`, `tailwindcss`, `recharts`, `nuqs`
- Configure `tailwind.config.ts` and `components.json` for shadcn
- Create basic layout structure: `app/layout.tsx`, `app/page.tsx`
- Add placeholder components in `components/` directory
- Configure `next.config.js` for optimal performance

### 4. API App (`apps/api`)

- Set up Python 3.11+ environment with `pyproject.toml` (using Poetry or pip)
- Install FastAPI, uvicorn, SQLAlchemy, redis-py, psycopg2, pydantic
- Create basic project structure:
  - `main.py`: FastAPI app initialization
  - `routers/`: API route handlers
  - `models/`: SQLAlchemy models (placeholder)
  - `config.py`: Settings management with pydantic-settings
- Add Dockerfile for API service
- Create health check endpoint

### 5. ETL App (`apps/etl`)

- Set up Python project with Airflow dependencies
- Create `dags/` directory for Airflow DAGs
- Create `scripts/` directory for ETL logic
- Install alchemy-sdk (Alchemy API client)
- Create `requirements.txt` or `pyproject.toml`
- Add basic DAG template (not yet functional, just structure)

### 6. Database Package (`packages/database`)

- Create SQL migration files using Alembic or raw SQL
- Initial schema definitions (wallets, transactions, positions, features_daily)
- Migration runner script
- Connection utilities

### 7. Types Package (`packages/types`)

- Shared TypeScript interfaces for API responses
- Wallet score types, component types
- Request/response schemas

### 8. GitHub Actions

Create `.github/workflows/ci.yml`:

- Lint check (ESLint for TS, Ruff/Black for Python)
- Type check (TypeScript, mypy for Python)
- Build verification (Turborepo build)
- Run on PR and main branch pushes

### 9. Documentation

- Root `README.md` with:
  - Project overview
  - Quick start guide
  - Development setup instructions
  - Architecture diagram (text-based)
  - Contribution guidelines
- Individual READMEs for each app/package

## Environment Variables Template

Create `.env.example`:

```
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=wallet_health
POSTGRES_PASSWORD=your_password
POSTGRES_DB=wallet_health_db

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_ENDPOINT=localhost:9000

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Airflow
AIRFLOW_UID=50000
AIRFLOW__CORE__EXECUTOR=LocalExecutor

# API Keys
ALCHEMY_API_KEY=your_alchemy_key

# API
API_PORT=8000
API_HOST=0.0.0.0

# Web
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Success Criteria

- All services start successfully with `docker-compose up`
- Web app runs on `localhost:3000`
- API runs on `localhost:8000` with `/health` endpoint
- Airflow UI accessible on `localhost:8080`
- Postgres accessible and accepts connections
- MinIO console accessible on `localhost:9001`
- Turborepo commands work: `pnpm build`, `pnpm dev`, `pnpm lint`
- Git repository initialized with proper `.gitignore`

### To-dos

- [ ] Initialize pnpm workspace, Turborepo config, root package.json, .gitignore, and .env.example
- [ ] Create Docker Compose configuration with Postgres, MinIO, Redis, and Airflow services
- [ ] Set up Next.js 15 App Router application with TypeScript, shadcn/ui, and Tailwind
- [ ] Set up FastAPI application with basic structure, health endpoint, and dependencies
- [ ] Set up Python ETL project structure with Airflow DAGs directory and Alchemy SDK
- [ ] Create database and types shared packages with initial schemas
- [ ] Set up GitHub Actions CI/CD workflow for linting, type checking, and builds
- [ ] Write comprehensive README files for root and each app/package
- [ ] Verify all services start correctly and development commands work