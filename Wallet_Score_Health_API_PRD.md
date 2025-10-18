# Wallet Score Health API — Product Requirements Document (MVP)

## 1. Overview
The **Wallet Score Health API** provides a standardized way to assess the on-chain "health" of a crypto wallet based on activity, diversification, risk profile, profitability, and stability.
It helps users, analysts, and dApps quickly understand a wallet’s behavior and risk level through a single, explainable score.

**Product Type:** Developer API + Analytics Dashboard  
**Version:** MVP (v0.1)  
**Owner:** Lagnajit Parida
**Date:** October 2025

---

## 2. Problem Statement
There is no unified metric today that quantifies the **health and quality** of an on-chain wallet.
DeFi protocols, analytics tools, and investors need a fast, data-driven way to:
- Assess user quality for airdrops, credit, or loyalty.
- Compare wallet behavior across activity and diversification.
- Monitor score trends and identify risk early.

---

## 3. Objectives
- Provide a **numerical score (0–100)** representing wallet health.
- Expose a **public API** returning score + component breakdown.
- Offer a **minimal dashboard** for score lookup and comparison.
- Automate **daily refreshes** using blockchain data pipelines.

---

## 4. Key Metrics (Score Components)

| Component | Description | Example Metrics |
|---|---|---|
| **Activity** | Wallet engagement and frequency | Tx count, unique contracts, active days |
| **Diversification** | Portfolio spread across tokens/protocols | Token diversity index |
| **Risk** | Exposure to volatile or leveraged positions | % volatile assets, borrow ratio |
| **Profitability** | Realized & unrealized profit/loss | % gain/loss, avg PnL per tx |
| **Stability** | Holding behavior & asset rotation | Stablecoin ratio, avg hold duration |

**Formula (MVP weighting):**
```
score = 0.2*Activity + 0.2*Diversification + 0.2*Risk + 0.2*Profitability + 0.2*Stability
```

---

## 5. Users & Use Cases

### Primary Users
- **Developers / Analysts:** use API for wallet evaluation.
- **DeFi teams:** filter genuine, active wallets for airdrops or incentives.
- **Investors / Traders:** track portfolio health trends.

### Example Use Cases
- “Show top 100 healthiest wallets in Uniswap.”
- “Compare my wallet vs. a whale’s wallet.”
- “Monitor risk score of trader addresses over time.”

---

## 6. Scope

### In Scope (MVP)
- Ethereum mainnet wallets
- Core components: Activity, Diversification, Risk, Profitability, Stability
- REST API endpoints
- ETL data pipeline (daily)
- Dashboard (Next.js + Recharts)

### Out of Scope (Post-MVP)
- L2s (Arbitrum, Optimism, Base)
- Predictive analytics / alerts
- Social integrations (ENS, Farcaster)
- ML-driven scoring

---

## 7. Functional Requirements

### API Endpoints
**GET /score/{address}**  
Returns current wallet score and component breakdown.

**GET /history/{address}**  
Returns time-series of wallet scores (7D, 30D).

**POST /compare**  
Compare multiple wallet addresses.

**Sample Response**
```json
{
  "address": "0x123...",
  "wallet_score": 78.4,
  "components": {
    "activity": 0.82,
    "diversification": 0.74,
    "risk": 0.68,
    "profitability": 0.90,
    "stability": 0.70
  },
  "last_updated": "2025-10-09T12:00:00Z"
}
```

---

## 8. Non-Functional Requirements

| Area | Requirement |
|---|---|
| **Performance** | API latency < 3s per wallet |
| **Availability** | 99% uptime |
| **Scalability** | Handle 10K wallet queries/day |
| **Security** | API key auth + rate limiting |
| **Storage** | Postgres for structured data; MinIO for raw blobs |
| **Observability** | Request logging, error tracking (Sentry), uptime checks |

---

## 9. Tech Stack
- **ETL:** Python + Airflow + Alchemy API / Covalent  
- **Storage:** Postgres (RDS) + MinIO  
- **API:** FastAPI + Redis cache  
- **Web:** Next.js 15 + shadcn/ui + Recharts  
- **Infra:** Docker Compose + GitHub Actions  
- **Hosting:** Vercel (web), Railway/Fly.io (API + DB)

---

## 10. Data Model (MVP)
- **wallets** (address PK, chain, first_seen, last_seen, tags[])
- **transactions** (hash PK, address FK, timestamp, gas_spent_usd, tx_type, contracts_involved[])
- **positions** (address FK, token, protocol, balance, usd_value, last_updated)
- **features_daily** (address FK, date, activity_score, diversification_score, risk_score, profitability_score, stability_score, total_score)

---

## 11. Development Roadmap

- [ ] **Phase 0 – Foundations (Week 1)**  
  - [ ] Monorepo setup (`/etl`, `/api`, `/web`, `/infra`)  
  - [ ] Docker Compose: Postgres + MinIO + Airflow + API  
  - [ ] Env config + GitHub Actions CI/CD  

- [ ] **Phase 1 – Data Pipeline (Weeks 2–3)**  
  - [ ] Define schemas (`wallets`, `transactions`, `positions`, `features_daily`)  
  - [ ] Fetch data via Alchemy/Covalent APIs  
  - [ ] Store raw JSON in MinIO + normalized tables in Postgres  
  - [ ] Compute derived features (tx count, diversification, PnL, etc.)  
  - [ ] Daily Airflow DAG + data validation  

- [ ] **Phase 2 – Scoring Engine (Weeks 4–5)**  
  - [ ] Implement scoring logic (`wallet_score.py`)  
  - [ ] Cache precomputed scores (materialized view or Redis)  
  - [ ] Unit tests for metrics  

- [ ] **Phase 3 – API (Weeks 6–7)**  
  - [ ] FastAPI endpoints `/score`, `/history`, `/compare`  
  - [ ] API key auth + caching + logs  

- [ ] **Phase 4 – Dashboard (Week 8)**  
  - [ ] Next.js frontend: search wallet, show score card + trends  
  - [ ] Comparison view  
  - [ ] Deploy to Vercel (web) + Railway (API)  

- [ ] **Launch Checklist**  
  - [ ] Seed 100 test wallets  
  - [ ] Validate scores manually  
  - [ ] README + API docs (OpenAPI)  
  - [ ] Demo video / GIF  

---

## 12. Success Criteria
- Working API serving valid scores for 100+ wallets  
- Dashboard for wallet lookup and comparison  
- Latency < 5s per wallet query  
- Component breakdown visible and explainable  
- Deployed public beta (API + dashboard)

---

## 13. Future Enhancements
- Support for multi-chain (Arbitrum, Optimism, Base)  
- Integration with ENS/Farcaster data  
- Machine learning–based behavioral scoring  
- Alerting system (“Wallet score dropped 20%”)

---

## 14. Open Questions
- What baseline period defines “recent” activity (30D vs 90D)?
- How to estimate unrealized PnL consistently across protocols?
- Should scores be sector-aware (DeFi vs NFT-heavy wallets)?

---

## 15. Changelog
- v0.1 (MVP): Initial PRD drafted
