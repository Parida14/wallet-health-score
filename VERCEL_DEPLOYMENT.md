# Vercel Deployment Guide

This guide explains how to deploy the Wallet Health Score application to Vercel's free tier.

## Important: Architecture Considerations

⚠️ **Vercel's free tier only supports frontend and serverless functions.** This project includes:
- ✅ **Next.js frontend** - Can be deployed to Vercel
- ❌ **FastAPI backend** - Requires separate hosting
- ❌ **PostgreSQL** - Requires separate database hosting
- ❌ **MinIO** - Requires separate object storage
- ❌ **Airflow** - Requires separate orchestration service

## Deployment Options

### Option 1: Frontend Only (Quick Demo)
Deploy just the Next.js frontend to Vercel with a mock API or connect to a separate backend.

### Option 2: Full Stack (Recommended)
- **Frontend**: Vercel (Free)
- **API**: Railway, Render, or Fly.io (Free tier available)
- **Database**: Neon, Supabase, or Railway (Free tier available)
- **Object Storage**: Cloudflare R2 or AWS S3 (Free tier available)

---

## Quick Start: Deploy Frontend to Vercel

### Prerequisites
1. [Vercel Account](https://vercel.com/signup) (free)
2. [Vercel CLI](https://vercel.com/docs/cli) (optional)
3. Git repository (GitHub/GitLab/Bitbucket)

### Method 1: Deploy via Vercel Dashboard (Easiest)

1. **Push your code to Git**
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

2. **Import to Vercel**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Click "Import Project"
   - Select your Git repository
   - Vercel will auto-detect Next.js

3. **Configure Settings**
   - **Root Directory**: Leave empty (Vercel will use the `web` directory automatically)
   - **Framework Preset**: Next.js
   - **Build Command**: `cd web && npm run build`
   - **Output Directory**: `web/.next`
   - **Install Command**: `cd web && npm install`

4. **Set Environment Variables**
   Add these in the Vercel project settings:
   ```
   NEXT_PUBLIC_API_URL=https://your-api-url.com
   ```
   
   For testing without a backend, you can use:
   ```
   NEXT_PUBLIC_API_URL=https://wallet-health-api.example.com
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes for build to complete
   - Your app will be live at `https://your-app.vercel.app`

### Method 2: Deploy via Vercel CLI

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy from project root**
   ```bash
   vercel
   ```
   
   Follow the prompts:
   - Set up and deploy: `Y`
   - Which scope: Select your account
   - Link to existing project: `N`
   - Project name: `wallet-health-score`
   - Directory: `./` (current directory)
   - Override settings: `Y`
   - Build Command: `cd web && npm run build`
   - Output Directory: `web/.next`
   - Install Command: `cd web && npm install`

4. **Set environment variables**
   ```bash
   vercel env add NEXT_PUBLIC_API_URL
   ```
   Enter your API URL when prompted.

5. **Deploy to production**
   ```bash
   vercel --prod
   ```

---

## Setting Up Backend Services (Free Tier)

### 1. Database: Neon (Free PostgreSQL)

1. Sign up at [neon.tech](https://neon.tech)
2. Create a new project
3. Copy the connection string:
   ```
   postgresql://user:password@host.neon.tech/dbname?sslmode=require
   ```
4. Run the schema migrations:
   ```bash
   psql "your-neon-connection-string" < etl/sql/001_init_schema.sql
   psql "your-neon-connection-string" < etl/sql/002_extraction_jobs.sql
   ```

**Free Tier Limits:**
- 10 GB storage
- 1 project
- Compute hibernates after 5 minutes of inactivity

### 2. API Backend: Railway (Free Tier)

1. Sign up at [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Configure the deployment:
   - **Root Directory**: `api`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Dockerfile**: Use the existing `api/Dockerfile`

5. Set environment variables in Railway:
   ```
   DATABASE_URL=your-neon-postgres-url
   MINIO_ENDPOINT=your-object-storage-url (optional)
   ALCHEMY_API_KEY=your-alchemy-key
   ```

6. Copy the Railway app URL (e.g., `https://your-app.railway.app`)

7. Update CORS in `api/app/main.py`:
   ```python
   allow_origins=[
       "http://localhost:3000",
       "https://your-app.vercel.app",  # Add your Vercel URL
   ]
   ```

8. Redeploy and note the API URL

**Railway Free Tier Limits:**
- $5 credit per month
- Apps sleep after 1 hour of inactivity
- 1 GB RAM, 1 vCPU

### Alternative: Render (Free Tier)

1. Sign up at [render.com](https://render.com)
2. Click "New" → "Web Service"
3. Connect your repository
4. Configure:
   - **Root Directory**: `api`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Render Free Tier Limits:**
- Apps spin down after 15 minutes of inactivity
- 750 hours per month (shared across all services)

### 3. Object Storage: Cloudflare R2 (Optional)

If you need object storage (for raw blockchain data):

1. Sign up at [cloudflare.com](https://cloudflare.com)
2. Go to R2 Storage
3. Create a bucket
4. Generate API tokens
5. Update the API config

**R2 Free Tier:**
- 10 GB storage
- No egress fees

---

## Update Vercel Environment Variable

After deploying your backend:

1. Go to your Vercel project
2. Settings → Environment Variables
3. Update `NEXT_PUBLIC_API_URL`:
   ```
   NEXT_PUBLIC_API_URL=https://your-api.railway.app
   ```
4. Redeploy frontend:
   ```bash
   vercel --prod
   ```

---

## CORS Configuration

Update your backend API to allow requests from Vercel:

```python
# In api/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",  # Allow all Vercel preview URLs
        "https://your-custom-domain.com",  # Your custom domain if any
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Custom Domain (Optional)

1. Go to Vercel Project → Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed
4. Vercel automatically provisions SSL certificates

---

## Monitoring Deployments

### View Build Logs
```bash
vercel logs your-deployment-url
```

### View Production Logs
```bash
vercel logs your-app.vercel.app --prod
```

### Check Build Status
- Dashboard: [vercel.com/dashboard](https://vercel.com/dashboard)
- Status page: [vercel-status.com](https://www.vercel-status.com)

---

## Troubleshooting

### Build Fails
1. Check build logs in Vercel dashboard
2. Verify `package.json` scripts are correct
3. Ensure all dependencies are in `package.json` (not just `devDependencies`)

### Environment Variables Not Working
- `NEXT_PUBLIC_*` vars must be set at BUILD time
- Redeploy after changing environment variables
- Check the variable name exactly matches

### API Connection Fails
1. Check CORS configuration in backend
2. Verify API URL in Vercel env vars
3. Check backend API is running (Railway/Render)
4. Test API directly: `curl https://your-api.railway.app/health`

### Page Not Found
- Ensure routes match between frontend and deployment
- Check `next.config.ts` for correct configuration
- Verify build completed successfully

---

## Cost Summary (Free Tier)

| Service | Free Tier | Limits |
|---------|-----------|--------|
| **Vercel** | Yes | 100 GB bandwidth, 6000 build minutes |
| **Railway** | $5 credit | ~500 hours/month, 1 GB RAM |
| **Neon** | Yes | 10 GB storage, compute hibernation |
| **Cloudflare R2** | Yes | 10 GB storage, 1M writes |

**Total Cost**: $0/month for light usage

---

## Next Steps

1. ✅ Deploy frontend to Vercel
2. ✅ Deploy backend to Railway/Render
3. ✅ Set up Neon PostgreSQL
4. ✅ Update environment variables
5. ✅ Test the application
6. 📊 Monitor usage and performance
7. 🚀 Scale as needed

---

## Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [Railway Documentation](https://docs.railway.app)
- [Neon Documentation](https://neon.tech/docs)
- [Render Documentation](https://render.com/docs)

---

## Need Help?

- Vercel Support: [vercel.com/support](https://vercel.com/support)
- Community: [Vercel Discord](https://vercel.com/discord)
- Documentation: [vercel.com/docs](https://vercel.com/docs)
