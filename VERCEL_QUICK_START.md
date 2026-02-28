# Vercel Deployment - Quick Reference

## 🚀 Fastest Way to Deploy (5 minutes)

### 1. Push to Git
```bash
git add .
git commit -m "Deploy to Vercel"
git push origin main
```

### 2. Deploy to Vercel
1. Go to **[vercel.com/new](https://vercel.com/new)**
2. Click **"Import Project"**
3. Select your repository
4. Click **"Deploy"**

### 3. Set Environment Variable
1. Go to your project → **Settings** → **Environment Variables**
2. Add: `NEXT_PUBLIC_API_URL` = `https://your-api-url.com`
3. **Redeploy**

✅ **Done!** Your app is live at `https://your-app.vercel.app`

---

## 📋 What You Need

| Item | Where to Get | Required? |
|------|--------------|-----------|
| Vercel Account | [vercel.com/signup](https://vercel.com/signup) | ✅ Yes |
| Git Repository | GitHub/GitLab/Bitbucket | ✅ Yes |
| Backend API | Railway/Render | ⚠️ For full features |
| Database | Neon/Supabase | ⚠️ For full features |

---

## 🔧 Backend Setup (Optional but Recommended)

### Option 1: Railway (Easiest)
1. Sign up at [railway.app](https://railway.app)
2. Create new project from GitHub
3. Select `api` directory
4. Add environment variable: `DATABASE_URL`
5. Deploy!

### Option 2: Render
1. Sign up at [render.com](https://render.com)
2. New Web Service → Connect repository
3. Root: `api`, Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variable: `DATABASE_URL`
5. Deploy!

### Database: Neon (Free PostgreSQL)
1. Sign up at [neon.tech](https://neon.tech)
2. Create project
3. Copy connection string
4. Run migrations:
   ```bash
   psql "your-connection-string" < etl/sql/001_init_schema.sql
   psql "your-connection-string" < etl/sql/002_extraction_jobs.sql
   ```

---

## ⚡ CLI Deployment (Advanced)

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
cd /Users/lagnajitparida/Developer/wallet-health-score
vercel

# Production deployment
vercel --prod

# Set environment variable
vercel env add NEXT_PUBLIC_API_URL production
```

---

## 🛠️ Pre-Deployment Check

Run this before deploying:

```bash
cd web
./vercel-check.sh
```

Or manually:
```bash
# Test build
npm run build

# Test locally
npm start
```

---

## 🔑 Environment Variables

### Vercel (Frontend)
- `NEXT_PUBLIC_API_URL` - Your API endpoint

### Railway/Render (Backend)
- `DATABASE_URL` - PostgreSQL connection string
- `ALLOWED_ORIGINS` - Vercel URL (comma-separated)
- `ALCHEMY_API_KEY` - For blockchain data (optional)

---

## 📊 Free Tier Limits

| Service | Limit | Auto-Sleep? |
|---------|-------|-------------|
| **Vercel** | 100 GB bandwidth/month | ❌ No |
| **Railway** | $5 credit (~500 hrs) | ✅ Yes (1hr) |
| **Render** | 750 hrs/month | ✅ Yes (15min) |
| **Neon** | 10 GB storage | ✅ Yes (5min) |

---

## 🐛 Common Issues

### Build Fails
```bash
# Fix locally first
cd web
npm run build
# Check for errors and fix them
```

### API Connection Fails
- Check `NEXT_PUBLIC_API_URL` in Vercel
- Verify backend is running
- Check CORS settings in API
- Test API: `curl https://your-api.com/health`

### Environment Variables Not Working
- Redeploy after adding variables
- Check spelling (must start with `NEXT_PUBLIC_`)
- View logs: `vercel logs`

---

## 📚 Full Documentation

- **Quick Start**: [web/DEPLOYMENT.md](web/DEPLOYMENT.md)
- **Complete Guide**: [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md)
- **Checklist**: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)

---

## 🎯 Deployment Flow

```
┌─────────────────┐
│   Git Push      │
│   (main branch) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Vercel Auto    │
│  Deployment     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Build Next.js  │
│  (2-3 minutes)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Deploy to     │
│   Production    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Live! 🎉      │
│ your-app.vercel │
│     .app        │
└─────────────────┘
```

---

## 💡 Pro Tips

1. **Preview Deployments**: Every PR gets a unique URL
2. **Custom Domain**: Add free HTTPS domain in Settings
3. **Analytics**: Enable Vercel Analytics for free
4. **Monitoring**: Check build logs regularly
5. **Git Workflow**: Use branches for features, PR for review

---

## 🆘 Need Help?

- 💬 [Vercel Discord](https://vercel.com/discord)
- 📖 [Vercel Docs](https://vercel.com/docs)
- 🎓 [Next.js Deployment](https://nextjs.org/docs/deployment)
- 🐛 [GitHub Issues](https://github.com/yourusername/wallet-health-score/issues)

---

**Ready to deploy?** → [vercel.com/new](https://vercel.com/new) 🚀
