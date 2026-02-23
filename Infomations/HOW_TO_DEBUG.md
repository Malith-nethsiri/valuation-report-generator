# How to Debug Your Application

A practical guide for debugging your SaaS product when things break.

---

## What You Need to Learn

| Skill | Why It Matters | Time to Learn |
|-------|---------------|---------------|
| Reading error logs | Know WHAT broke | 1-2 hours |
| Using browser DevTools | See frontend errors | 1-2 hours |
| Basic terminal commands | Check server status | 1 hour |
| Understanding error messages | Know WHERE to look | Practice |

---

## Part 1: Reading Backend Error Logs

### Where to Find Logs

**On Render (your current backend host):**
1. Go to https://dashboard.render.com
2. Click on your backend service
3. Click "Logs" tab
4. You'll see real-time logs

**On Railway (if you switch):**
1. Go to https://railway.app/dashboard
2. Click your project → service
3. Click "Logs" in the sidebar

### Understanding Error Messages

**Example 1: Database Error**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server failed
```
**What it means:** Can't connect to Neon database
**How to fix:**
- Check if DATABASE_URL is correct in environment variables
- Check if Neon dashboard shows database is running
- Database might be "sleeping" (cold start) - wait and retry

---

**Example 2: Missing Environment Variable**
```
ValueError: SECRET_KEY environment variable is not set
```
**What it means:** Server can't start because SECRET_KEY is missing
**How to fix:**
- Go to Render/Railway dashboard
- Find "Environment Variables" section
- Add the missing variable

---

**Example 3: Import Error**
```
ModuleNotFoundError: No module named 'some_package'
```
**What it means:** A Python package is missing
**How to fix:**
- Add package to `requirements.txt`
- Redeploy

---

**Example 4: API Error**
```
HTTPException: 401 Unauthorized - Could not validate credentials
```
**What it means:** User's login token is invalid or expired
**How to fix:** This is usually normal - user needs to login again

---

**Example 5: Validation Error**
```
pydantic.error_wrappers.ValidationError: 1 validation error for PropertyCreate
land_extent_acres: value is not a valid float
```
**What it means:** Frontend sent wrong data format
**Where to look:** Check the frontend form that sends this data

---

### Log Levels to Know

| Level | Meaning | Action Needed? |
|-------|---------|----------------|
| DEBUG | Detailed info | No - just for development |
| INFO | Normal operation | No - things working |
| WARNING | Something unusual | Maybe - check it |
| ERROR | Something failed | Yes - needs attention |
| CRITICAL | App might crash | Yes - urgent |

---

## Part 2: Reading Frontend Errors

### Using Browser Developer Tools

**How to open DevTools:**
- Windows: Press `F12` or `Ctrl + Shift + I`
- Mac: Press `Cmd + Option + I`
- Or: Right-click page → "Inspect"

### Console Tab (Most Important)

This shows JavaScript errors. Look for RED text.

**Example 1: Network Error**
```
POST https://your-api.com/api/reports 500 (Internal Server Error)
```
**What it means:** Backend returned an error
**How to fix:** Check backend logs for the actual error

---

**Example 2: CORS Error**
```
Access to XMLHttpRequest at 'https://api.com' from origin 'https://app.com'
has been blocked by CORS policy
```
**What it means:** Backend doesn't allow requests from your frontend URL
**How to fix:**
- Add your frontend URL to `CORS_ORIGINS` in backend environment variables
- Example: `CORS_ORIGINS=https://your-app.vercel.app`

---

**Example 3: Undefined Error**
```
TypeError: Cannot read properties of undefined (reading 'map')
```
**What it means:** Code tried to use `.map()` on something that doesn't exist
**Where to look:** The file and line number shown in the error

---

### Network Tab (Second Most Important)

Shows all API calls between frontend and backend.

**How to use:**
1. Open DevTools → Network tab
2. Do the action that's failing (e.g., submit form)
3. Look for RED requests (failed)
4. Click the failed request
5. Look at "Response" tab to see error message

**What to look for:**
- Status 401: User not logged in / token expired
- Status 403: User doesn't have permission
- Status 404: API endpoint doesn't exist
- Status 422: Data validation failed (wrong format)
- Status 500: Backend crashed - check backend logs

---

## Part 3: Common Problems and Solutions

### Problem: "App is slow"

**Check:**
1. Network tab - are API calls slow? (>2 seconds)
2. If yes, check backend logs for slow database queries
3. Neon cold start? First request after inactivity is slow (normal)

---

### Problem: "Login not working"

**Check:**
1. Network tab - what's the error code?
2. 401? Token expired, user needs to re-login
3. 500? Check backend logs
4. No response? Backend might be down

---

### Problem: "Form submission fails"

**Check:**
1. Console tab - any JavaScript errors?
2. Network tab - what does the API return?
3. Look at "Request" tab to see what data was sent
4. Look at "Response" tab to see what error came back

---

### Problem: "Page shows blank/white"

**Check:**
1. Console tab - look for red errors
2. Usually a JavaScript crash
3. Error will show file name and line number

---

### Problem: "Data not saving"

**Check:**
1. Network tab - was API call made?
2. If no call: frontend bug (form not submitting)
3. If call made but failed: check response error
4. If call succeeded (200): check if page needs refresh

---

## Part 4: How to Describe Problems (To Me or a Developer)

When asking for help, include:

### Template:
```
**What I was trying to do:**
[e.g., "Create a new property report"]

**What happened instead:**
[e.g., "Got an error message saying 'Failed to save'"]

**Error message (exact text):**
[Copy-paste the EXACT error from console or logs]

**Steps to reproduce:**
1. Go to [page]
2. Click [button]
3. Fill in [fields]
4. Error appears

**Screenshots:**
[If helpful, include screenshots of the error]
```

### Good Example:
```
**What I was trying to do:**
Save a new property report with 2 buildings

**What happened instead:**
Red error box appeared saying "Internal server error"

**Error from browser console:**
POST https://api.example.com/api/reports 500 (Internal Server Error)
Response: {"detail": "cannot serialize JSON: 'buildings' is not valid"}

**Error from Render logs:**
TypeError: Object of type Decimal is not JSON serializable
File "app/main.py", line 892, in create_report

**Steps to reproduce:**
1. Go to /new-report
2. Fill in property details
3. Add building with floor area "150.5"
4. Click Submit
```

### Bad Example:
```
"App doesn't work, please fix"
```
(This tells me nothing - I can't help without details)

---

## Part 5: Quick Reference Commands

### Check if backend is running
```bash
# In browser, visit:
https://your-backend-url.com/api/health
# Should return: {"status": "healthy", ...}
```

### Check Neon database
1. Go to https://console.neon.tech
2. Click your project
3. "Dashboard" shows if database is active
4. "Tables" lets you see your data

### Check Vercel frontend
1. Go to https://vercel.com/dashboard
2. Click your project
3. "Deployments" shows recent deploys
4. Click a deployment to see build logs

---

## Part 6: Setting Up Error Monitoring (Sentry)

This automatically emails you when errors happen.

### Step 1: Create Sentry Account
1. Go to https://sentry.io
2. Sign up (free tier is enough)
3. Create a new project → Select "FastAPI"

### Step 2: Add to Backend
Add to `requirements.txt`:
```
sentry-sdk[fastapi]
```

Add to `main.py` (at the top):
```python
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=0.1,  # 10% of requests traced
)
```

### Step 3: Add Environment Variable
In Render/Railway, add:
```
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```
(Get this URL from Sentry dashboard)

### Step 4: Test It Works
Add temporary code to cause an error:
```python
@app.get("/api/test-sentry")
async def test_sentry():
    raise Exception("Test error for Sentry")
```

Visit that URL, then check Sentry dashboard - you should see the error.

---

## Part 7: Learning Resources

### Free Courses (Recommended Order)

1. **Browser DevTools** (1-2 hours)
   - https://developer.chrome.com/docs/devtools/
   - Focus on: Console, Network tabs

2. **Reading Python Errors** (30 mins)
   - https://realpython.com/python-traceback/
   - Learn to read stack traces

3. **Basic Terminal** (1 hour)
   - Just learn: `cd`, `ls`, `cat`, `tail`
   - You'll mostly use dashboard UIs anyway

### Practice Exercise

1. Open your app in browser
2. Open DevTools (F12)
3. Go to Network tab
4. Use your app normally
5. Watch the API calls happen
6. Try to find a failed request (if any)
7. Read the error response

---

## Checklist: What You Should Know

After reading this guide, you should be able to:

- [ ] Open browser DevTools
- [ ] Find errors in Console tab
- [ ] See failed API calls in Network tab
- [ ] Access Render/Railway logs
- [ ] Understand common error codes (401, 403, 404, 500)
- [ ] Describe a bug clearly for someone to help you
- [ ] Set up Sentry for automatic error alerts

---

## When to Ask for Help vs. Fix Yourself

### Fix Yourself:
- Environment variable missing (easy to add)
- CORS error (add URL to config)
- User can't login (token expired - normal)
- Neon cold start slowness (normal, just wait)

### Ask for Help:
- Error message you don't understand
- Same error keeps happening
- Data is being corrupted
- Security-related errors
- Errors in code logic

---

*Remember: Most bugs are simple once you know where to look. The error message usually tells you exactly what's wrong - you just need to learn how to read it.*
