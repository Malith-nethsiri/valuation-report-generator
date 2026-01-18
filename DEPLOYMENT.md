# Deployment Guide

## Recommended Stack (Free/Low Cost)

| Component | Platform | Cost |
|-----------|----------|------|
| Frontend | **Vercel** | FREE |
| Backend | **Railway** | $5/mo (or free trial) |
| Database | **Neon.tech** | FREE tier (already set up) |

**Total Cost: ~$5/month**

---

## Step 1: Prepare Your Code

### 1.1 Generate New Credentials

Your old credentials were exposed. Generate new ones:

```bash
# Generate new SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 1.2 Rotate API Keys

1. **Neon.tech Database:**
   - Go to https://console.neon.tech
   - Reset your database password
   - Copy the new connection string

2. **Anthropic:**
   - Go to https://console.anthropic.com/settings/keys
   - Create new API key, delete old one

3. **Google Cloud:**
   - Go to https://console.cloud.google.com/apis/credentials
   - Create new API keys with restrictions:
     - Maps JavaScript API
     - Places API
     - Cloud Vision API
   - Restrict by HTTP referrer (your domains)

---

## Step 2: Deploy Backend to Railway

### 2.1 Push Code to GitHub

```bash
# Make sure you're in the project root
cd D:\project

# Initialize git if not already
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for deployment"

# Create GitHub repo and push
# Go to github.com, create new repo, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### 2.2 Deploy on Railway

1. **Go to Railway:** https://railway.app
2. **Sign in with GitHub**
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose your repository**
6. **Select the `backend` folder as root directory:**
   - Click on your service
   - Go to Settings → Root Directory
   - Set to: `backend`

### 2.3 Configure Environment Variables on Railway

Go to your service → **Variables** tab → Add these:

```
DATABASE_URL = postgresql://user:pass@host/db?sslmode=require
CORS_ORIGINS = https://your-app.vercel.app
GOOGLE_MAPS_API_KEY = your_new_key
GOOGLE_PLACES_API_KEY = your_new_key
GOOGLE_VISION_API_KEY = your_new_key
ANTHROPIC_API_KEY = your_new_key
SECRET_KEY = your_generated_secret_key
ENV = production
```

### 2.4 Get Your Backend URL

After deployment, Railway gives you a URL like:
```
https://your-app-production.up.railway.app
```

Copy this URL - you'll need it for the frontend.

---

## Step 3: Deploy Frontend to Vercel

### 3.1 Deploy on Vercel

1. **Go to Vercel:** https://vercel.com
2. **Sign in with GitHub**
3. **Click "Add New" → "Project"**
4. **Import your GitHub repository**
5. **Configure the project:**
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

### 3.2 Configure Environment Variables on Vercel

Go to Project Settings → **Environment Variables** → Add:

```
VITE_API_URL = https://your-app-production.up.railway.app
VITE_GOOGLE_MAPS_API_KEY = your_google_maps_key
```

### 3.3 Deploy

Click **Deploy**. Vercel will:
- Install dependencies
- Build the React app
- Deploy to their CDN

Your frontend URL will be:
```
https://your-app.vercel.app
```

---

## Step 4: Update CORS (Important!)

Go back to Railway and update `CORS_ORIGINS` to include your Vercel URL:

```
CORS_ORIGINS = https://your-app.vercel.app
```

Railway will auto-redeploy.

---

## Step 5: Verify Deployment

### 5.1 Check Backend Health

```bash
curl https://your-app-production.up.railway.app/api/health
```

Expected response:
```json
{"status": "success", "message": "API is healthy and running"}
```

### 5.2 Check Detailed Health

```bash
curl https://your-app-production.up.railway.app/api/health/detailed
```

Verify all services show "healthy" or "configured".

### 5.3 Test Frontend

1. Open https://your-app.vercel.app
2. Try to register a new account
3. Login and create a test report
4. Generate a DOCX file

---

## Custom Domain (Optional)

### For Frontend (Vercel)
1. Go to Project Settings → Domains
2. Add your domain (e.g., `valuations.yourdomain.com`)
3. Update DNS records as instructed

### For Backend (Railway)
1. Go to Service Settings → Networking → Custom Domain
2. Add your domain (e.g., `api.yourdomain.com`)
3. Update DNS records as instructed

Then update:
- `VITE_API_URL` in Vercel to use your custom API domain
- `CORS_ORIGINS` in Railway to include your custom frontend domain

---

## Alternative Deployment Options

### Option 2: All on Render (100% Free)

| Component | Platform | Cost |
|-----------|----------|------|
| Frontend | Render Static | FREE |
| Backend | Render Web Service | FREE (spins down after 15min inactivity) |
| Database | Neon.tech | FREE |

**Pros:** Completely free
**Cons:** Backend "cold starts" take 30-60 seconds after inactivity

### Option 3: DigitalOcean (More Control)

| Component | Platform | Cost |
|-----------|----------|------|
| Frontend | DigitalOcean App Platform | $3/mo |
| Backend | DigitalOcean App Platform | $5/mo |
| Database | Neon.tech | FREE |

**Total: ~$8/month**

### Option 4: AWS (Enterprise Scale)

| Component | Platform | Cost |
|-----------|----------|------|
| Frontend | S3 + CloudFront | ~$1/mo |
| Backend | ECS Fargate or Lambda | ~$10-50/mo |
| Database | RDS or Neon.tech | $15+/mo |

**Pros:** Highly scalable, full control
**Cons:** Complex setup, higher cost

---

## Troubleshooting

### Backend won't start
1. Check Railway logs: Service → Deployments → View Logs
2. Common issues:
   - Missing environment variables
   - Database connection failed
   - Port not binding correctly

### Frontend shows "Network Error"
1. Check browser console (F12)
2. Verify `VITE_API_URL` is correct
3. Check CORS_ORIGINS includes your frontend URL

### Database connection issues
1. Verify DATABASE_URL is correct
2. Check Neon.tech dashboard for connection limits
3. Ensure `?sslmode=require` is in the URL

### Google Maps not loading
1. Check API key restrictions in Google Cloud Console
2. Add your production domains to allowed referrers
3. Verify APIs are enabled (Maps JavaScript, Places, Vision)

---

## Rollback Procedures

### Railway (Backend)
1. Go to Deployments
2. Click on previous successful deployment
3. Click "Redeploy"

### Vercel (Frontend)
1. Go to Deployments
2. Find previous deployment
3. Click "..." → "Promote to Production"

### Database
```bash
# If you have a backup
psql $DATABASE_URL < backup.sql

# Or use Neon.tech's point-in-time recovery
# Go to Neon Console → Your Project → Branches → Restore
```

---

## Post-Deployment Checklist

- [ ] Backend health check passes
- [ ] Frontend loads without errors
- [ ] User can register and login
- [ ] Reports can be created and saved
- [ ] DOCX generation works
- [ ] OCR document upload works
- [ ] Google Maps loads correctly
- [ ] All API integrations working (Anthropic, Google Vision)

---

## Monitoring (Recommended)

Set up free monitoring:

1. **UptimeRobot** (free): https://uptimerobot.com
   - Monitor your `/api/health` endpoint
   - Get alerts when site is down

2. **Sentry** (free tier): https://sentry.io
   - Error tracking for both frontend and backend
   - See stack traces of production errors

---

## Security Reminders

- [ ] Never commit `.env` files to git
- [ ] Rotate API keys periodically
- [ ] Keep dependencies updated
- [ ] Enable 2FA on all service accounts (Railway, Vercel, GitHub, Neon)
- [ ] Restrict Google API keys by HTTP referrer
