# Project Overview: Wallet Score Health API

## Project Goal
The "Wallet Score Health API" aims to provide a comprehensive analysis and scoring of the on-chain health of cryptocurrency wallets. This involves collecting relevant blockchain data, processing it through an ETL pipeline, calculating a health score, and exposing this information via an API and a web interface.

## Architecture

The project follows a monorepo structure and is composed of three main services:

1.  **ETL (Extract, Transform, Load) Pipeline:**
    *   **Purpose:** Responsible for data ingestion, cleaning, transformation, and loading into the data store.
    *   **Technology:** Python, Apache Airflow (for orchestration), Alchemy API (for data fetching).
    *   **Data Flow:** Fetches raw blockchain data from Alchemy, stores it temporarily in MinIO (object storage), processes it, and then loads the refined data into PostgreSQL.
    *   **Status:** This is the most developed component, with a daily job defined in Airflow and a placeholder for the core scoring logic.

2.  **API (Application Programming Interface):**
    *   **Purpose:** To expose the wallet health scores and related data to external applications and the web frontend.
    *   **Technology:** FastAPI (Python).
    *   **Status:** Currently a placeholder.

3.  **Web Dashboard:**
    *   **Purpose:** A user-friendly interface to visualize wallet health scores and interact with the system.
    *   **Technology:** Next.js (React/TypeScript).
    *   **Status:** Currently a placeholder.

## Key Technologies

*   **Backend/ETL:** Python
*   **API Framework:** FastAPI
*   **Web Framework:** Next.js (React)
*   **Orchestration:** Apache Airflow
*   **Database:** PostgreSQL
*   **Object Storage:** MinIO
*   **Containerization:** Docker, Docker Compose
*   **Data Source:** Alchemy API

## Current Status

*   The ETL pipeline is functional for data ingestion and processing, with the core scoring logic awaiting implementation.
*   The API and Web components are currently set up as basic project structures (placeholders).
*   The entire local development environment is managed via `docker-compose.yml`.

## Setup and Deployment

The project utilizes Docker Compose for setting up the local development environment, including PostgreSQL, MinIO, and Airflow. Detailed setup instructions can be found in the respective `README.md` files within each service directory and the `infra` directory.
