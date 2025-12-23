This document provides a detailed, step-by-step guide to building, running, and using the On-Chain Wallet Health Score service. It synthesizes information from the `PROJECT_OVERVIEW.md` and `Wallet_Score_Health_API_PRD.md`.

## 1. Project Goal

The primary goal is to create a service that assesses the "health" of an on-chain cryptocurrency wallet. This is achieved by calculating a numerical score from 0 to 100 based on five key metrics:

- **Activity:** Transaction frequency and engagement.
- **Diversification:** Spread of assets across different tokens and protocols.
- **Risk:** Exposure to volatile assets and leverage.
- **Profitability:** Realized and unrealized gains and losses.
- **Stability:** Holding patterns and asset rotation.

The final service will consist of a data pipeline, a REST API, and a web dashboard for visualization.

## 2. Development Roadmap

The development is broken down into distinct phases, from setting up the foundational infrastructure to deploying the final application.

### Phase 0: Foundations & Setup

This phase involves setting up the monorepo, containerized services, and continuous integration.

**1. Monorepo Structure:**
The project is organized into a monorepo with the following key directories:
- `/etl`: The data extraction, transformation, and loading pipeline.
- `/api`: The FastAPI application for serving the scores.
- `/web`: The Next.js frontend for the user dashboard.
- `/infra`: Docker Compose configuration for managing services.

**2. Infrastructure Setup with Docker Compose:**
The entire local development environment is managed by Docker Compose. The `infra/docker-compose.yml` file defines the following services:
- **PostgreSQL:** The primary database for storing structured data (e.g., wallet features, scores).
- **MinIO:** An S3-compatible object storage for raw, unstructured data fetched from the blockchain.
- **Apache Airflow:** The orchestrator for scheduling and running the daily ETL jobs.

To start all services, run:
```bash
docker-compose -f infra/docker-compose.yml up -d
```

**3. Continuous Integration (CI):**
A GitHub Actions workflow is defined in `.github/workflows/ci.yml`. This workflow should be configured to:
- Run linters and tests for the `etl`, `api`, and `web` components on every push and pull request.
- Build Docker images to ensure they are not broken.

### Phase 1: Data Pipeline (ETL)

This is the core component responsible for gathering and processing the data needed for scoring.

**1. Schema Definition:**
Define the database schema in PostgreSQL. The initial SQL script is located at `etl/sql/001_init_schema.sql`. This script should create the following tables:
- `wallets`: Stores basic information about each wallet address.
- `transactions`: Records all transactions for a tracked wallet.
- `positions`: Tracks a wallet's token and protocol positions.
- `features_daily`: An aggregated table storing the calculated scores for each component, updated daily.

**2. Data Extraction:**
- The ETL pipeline uses the **Alchemy API** to fetch raw transaction history and token balances for a given wallet.
- The client for this is implemented in `etl/src/wallet_etl/clients/alchemy.py`.
- Raw JSON responses from the API are backed up in MinIO object storage for auditing and reprocessing.

**3. Data Transformation and Loading:**
- The daily ETL job is defined in the Airflow DAG at `etl/dags/wallet_score_daily.py`.
- This DAG orchestrates a Python script (`etl/src/wallet_etl/pipeline/daily_job.py`) that:
    a. Fetches data from Alchemy.
    b. Stores the raw data in MinIO.
    c. Parses the raw data and calculates the five key metrics (Activity, Diversification, etc.).
    d. Inserts or updates the calculated scores in the `features_daily` table in PostgreSQL.

### Phase 2: Scoring Engine

This component implements the business logic for calculating the health score.

**1. Scoring Logic:**
- The core scoring logic will be implemented in a dedicated Python module, likely within the `etl` service.
- The formula for the MVP is a weighted average of the five components:
  ```
  score = 0.2*Activity + 0.2*Diversification + 0.2*Risk + 0.2*Profitability + 0.2*Stability
  ```
- Each component score should be normalized to a value between 0 and 1 before being weighted.

**2. Caching and Performance:**
- To ensure fast API responses, the daily scores are pre-calculated and stored in the `features_daily` table.
- For the API layer, a caching layer (e.g., Redis) can be added to cache the most frequently accessed wallet scores.

### Phase 3: API Development

The API exposes the calculated scores to the world.

**1. API Endpoints (FastAPI):**
The API is built using FastAPI and is defined in `api/app/main.py`. The following endpoints are required:
- `GET /score/{address}`: Returns the latest health score and its component breakdown for a given wallet address.
- `GET /history/{address}`: Provides a time-series of a wallet's score over the last 7 or 30 days.
- `POST /compare`: Accepts a list of wallet addresses and returns a comparison of their scores.

**2. Security and Scalability:**
- **Authentication:** Implement API key authentication to manage access.
- **Rate Limiting:** Protect the API from abuse.
- **Validation:** Use Pydantic models for request and response validation.

### Phase 4: Web Dashboard

A user-friendly interface for non-technical users.

**1. Frontend Framework:**
- The dashboard will be built with **Next.js** and **TypeScript**.
- UI components from a library like `shadcn/ui` will be used for a modern look and feel.
- Charts for visualizing score history will be created using `Recharts`.

**2. Key Features:**
- A search bar to look up any Ethereum wallet address.
- A "Score Card" view displaying the overall score and the five component scores.
- A historical trend chart showing the score's evolution over time.
- A comparison view to see multiple wallets side-by-side.

## 3. Deployment and Hosting

- **Web Frontend (Vercel):** The Next.js application can be seamlessly deployed to Vercel, which is optimized for this framework.
- **API & Database (Railway/Fly.io):** The FastAPI application, PostgreSQL database, and other backend services can be deployed using containers on a platform like Railway or Fly.io.
- **CI/CD:** The GitHub Actions workflow should be extended to automate deployments to the respective hosting platforms on merges to the `main` branch.

## 4. How to Use the Service

Once deployed, the service can be used in two ways:

**1. Via the API:**
Developers can integrate the API into their applications to programmatically fetch wallet scores.
```bash
curl -X GET "https://your-api-domain.com/score/0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae" \
     -H "Authorization: Bearer YOUR_API_KEY"
```

**2. Via the Web Dashboard:**
Users can simply navigate to the web application's URL, enter a wallet address, and view the health score and its detailed breakdown in a user-friendly format.
