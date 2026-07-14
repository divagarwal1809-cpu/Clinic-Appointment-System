# ClinicFlow Deployment Guide

This guide walks you through deploying ClinicFlow's **frontend** on Netlify, **backend** on Render, and **database** on Neon (serverless PostgreSQL).

---

## Architecture Overview

```
┌──────────────────┐      HTTPS / JSON      ┌──────────────────┐
│   Netlify (CDN)  │ ────────────────────▶   │  Render (Python) │
│   Static SPA     │                         │  FastAPI + Uvi   │
│   index.html     │ ◀──────────────────── │  cors: *         │
│   style.css      │                         │                  │
│   app.js         │                         └────────┬─────────┘
└──────────────────┘                                  │
                                                      │ DATABASE_URL
                                                      ▼
                                              ┌──────────────────┐
                                              │   Neon (PgSQL)   │
                                              │   Serverless DB  │
                                              └──────────────────┘
```

---

## 1. Database — Neon (PostgreSQL)

### Step 1: Create a Neon Project
1. Go to [https://neon.tech](https://neon.tech) and sign up / log in.
2. Click **"New Project"** → name it `clinicflow`.
3. Select a region close to your Render deployment (e.g., `us-east-1`).
4. Once created, Neon will show you a **connection string** like:
   ```
   postgresql://user:password@ep-xxxxx.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```
5. **Copy this string** — you will need it for the backend.

### Step 2: Initialize Tables
The FastAPI backend auto-creates tables on startup via `init_db()`. Once the backend is deployed with the `DATABASE_URL` set, the tables will be created automatically.

To seed data, you can run the data loader script locally with the Neon URL:
```bash
DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require" python -m src.load_data
```

---

## 2. Backend — Render (FastAPI)

### Step 1: Prepare Your Repository
Ensure these files exist at the project root:
- `requirements.txt` — includes `psycopg2-binary`, `fastapi`, `uvicorn`, `sqlalchemy`, `anthropic`
- `app/app.py` — the entry point

### Step 2: Create a Render Web Service
1. Go to [https://render.com](https://render.com) and sign up / log in.
2. Click **"New" → "Web Service"**.
3. Connect your GitHub repository.
4. Configure:
   - **Name:** `clinicflow-api`
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free (or Starter for production)

### Step 3: Set Environment Variables
In the Render dashboard, add these environment variables:
| Variable | Value |
|---|---|
| `DATABASE_URL` | Your Neon connection string from Step 1 |
| `ANTHROPIC_API_KEY` | Your Anthropic API key (optional — falls back to mock) |
| `PYTHONPATH` | `.` |

### Step 4: Deploy
Click **"Create Web Service"**. Render will build and deploy automatically. Note the public URL (e.g., `https://clinicflow-api.onrender.com`).

---

## 3. Frontend — Netlify (Static SPA)

### Step 1: Update API URL
Before deploying, update the `API` constant in `frontend/app.js` to point to your Render backend URL:
```javascript
const API = 'https://clinicflow-api.onrender.com';
```

### Step 2: Deploy to Netlify
**Option A: Netlify CLI**
```bash
npm install -g netlify-cli
cd frontend
netlify deploy --prod --dir=.
```

**Option B: Netlify Dashboard**
1. Go to [https://app.netlify.com](https://app.netlify.com).
2. Click **"Add new site" → "Deploy manually"**.
3. Drag and drop the `frontend/` folder.
4. Netlify will assign a URL like `https://clinicflow.netlify.app`.

### Step 3: Verify
The `netlify.toml` file in the `frontend/` directory is already configured to redirect all routes to `index.html` for SPA compatibility.

---

## 4. Post-Deployment Checklist

| Check | How |
|---|---|
| ✅ API is online | Visit `https://your-render-url.onrender.com/docs` |
| ✅ Database connected | Check Render logs for `Connected to PostgreSQL` |
| ✅ Frontend loads | Visit your Netlify URL |
| ✅ Theme toggle works | Click the sun/moon icon in the topbar |
| ✅ Booking flow works | Fill out the combined booking & intake form |
| ✅ AI summary works | Staff dashboard → click "Summarize" on an intake |
| ✅ Safety scrubber active | Verify no clinical terms appear in summaries |

---

## 5. Environment Variables Summary

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | Neon PostgreSQL connection string |
| `ANTHROPIC_API_KEY` | No | Anthropic Claude API key; falls back to mock summarizer if unset |
| `PYTHONPATH` | Yes (Render) | Set to `.` for module resolution |

---

## 6. Local Development

For local development, no environment variables are needed — the system defaults to SQLite (`clinic.db`) and the mock AI summarizer:

```powershell
# 1. Setup
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 2. Seed database
python -m src.load_data

# 3. Start backend
python -m app.app

# 4. Start frontend (separate terminal)
python -m http.server 8080 --directory frontend
```

Then open [http://127.0.0.1:8080](http://127.0.0.1:8080).
