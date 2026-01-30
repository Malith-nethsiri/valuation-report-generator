# Deployment Guide

## Recommended Stack (100% Free)

| Component | Platform      | Cost | Notes                              |
| --------- | ------------- | ---- | ---------------------------------- |
| Frontend  | **Vercel**    | FREE | Perfect for React/Vite, global CDN |
| Backend   | **Render**    | FREE | Cold starts after 15min idle       |
| Database  | **Neon.tech** | FREE | Already configured                 |

**Total Cost: $0/month**

### Important: Cold Start Warning ⚠️

Render's free tier spins down your backend after 15 minutes of inactivity. The first request after idle takes **30-60 seconds** to wake up. This is normal for free hosting.

**Mitigation:** Set up a free uptime monitor (UptimeRobot) to ping your `/api/health` endpoint every 14 minutes to keep it warm.

---

## Step 1: Prepare Your Code

### 1.1 Generate New Credentials

Generate secure credentials for production:

```bash
# Generate new SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 1.2 Rotate API Keys (If Previously Exposed)

1. **Neon.tech Database:**
   - Go to https://console.neon.tech
   - Reset your database password if needed
   - Copy the new connection string

2. **Anthropic:**
   - Go to https://console.anthropic.com/settings/keys
   - Create new API key if needed

3. **Google Cloud:**
   - Go to https://console.cloud.google.com/apis/credentials
   - Create new API keys with restrictions:
     - Maps JavaScript API
     - Places API
     - Cloud Vision API
   - Restrict by HTTP referrer (your production domains)

---

## Step 2: Deploy Backend to Render

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
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### 2.2 Create render.yaml (Blueprint)

Create a `render.yaml` file in your project root for easy deployment:

```yaml
services:
  - type: web
    name: property-valuation-api
    runtime: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: SECRET_KEY
        sync: false
      - key: CORS_ORIGINS
        sync: false
      - key: GOOGLE_MAPS_API_KEY
        sync: false
      - key: GOOGLE_PLACES_API_KEY
        sync: false
      - key: GOOGLE_VISION_API_KEY
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: ENV
        value: production
    plan: free
    healthCheckPath: /api/health
```

### 2.3 Deploy on Render

1. **Go to Render:** https://render.com
2. **Sign in with GitHub**
3. **Click "New +" → "Web Service"**
4. **Connect your GitHub repository**
5. **Configure the service:**
   - **Name:** `property-valuation-api`
   - **Root Directory:** `backend`
   - **Runtime:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free`

### 2.4 Configure Environment Variables on Render

Go to your service → **Environment** tab → Add these:

```
DATABASE_URL = postgresql://user:pass@host/db?sslmode=require
SECRET_KEY = your_generated_secret_key
CORS_ORIGINS = https://your-app.vercel.app
GOOGLE_MAPS_API_KEY = your_key
GOOGLE_PLACES_API_KEY = your_key
GOOGLE_VISION_API_KEY = your_key
ANTHROPIC_API_KEY = your_key
ENV = production
```

### 2.5 Get Your Backend URL

After deployment, Render gives you a URL like:
```
https://property-valuation-api.onrender.com
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
VITE_API_URL = https://property-valuation-api.onrender.com
VITE_GOOGLE_MAPS_API_KEY = your_google_maps_key
```

### 3.3 Deploy

Click **Deploy**. Vercel will:
- Install dependencies
- Build the React app
- Deploy to their global CDN

Your frontend URL will be:
```
https://your-app.vercel.app
```

---

## Step 4: Update CORS (Important!)

Go back to Render and update `CORS_ORIGINS` to include your Vercel URL:

```
CORS_ORIGINS = https://your-app.vercel.app
```

Render will auto-redeploy.

---

## Step 5: Set Up Uptime Monitor (Prevent Cold Starts)

To minimize cold starts, set up a free ping service:

1. **Go to UptimeRobot:** https://uptimerobot.com (free account)
2. **Create new monitor:**
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** Property Valuation API
   - **URL:** `https://property-valuation-api.onrender.com/api/health`
   - **Monitoring Interval:** 5 minutes (or every 14 minutes to stay under limits)
3. **Save**

This keeps your backend warm by pinging it regularly.

---

## Step 6: Verify Deployment

### 6.1 Check Backend Health

```bash
curl https://property-valuation-api.onrender.com/api/health
```

Expected response:
```json
{"status": "success", "message": "API is healthy and running"}
```

### 6.2 Check Detailed Health

```bash
curl https://property-valuation-api.onrender.com/api/health/detailed
```

Verify all services show "healthy" or "configured".

### 6.3 Test Frontend

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

### For Backend (Render)
1. Go to Service Settings → Custom Domains
2. Add your domain (e.g., `api.yourdomain.com`)
3. Update DNS records as instructed

Then update:
- `VITE_API_URL` in Vercel to use your custom API domain
- `CORS_ORIGINS` in Render to include your custom frontend domain

---

## Alternative Deployment Options

### Option 2: Railway (If Budget Allows - $5/month)

| Component | Platform  | Cost  |
| --------- | --------- | ----- |
| Frontend  | Vercel    | FREE  |
| Backend   | Railway   | $5/mo |
| Database  | Neon.tech | FREE  |

**Pros:** No cold starts, better performance, better developer experience
**Cons:** Costs $5/month

### Option 3: Fly.io (Free but Complex)

| Component | Platform  | Cost           |
| --------- | --------- | -------------- |
| Frontend  | Vercel    | FREE           |
| Backend   | Fly.io    | FREE (limited) |
| Database  | Neon.tech | FREE           |

**Pros:** More control, Docker-based
**Cons:** Reduced free tier, more complex setup, still has cold starts

### Option 4: All on Render (Simpler)

| Component | Platform           | Cost |
| --------- | ------------------ | ---- |
| Frontend  | Render Static      | FREE |
| Backend   | Render Web Service | FREE |
| Database  | Neon.tech          | FREE |

**Pros:** Single platform for frontend and backend
**Cons:** Vercel is faster/better for frontend

### Option 5: DigitalOcean (Paid, More Control)

| Component | Platform                  | Cost  |
| --------- | ------------------------- | ----- |
| Frontend  | Vercel                    | FREE  |
| Backend   | DigitalOcean App Platform | $5/mo |
| Database  | Neon.tech                 | FREE  |

**Total: $5/month**

---

## Known Limitations (Free Tier)

### Render Free Tier Limits
- ⚠️ **Cold starts:** 30-60 seconds after 15min idle
- ⚠️ **512MB RAM:** May be tight for heavy PDF generation (WeasyPrint)
- ⚠️ **Compute hours:** 750 hours/month (enough for one service)
- ⚠️ **Bandwidth:** 100GB/month outbound

### Vercel Free Tier Limits
- ✅ **100GB bandwidth/month** - Very generous
- ✅ **Unlimited deployments**
- ⚠️ **Serverless function timeout:** 10 seconds (not applicable - we're using Render for API)

### Neon Free Tier Limits
- ✅ **0.5GB storage** - Sufficient for most projects
- ✅ **Unlimited databases**
- ⚠️ **Compute hours:** 191.9 hours/month (auto-suspends after 5min idle)

---

## Troubleshooting

### Backend won't start
1. Check Render logs: Service → Logs
2. Common issues:
   - Missing environment variables
   - Database connection failed (check DATABASE_URL)
   - Port binding issue (must use `$PORT`)

### Backend is slow (cold start)
1. This is normal for Render free tier
2. Set up UptimeRobot to ping every 5-14 minutes
3. First request after idle will be slow

### Frontend shows "Network Error"
1. Check browser console (F12)
2. Verify `VITE_API_URL` is correct (no trailing slash)
3. Check CORS_ORIGINS includes your frontend URL exactly
4. Wait for backend to wake up (cold start)

### Database connection issues
1. Verify DATABASE_URL is correct
2. Ensure `?sslmode=require` is in the URL
3. Check Neon.tech dashboard - database may be suspended (auto-resumes)

### Google Maps not loading
1. Check API key restrictions in Google Cloud Console
2. Add your production domains to allowed referrers:
   - `https://your-app.vercel.app/*`
   - `https://*.vercel.app/*` (for preview deployments)
3. Verify APIs are enabled (Maps JavaScript, Places, Vision)

### PDF/Document generation fails
1. Check Render logs for memory errors
2. 512MB may not be enough for large documents
3. Consider upgrading to paid tier if this is critical

---

## Rollback Procedures

### Render (Backend)
1. Go to Events → Find previous successful deploy
2. Click "Rollback to this deploy"

### Vercel (Frontend)
1. Go to Deployments
2. Find previous deployment
3. Click "..." → "Promote to Production"

### Database
```bash
# Use Neon.tech's branching feature for point-in-time recovery
# Go to Neon Console → Your Project → Branches → Create branch from specific point
```

---

## Post-Deployment Checklist

- [ ] Backend health check passes (`/api/health`)
- [ ] Frontend loads without errors
- [ ] User can register and login
- [ ] Reports can be created and saved
- [ ] DOCX generation works
- [ ] OCR document upload works (if using Google Vision)
- [ ] Google Maps loads correctly
- [ ] UptimeRobot monitoring is configured
- [ ] CORS is properly configured

---

## Monitoring (Recommended)

### Free Monitoring Tools

1. **UptimeRobot** (free): https://uptimerobot.com
   - Monitor your `/api/health` endpoint
   - Get alerts when site is down
   - Keeps backend warm (prevents cold starts)

2. **Sentry** (free tier): https://sentry.io
   - Error tracking for both frontend and backend
   - Already configured in your project
   - Set `SENTRY_DSN` environment variable

3. **Render Dashboard**
   - Built-in metrics and logs
   - Monitor memory usage (important for free tier)

---

## Security Reminders

- [ ] Never commit `.env` files to git
- [ ] Rotate API keys periodically
- [ ] Keep dependencies updated
- [ ] Enable 2FA on all service accounts (Render, Vercel, GitHub, Neon)
- [ ] Restrict Google API keys by HTTP referrer
- [ ] Use strong, unique `SECRET_KEY` in production
