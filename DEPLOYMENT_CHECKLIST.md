# Vercel Deployment Checklist

Use this checklist to ensure a smooth deployment to Vercel.

## Pre-Deployment

- [ ] Code is committed to Git
- [ ] Code is pushed to GitHub/GitLab/Bitbucket
- [ ] All dependencies are in `package.json`
- [ ] Build works locally (`npm run build`)
- [ ] Environment variables are documented

## Vercel Setup

- [ ] Vercel account created
- [ ] Repository connected to Vercel
- [ ] Project imported in Vercel dashboard
- [ ] Framework preset set to Next.js
- [ ] Build settings configured (should auto-detect from `vercel.json`)

## Environment Variables

- [ ] `NEXT_PUBLIC_API_URL` added in Vercel dashboard
- [ ] Environment variable set for Production
- [ ] Environment variable set for Preview (optional)
- [ ] Environment variable set for Development (optional)

## Backend Services (Required for Full Functionality)

### Database
- [ ] PostgreSQL database provisioned (Neon/Supabase/Railway)
- [ ] Connection string obtained
- [ ] Database schema migrated (`001_init_schema.sql`)
- [ ] Extraction jobs table created (`002_extraction_jobs.sql`)
- [ ] Test connection successful

### API Backend
- [ ] FastAPI deployed to Railway/Render/Fly.io
- [ ] `DATABASE_URL` environment variable set in backend
- [ ] `ALLOWED_ORIGINS` includes Vercel URL
- [ ] API health endpoint accessible: `/health`
- [ ] CORS configuration updated for Vercel domain

### Optional Services
- [ ] MinIO/R2 storage configured (if needed)
- [ ] Alchemy API key configured
- [ ] Airflow set up (if needed for scheduled jobs)

## Deployment

- [ ] Initial deployment triggered
- [ ] Build completed successfully
- [ ] Deployment preview URL works
- [ ] Production deployment created
- [ ] Custom domain added (optional)
- [ ] DNS configured for custom domain (optional)
- [ ] SSL certificate provisioned (automatic)

## Post-Deployment Testing

- [ ] Homepage loads correctly
- [ ] Wallet search functionality works
- [ ] API calls succeed (check browser console)
- [ ] No CORS errors in browser console
- [ ] All routes accessible
- [ ] Mobile responsive design works
- [ ] Performance is acceptable (check Vercel Analytics)

## Monitoring & Optimization

- [ ] Vercel Analytics enabled
- [ ] Error tracking configured
- [ ] Build logs reviewed
- [ ] Runtime logs reviewed
- [ ] Performance metrics checked
- [ ] Core Web Vitals reviewed

## Documentation

- [ ] README updated with deployment info
- [ ] Environment variables documented
- [ ] Architecture diagram updated (optional)
- [ ] API endpoints documented
- [ ] Known issues documented (if any)

## Rollback Plan

- [ ] Previous deployment URL saved
- [ ] Rollback process understood
- [ ] Team knows how to revert deployment

## Team Access

- [ ] Team members invited to Vercel project
- [ ] Access levels configured appropriately
- [ ] Deployment notifications configured

## Cost Management (Free Tier)

- [ ] Bandwidth usage monitored (<100 GB/month)
- [ ] Build minutes tracked (<6000 minutes/month)
- [ ] Serverless function executions monitored
- [ ] Backend service usage tracked (Railway/Render limits)
- [ ] Database storage monitored (10 GB limit on Neon)

## Security

- [ ] Environment variables use Vercel's encrypted storage
- [ ] No secrets committed to Git
- [ ] `.env` files in `.gitignore`
- [ ] API keys rotated if exposed
- [ ] HTTPS enforced (automatic on Vercel)

## Continuous Deployment

- [ ] Auto-deployment enabled for main branch
- [ ] Preview deployments enabled for PRs
- [ ] Branch protection rules configured (optional)
- [ ] Git workflow documented

---

## Quick Commands

### Deploy from CLI
```bash
vercel --prod
```

### Check deployment status
```bash
vercel ls
```

### View logs
```bash
vercel logs
```

### Add environment variable
```bash
vercel env add NEXT_PUBLIC_API_URL production
```

### Pull environment variables locally
```bash
vercel env pull .env.local
```

---

## Common Issues & Solutions

### Build Fails
- Check build logs in Vercel dashboard
- Verify all dependencies are listed in `package.json`
- Ensure build command is correct
- Test build locally: `npm run build`

### Environment Variables Not Applied
- Redeploy after adding/changing env vars
- Check variable names start with `NEXT_PUBLIC_`
- Verify values in Vercel dashboard

### API Connection Fails
- Check CORS configuration in backend
- Verify `NEXT_PUBLIC_API_URL` is correct
- Test API endpoint directly
- Check backend logs for errors

### Page Not Found / 404
- Verify routes are correctly defined
- Check `next.config.ts` configuration
- Ensure build completed successfully

---

## Support Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Discord](https://vercel.com/discord)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [Railway Docs](https://docs.railway.app)
- [Neon Docs](https://neon.tech/docs)

---

**Last Updated**: February 2026
