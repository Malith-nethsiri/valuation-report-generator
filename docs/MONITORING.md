# Monitoring Setup Guide

This document describes how to set up monitoring for the Property Valuation Platform using UptimeRobot and Sentry.

## Overview

The platform uses two monitoring systems:
- **UptimeRobot**: External uptime monitoring (free tier available)
- **Sentry**: Error tracking and performance monitoring (already integrated)

---

## UptimeRobot Setup

UptimeRobot monitors your endpoints externally and alerts you when they become unavailable.

### Step 1: Create Account

1. Go to [UptimeRobot](https://uptimerobot.com/)
2. Create a free account (50 monitors included)
3. Verify your email address

### Step 2: Add Health Check Monitor

1. Click **"+ Add New Monitor"**
2. Configure the monitor:

| Setting | Value |
|---------|-------|
| Monitor Type | HTTP(s) |
| Friendly Name | Property Valuation API - Health |
| URL | `https://your-api.railway.app/api/health` |
| Monitoring Interval | 5 minutes |

3. Click **"Create Monitor"**

### Step 3: Add Additional Monitors (Recommended)

#### API Authentication Endpoint
```
Monitor Type: HTTP(s)
Friendly Name: Property Valuation API - Auth
URL: https://your-api.railway.app/api/auth/me
Expected Status Code: 401 (Unauthorized expected without token)
Interval: 5 minutes
```

#### Frontend Application
```
Monitor Type: HTTP(s)
Friendly Name: Property Valuation Frontend
URL: https://your-app.vercel.app
Interval: 5 minutes
```

### Step 4: Configure Alert Contacts

1. Go to **"My Settings"** > **"Alert Contacts"**
2. Add your preferred notification methods:
   - **Email** (default, free)
   - **Slack** (via webhook)
   - **SMS** (paid plans)
   - **Discord** (via webhook)

#### Slack Integration

1. Create an Incoming Webhook in Slack
2. Add it as an Alert Contact in UptimeRobot:
   - Type: Slack
   - URL: Your Slack webhook URL

#### Discord Integration

1. Create a Webhook in your Discord server
2. Add as Alert Contact with URL: `YOUR_DISCORD_WEBHOOK/slack`

### Step 5: Create Public Status Page (Optional)

1. Go to **"Status Pages"**
2. Click **"Add Status Page"**
3. Configure:
   - Name: Property Valuation Platform Status
   - Custom Domain (optional)
   - Select monitors to display
4. Share the status page URL with stakeholders

---

## Health Check Endpoint Details

The backend exposes a health check endpoint at `/api/health`:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-15T10:30:00Z",
  "components": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### Component Status Meanings

| Status | Description |
|--------|-------------|
| `healthy` | Component is functioning normally |
| `degraded` | Component is working but with issues |
| `unhealthy` | Component is not functioning |

---

## Sentry Integration (Already Configured)

Sentry is integrated for error tracking and performance monitoring.

### Backend (FastAPI)

Sentry captures:
- Unhandled exceptions
- HTTP errors (4xx/5xx)
- Slow database queries
- External API failures (Google Maps, SendGrid)

### Frontend (React)

Sentry captures:
- JavaScript errors
- React component errors
- Network request failures
- Performance issues

### Accessing Sentry Dashboard

1. Log in to [Sentry](https://sentry.io/)
2. Select your project
3. View:
   - **Issues**: Error reports grouped by type
   - **Performance**: Transaction timing
   - **Releases**: Deployment tracking

### Setting Up Sentry Alerts

1. Go to **Alerts** > **Create Alert Rule**
2. Recommended alerts:

#### High Error Rate Alert
```
When: event.type:error
Triggers: More than 10 events in 1 hour
Action: Send email notification
```

#### New Error Alert
```
When: A new issue is created
Filter: level:error OR level:fatal
Action: Send Slack notification
```

---

## Recommended Monitoring Dashboard

### Key Metrics to Track

| Metric | Tool | Threshold |
|--------|------|-----------|
| API Uptime | UptimeRobot | > 99.5% |
| Response Time | UptimeRobot | < 2s average |
| Error Rate | Sentry | < 1% of requests |
| Unique Errors | Sentry | < 5 new issues/day |

### Response Time Benchmarks

| Endpoint | Expected Response |
|----------|-------------------|
| `/api/health` | < 100ms |
| `/api/auth/login` | < 500ms |
| `/api/reports` (list) | < 1s |
| `/api/reports/{id}/generate` | < 5s |
| `/api/ocr/extract` | < 30s |

---

## Incident Response

### When UptimeRobot Alerts

1. **Check Sentry** for related errors
2. **Check Railway logs**: `railway logs --tail`
3. **Check database** connectivity via Railway dashboard
4. **Check Redis** connectivity via Railway dashboard
5. **Verify external services** (Google Maps, SendGrid)

### Common Issues and Solutions

#### Database Connection Errors
```bash
# Check Neon database status
# Visit: https://console.neon.tech/
```

#### Redis Connection Errors
```bash
# Check Railway Redis plugin status
# Visit: https://railway.app/project/{your-project}
```

#### High Memory Usage
- Review recent deployments
- Check for memory leaks in Sentry
- Consider scaling Railway resources

---

## Cost Considerations

### Free Tier Limits

| Service | Free Tier |
|---------|-----------|
| UptimeRobot | 50 monitors, 5-min intervals |
| Sentry | 5k errors/month, 10k transactions |

### Scaling Recommendations

When traffic grows:
1. Upgrade UptimeRobot for 1-min monitoring intervals
2. Upgrade Sentry for more error quota
3. Consider adding APM (Application Performance Monitoring)

---

## Maintenance

### Weekly Tasks
- Review Sentry error trends
- Check UptimeRobot response time graphs
- Clear resolved Sentry issues

### Monthly Tasks
- Review and update alert thresholds
- Test notification channels
- Archive old incidents

---

## Quick Reference

### URLs

| Service | URL |
|---------|-----|
| UptimeRobot Dashboard | https://uptimerobot.com/dashboard |
| Sentry Dashboard | https://sentry.io/ |
| Railway Dashboard | https://railway.app/ |
| Vercel Dashboard | https://vercel.com/dashboard |
| Neon Console | https://console.neon.tech/ |

### Environment Variables

Ensure these are set in production:

```env
# Backend (Railway)
SENTRY_DSN=your-sentry-dsn
REDIS_URL=your-redis-url
DATABASE_URL=your-database-url

# Frontend (Vercel)
VITE_SENTRY_DSN=your-frontend-sentry-dsn
VITE_API_URL=your-api-url
```
