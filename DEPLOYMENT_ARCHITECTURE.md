# Deployment Architecture - Vercel Free Tier

## Overview

This document explains how to deploy the Wallet Health Score application using free-tier services.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER'S BROWSER                          │
│                    https://your-app.vercel.app                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      VERCEL (Frontend)                          │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Next.js 15 Application                    │    │
│  │  • Server Components                                   │    │
│  │  • Client Components (React)                          │    │
│  │  • Static Assets (CSS, Images)                        │    │
│  │  • API Routes (Proxied)                               │    │
│  └─────────────────────┬──────────────────────────────────┘    │
│                        │                                        │
│  Environment:          │                                        │
│  • NEXT_PUBLIC_API_URL ────┐                                   │
└────────────────────────────┼────────────────────────────────────┘
                             │
                             │ HTTP/HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   RAILWAY / RENDER (Backend)                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                  FastAPI Application                   │    │
│  │                                                        │    │
│  │  Endpoints:                                           │    │
│  │  • GET  /health                                       │    │
│  │  • GET  /score/{address}                              │    │
│  │  • GET  /history/{address}                            │    │
│  │  • POST /compare                                      │    │
│  │  • POST /extract/{address}                            │    │
│  │  • GET  /extract/status/{job_id}                      │    │
│  └─────────────────────┬──────────────────────────────────┘    │
│                        │                                        │
│  Environment:          │                                        │
│  • DATABASE_URL        │                                        │
│  • ALLOWED_ORIGINS     │                                        │
│  • ALCHEMY_API_KEY     │                                        │
└────────────────────────┼────────────────────────────────────────┘
                         │
                         │ PostgreSQL Protocol
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      NEON / SUPABASE (Database)                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                    PostgreSQL 15                       │    │
│  │                                                        │    │
│  │  Tables:                                              │    │
│  │  • features_daily (wallet scores)                     │    │
│  │  • extraction_jobs (job tracking)                     │    │
│  │  • raw_transactions (optional)                        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Features:                                                      │
│  • Auto-sleep after 5 min                                      │
│  • 10 GB storage                                               │
│  • Connection pooling                                          │
└─────────────────────────────────────────────────────────────────┘

                             │
                             │ (Optional)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              CLOUDFLARE R2 / AWS S3 (Object Storage)            │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                   MinIO-compatible                     │    │
│  │  • Raw blockchain data                                 │    │
│  │  • Transaction archives                                │    │
│  │  • ETL artifacts                                       │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘

                             │
                             │ (For scheduled jobs)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AIRFLOW (Optional/Self-hosted)               │
│  • Daily ETL pipeline                                           │
│  • Score recalculation                                          │
│  • Data cleanup                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Service Responsibilities

### 1. Vercel (Frontend) - FREE
- **Hosts**: Next.js web application
- **Handles**: 
  - Server-side rendering (SSR)
  - Static site generation (SSG)
  - Client-side routing
  - Image optimization
  - API route proxying
- **Limits**: 
  - 100 GB bandwidth/month
  - 6,000 build minutes
- **Auto-scales**: Yes

### 2. Railway/Render (Backend API) - FREE with limits
- **Hosts**: FastAPI Python application
- **Handles**:
  - REST API endpoints
  - Database queries
  - On-demand ETL jobs
  - Score calculations
- **Limits**:
  - Railway: $5/month credit (~500 hours)
  - Render: 750 hours/month
- **Auto-sleep**: Yes (Railway: 1hr, Render: 15min)

### 3. Neon/Supabase (Database) - FREE
- **Hosts**: PostgreSQL database
- **Handles**:
  - Wallet scores storage
  - Job tracking
  - Historical data
- **Limits**: 10 GB storage
- **Auto-sleep**: Yes (5 minutes of inactivity)

### 4. Cloudflare R2 (Object Storage) - FREE (Optional)
- **Hosts**: Raw blockchain data
- **Handles**:
  - Transaction archives
  - ETL artifacts
  - Backups
- **Limits**: 10 GB storage, 1M writes
- **Auto-sleep**: No

## Data Flow

### User Request Flow
```
1. User visits https://your-app.vercel.app
2. Vercel serves Next.js app (SSR/SSG)
3. Browser loads React components
4. User searches for wallet address
5. Frontend calls API: GET /score/{address}
6. Railway/Render wakes up (if sleeping)
7. FastAPI queries Neon database
8. Database returns wallet scores
9. API formats and returns JSON
10. Frontend displays scores with charts
```

### On-Demand Extraction Flow
```
1. User clicks "Extract" for new wallet
2. Frontend: POST /extract/{address}
3. API validates address
4. Creates job in database
5. Spawns background thread
6. Thread calls Alchemy API
7. Fetches transaction data
8. Calculates health scores
9. Stores in database
10. Updates job status
11. Frontend polls: GET /extract/status/{job_id}
12. Shows results when complete
```

## Cost Breakdown (Free Tier)

| Service | Free Tier | Monthly Cost | Auto-Sleep |
|---------|-----------|--------------|------------|
| **Vercel** | 100 GB bandwidth | $0 | No |
| **Railway** | $5 credit | $0 | Yes (1hr) |
| **Neon** | 10 GB storage | $0 | Yes (5min) |
| **Cloudflare R2** | 10 GB storage | $0 | No |
| **Total** | - | **$0** | - |

### Usage Estimates (Light Traffic)

**Assumptions:**
- 1,000 page views/month
- 500 API calls/month
- 50 new wallet extractions/month

**Expected Costs:**
- ✅ Well within Vercel limits
- ✅ ~100 hours Railway compute (20% of credit)
- ✅ <1 GB database storage
- ✅ <100 MB object storage

## Scaling Considerations

### When You Might Need Paid Plans

| Metric | Free Limit | Upgrade If... |
|--------|------------|---------------|
| **Bandwidth** | 100 GB/month | >100K page views |
| **API Calls** | ~10K/month | High-frequency requests |
| **Database** | 10 GB | >1M wallet records |
| **Compute** | ~500 hrs | 24/7 availability needed |

### Optimization Tips

1. **Enable Caching**
   - Cache wallet scores for 1 hour
   - Use Vercel Edge caching
   - Implement Redis for hot data

2. **Reduce API Calls**
   - Batch requests where possible
   - Use stale-while-revalidate
   - Implement client-side caching

3. **Database Optimization**
   - Index frequently queried fields
   - Archive old historical data
   - Use materialized views

4. **Prevent Auto-Sleep**
   - Use cron-job.org to ping every 14 minutes
   - Or upgrade to paid tier for 24/7 uptime

## Alternative Architectures

### Option A: Vercel Serverless Functions (Not Recommended)
❌ Python FastAPI doesn't run well on Vercel's Node.js runtime
❌ Database connections are challenging with serverless
❌ ETL jobs too long for serverless limits (10s)

### Option B: All-in-One (Railway)
✅ Deploy both frontend and backend on Railway
❌ Uses more compute credits
❌ Less optimized than Vercel for Next.js

### Option C: Fly.io (Alternative)
✅ Similar to Railway with persistent VMs
✅ Better for always-on services
❌ More complex setup

## Recommended Setup (Balanced)

```
Frontend:  Vercel (best Next.js support)
Backend:   Railway (easy Python deployment)
Database:  Neon (serverless PostgreSQL)
Storage:   Skip for MVP, add R2 later
Airflow:   Skip for MVP, use on-demand extraction
```

## Migration Path

### Stage 1: MVP (Current Guide)
- Free tier services
- On-demand extraction only
- Manual database management

### Stage 2: Growth
- Paid Vercel Pro ($20/month) - More bandwidth
- Railway Team ($20/month) - 24/7 uptime
- Scheduled jobs via GitHub Actions

### Stage 3: Scale
- Dedicated server (DigitalOcean/AWS)
- Managed database (AWS RDS/GCP Cloud SQL)
- CDN for static assets
- Load balancer for API

## Security Considerations

1. **Environment Variables**
   - Never commit `.env` files
   - Use Vercel's encrypted storage
   - Rotate API keys regularly

2. **CORS Configuration**
   - Whitelist specific origins only
   - Don't use wildcards in production

3. **Rate Limiting**
   - Implement on API endpoints
   - Use Vercel Edge Middleware

4. **Database Access**
   - Use connection pooling
   - Enable SSL for connections
   - Rotate database passwords

## Monitoring & Observability

1. **Vercel Analytics** (Free)
   - Page views
   - Web Vitals
   - Real User Monitoring

2. **Railway/Render Logs**
   - API request logs
   - Error tracking
   - Performance metrics

3. **Neon Monitoring**
   - Query performance
   - Storage usage
   - Connection count

4. **External Tools** (Optional)
   - Sentry for error tracking
   - LogRocket for session replay
   - BetterStack for uptime monitoring

## Summary

This architecture provides:
- ✅ **$0/month** for light usage
- ✅ **Easy deployment** (< 30 minutes)
- ✅ **Auto-scaling** frontend
- ✅ **Modern stack** (Next.js + FastAPI)
- ✅ **Production-ready** with HTTPS
- ⚠️ **Auto-sleep** for backend (acceptable for MVP)
- ⚠️ **Limited compute** (upgrade as you grow)

**Perfect for**: MVPs, side projects, demos, portfolios
**Not ideal for**: 24/7 critical services, high-traffic apps

---

For implementation details, see:
- [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md) - Full deployment guide
- [VERCEL_QUICK_START.md](VERCEL_QUICK_START.md) - Quick reference
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Complete checklist
