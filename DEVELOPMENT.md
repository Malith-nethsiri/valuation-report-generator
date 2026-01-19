# Development Guide

This guide explains how to develop and test changes locally without affecting the production website.

## Architecture Overview

```
Production:
  Frontend: https://valuerpro.online (Vercel)
  Backend:  https://api.valuerpro.online (Render)
  Database: Neon PostgreSQL

Local Development:
  Frontend: http://localhost:5173 (Vite dev server)
  Backend:  http://localhost:8000 (Uvicorn)
  Database: Same Neon DB (or local PostgreSQL)
```

---

## Local Development Setup

### Prerequisites

- Node.js 18+
- Python 3.11+
- Git

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/Malith-nethsiri/valuation-report-generator.git
cd valuation-report-generator
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (copy from example)
cp .env.example .env
# Edit .env with your credentials
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local for local development
echo "VITE_API_URL=http://localhost:8000" > .env.local
echo "VITE_GOOGLE_MAPS_API_KEY=your_key_here" >> .env.local
```

### 4. Run Locally

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate  # or source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Access at: http://localhost:5173

---

## Development Workflow

### Branch Strategy

```
main (production)
  └── develop (integration)
       ├── feature/feature-name
       ├── fix/bug-description
       └── hotfix/urgent-fix
```

### Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test locally:**
   - Run both frontend and backend locally
   - Test all affected functionality
   - Check browser console for errors

3. **Commit changes:**
   ```bash
   git add .
   git commit -m "feat: description of changes"
   ```

4. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub.

5. **Preview deployment (automatic):**
   - Vercel creates a preview URL for each PR
   - Test the preview before merging

6. **Merge to main:**
   - After review, merge PR to main
   - Production auto-deploys

---

## Environment Variables

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require

# Security
SECRET_KEY=your-secret-key-here

# CORS (comma-separated for multiple origins)
CORS_ORIGINS=http://localhost:5173,https://valuerpro.online

# Google APIs
GOOGLE_MAPS_API_KEY=your_key
GOOGLE_PLACES_API_KEY=your_key
GOOGLE_VISION_API_KEY=your_key

# AI
ANTHROPIC_API_KEY=your_key

# Environment
ENV=development

# Optional
SENTRY_DSN=your_sentry_dsn
REDIS_URL=redis://localhost:6379
SENDGRID_API_KEY=your_key
```

### Frontend (.env.local)

```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_MAPS_API_KEY=your_key
```

---

## Testing

### Backend Tests

```bash
cd backend
pytest
pytest --cov=app  # with coverage
```

### Frontend Tests

```bash
cd frontend
npm test
npm run test:coverage  # with coverage
```

### Manual Testing Checklist

Before merging to production, test:

- [ ] User registration and login
- [ ] Create new report
- [ ] Save and load draft
- [ ] OCR document upload
- [ ] Generate DOCX
- [ ] Google Maps integration
- [ ] All form steps complete without errors

---

## Database Migrations

### Creating a Migration

When you add/modify columns in `models.py`:

1. Create a migration script in `backend/migrations/`
2. Test locally first
3. Run on production Neon database

### Running Migrations

**Locally:**
```bash
cd backend
python migrations/your_migration.py
```

**Production (Neon):**
- Go to Neon Console → SQL Editor
- Run the SQL statements manually
- Or run the migration script with production DATABASE_URL

---

## Deployment

### Automatic Deployment

- **Push to `main`** → Auto-deploys to production
- **Push to feature branch** → Creates Vercel preview

### Manual Deployment

**Frontend (Vercel):**
```bash
cd frontend
npm run build
# Vercel auto-deploys on push
```

**Backend (Render):**
- Push to main
- Render auto-deploys

### Rollback

**Vercel:**
1. Go to Deployments
2. Find previous deployment
3. Click "..." → "Promote to Production"

**Render:**
1. Go to Events
2. Find previous deploy
3. Click "Rollback"

---

## Adding Custom Domain (valuerpro.online)

### Step 1: Configure Vercel (Frontend)

1. Go to [Vercel Dashboard](https://vercel.com)
2. Select your project
3. Go to **Settings** → **Domains**
4. Add domain: `valuerpro.online`
5. Add domain: `www.valuerpro.online`

### Step 2: Configure Render (Backend API)

1. Go to [Render Dashboard](https://render.com)
2. Select your backend service
3. Go to **Settings** → **Custom Domains**
4. Add domain: `api.valuerpro.online`

### Step 3: Configure DNS in Squarespace

Go to Squarespace → Domains → DNS → Add these records:

**For Frontend (valuerpro.online):**
| Type | Host | Value | TTL |
|------|------|-------|-----|
| A | @ | 76.76.21.21 | 3600 |
| CNAME | www | cname.vercel-dns.com | 3600 |

**For Backend API (api.valuerpro.online):**
| Type | Host | Value | TTL |
|------|------|-------|-----|
| CNAME | api | [your-app].onrender.com | 3600 |

### Step 4: Update Environment Variables

**Render (Backend):**
```
CORS_ORIGINS=https://valuerpro.online,https://www.valuerpro.online
```

**Vercel (Frontend):**
```
VITE_API_URL=https://api.valuerpro.online
```

### Step 5: Update CSP in vercel.json

Update `frontend/vercel.json` to allow the new API domain:
```json
"connect-src 'self' https://api.valuerpro.online https://*.onrender.com ..."
```

### Step 6: Wait for DNS Propagation

- DNS changes take 5 minutes to 48 hours
- Check status: https://dnschecker.org

---

## Troubleshooting

### CORS Errors

- Check `CORS_ORIGINS` in Render includes your frontend URL
- Check `vercel.json` CSP allows your API domain
- Clear browser cache

### Database Connection Issues

- Verify `DATABASE_URL` is correct
- Check Neon dashboard for connection limits
- Ensure `?sslmode=require` is in the URL

### Build Failures

- Check Vercel/Render logs
- Run build locally: `npm run build` / `pip install -r requirements.txt`
- Check for missing dependencies

### Cold Start Slowness

- Render free tier sleeps after 15min
- Set up UptimeRobot to ping every 14min
- First request after sleep takes 30-60s

---

## Useful Commands

```bash
# Git
git status
git log --oneline -10
git diff

# Backend
uvicorn app.main:app --reload
pytest
pip freeze > requirements.txt

# Frontend
npm run dev
npm run build
npm test

# Database
# Connect to Neon via psql
psql "postgresql://user:pass@host/db?sslmode=require"
```

---

## Contact & Resources

- **Repository:** https://github.com/Malith-nethsiri/valuation-report-generator
- **Frontend (Vercel):** https://valuerpro.online
- **Backend (Render):** https://api.valuerpro.online
- **Database (Neon):** https://console.neon.tech
