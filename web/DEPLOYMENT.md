# Deploying to Vercel - Quick Start

## Prerequisites
- Vercel account (free): [vercel.com/signup](https://vercel.com/signup)
- Git repository (GitHub, GitLab, or Bitbucket)

## Step-by-Step Guide

### 1. Push to Git Repository

```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Ready for Vercel deployment"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/yourusername/wallet-health-score.git

# Push
git push -u origin main
```

### 2. Deploy to Vercel

#### Option A: Using Vercel Dashboard (Recommended)

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click "Import Project"
3. Select your Git repository
4. Vercel will auto-detect the configuration from `vercel.json`
5. Add environment variable:
   - Key: `NEXT_PUBLIC_API_URL`
   - Value: Your API URL (or use a demo API for now)
6. Click "Deploy"

#### Option B: Using Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Deploy to production
vercel --prod
```

### 3. Configure Environment Variables

In Vercel Dashboard → Settings → Environment Variables, add:

```
NEXT_PUBLIC_API_URL=https://your-api-url.com
```

Or via CLI:

```bash
vercel env add NEXT_PUBLIC_API_URL production
# Enter your API URL when prompted
```

### 4. Redeploy

After adding environment variables, redeploy:

```bash
vercel --prod
```

Or push to your git repository to trigger auto-deployment.

## Important Notes

### Project Structure
This is a **monorepo** with multiple services. Vercel will only deploy the **Next.js frontend** located in the `web/` directory.

### Backend Services
The following services need to be deployed separately:
- **API (FastAPI)**: Deploy to Railway, Render, or Fly.io
- **Database (PostgreSQL)**: Use Neon, Supabase, or Railway
- **Object Storage**: Use Cloudflare R2 or AWS S3 (optional)

See [VERCEL_DEPLOYMENT.md](../VERCEL_DEPLOYMENT.md) for complete backend setup instructions.

### Free Tier Limits

**Vercel Free Tier:**
- 100 GB bandwidth per month
- 6,000 build minutes per month
- Unlimited preview deployments
- Automatic HTTPS

## Testing Your Deployment

Once deployed, you can:

1. Visit your Vercel URL: `https://your-app.vercel.app`
2. Check the build logs in Vercel Dashboard
3. Monitor performance in Vercel Analytics

## Troubleshooting

### Build Fails

Check the build logs in Vercel dashboard. Common issues:
- Missing dependencies in `package.json`
- Node version mismatch
- Build command errors

### Environment Variables Not Working

- Ensure variables start with `NEXT_PUBLIC_` for client-side access
- Redeploy after adding/changing environment variables
- Check variable values in Vercel dashboard

### API Connection Issues

- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check CORS configuration in your backend API
- Test API endpoint directly with curl or Postman

## Custom Domain

To add a custom domain:

1. Go to Vercel Project → Settings → Domains
2. Add your domain
3. Update DNS records as instructed
4. SSL certificate is automatically provisioned

## Automatic Deployments

Vercel automatically deploys:
- **Production**: When you push to `main` branch
- **Preview**: For every pull request and branch

## Local Development

To test locally before deploying:

```bash
cd web

# Install dependencies
npm install

# Set environment variable
export NEXT_PUBLIC_API_URL=http://localhost:8000

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Next Steps

1. ✅ Deploy frontend to Vercel
2. 🔧 Deploy backend services (see [VERCEL_DEPLOYMENT.md](../VERCEL_DEPLOYMENT.md))
3. 🔗 Update `NEXT_PUBLIC_API_URL` to point to your backend
4. 🧪 Test the application
5. 📊 Monitor with Vercel Analytics

## Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Next.js Deployment Guide](https://nextjs.org/docs/deployment)
- [Full Deployment Guide](../VERCEL_DEPLOYMENT.md)

## Support

- Vercel Discord: [vercel.com/discord](https://vercel.com/discord)
- GitHub Issues: Create an issue in your repository
- Documentation: [vercel.com/docs](https://vercel.com/docs)
