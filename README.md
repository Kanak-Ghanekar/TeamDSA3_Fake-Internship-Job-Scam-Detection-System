# Scam Detect AI — Fake Job & Internship Detection System

**Graphura India Private Limited**

Full-stack web application for detecting fake job postings and fraudulent internship
offers. Every score, chart, and table in this app is computed live — from the text
you give it, a server-side page scrape, and Supabase lookups. There is no embedded
sample dataset and no local fallback scoring.

---

## Project Structure

```
ScamDetectAI/
├── backend/                     ← FastAPI Python backend
│   ├── main.py                  ← App entry point, CORS, exception handlers
│   ├── requirements.txt         ← Python dependencies
│   ├── .env                     ← Supabase keys & table names
│   ├── api/
│   │   ├── router.py            ← Mounts all route modules
│   │   └── routes/
│   │       ├── analyze.py       ← POST /analyze, POST /analyze-url
│   │       ├── domain.py        ← POST /domain-check
│   │       ├── recruiter.py     ← POST /recruiter-check, GET /recruiters
│   │       ├── report.py        ← POST /report, GET /reports
│   │       ├── dashboard.py     ← GET  /dashboard
│   │       ├── auth.py          ← POST /auth/login, /auth/register
│   │       └── db_health.py     ← GET  /db-health
│   ├── models/
│   │   └── schemas.py           ← All Pydantic request/response models
│   ├── services/
│   │   ├── analysis_service.py  ← Composite scam scorer (keywords + live domain/recruiter/report lookups)
│   │   ├── scrape_service.py    ← Server-side job-URL scraper (JSON-LD + meta + heuristic extraction)
│   │   ├── domain_service.py    ← Domain trust lookup (Supabase domain_reputation)
│   │   ├── recruiter_service.py ← Recruiter verification (Supabase recruiter_profiles)
│   │   ├── report_service.py    ← Scam report submission (Supabase scam_reports)
│   │   ├── dashboard_service.py ← Live aggregate stats (Supabase job_posts + scam_reports)
│   │   └── health_service.py    ← DB connectivity check
│   ├── core/
│   │   ├── config.py            ← Settings (Supabase, CORS)
│   │   ├── security.py          ← JWT auth, test accounts
│   │   ├── startup.py           ← Startup validation
│   │   └── logging.py           ← Structured logging setup
│   └── db/
│       └── supabase.py          ← Supabase client factory
│
└── frontend/                    ← Vanilla HTML/CSS/JS frontend
    ├── index.html               ← Dashboard — live stats, donut chart, trend, job feed
    ├── scamanalysis.html        ← Analyze a job: paste a URL (auto-scraped) or enter manually
    ├── recruiter.html           ← Recruiter & domain check + live database browser
    ├── report.html              ← Submit scam report + live community feed/table
    ├── style.css                ← Gold & navy theme stylesheet
    └── scamdetectai.js          ← Shared JS — thin client for the live API, no embedded data
```

---

## Quick Start

### 1 — Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### 2 — Database

Run `supabase_setup.sql` in the Supabase SQL Editor (safe to re-run). It creates the
`job_posts`, `scam_reports`, `recruiter_profiles`, and `domain_reputation` tables and
the row-level-security policies the backend needs — including `anon insert` on
`job_posts`, which is required for `/analyze` and `/analyze-url` to save results.

### 3 — Frontend

Open any HTML file directly in your browser, **or** serve with:

```bash
cd frontend
python -m http.server 5500
# then open http://localhost:5500
```

The frontend talks **only** to the live FastAPI backend at `http://127.0.0.1:8000`.
If the backend is down, pages show a clear "can't reach the server" message instead
of silently substituting fake numbers — check the **● Live / ● Offline** badge in
the top-right of every page.

---

## Analyzing a job posting

On the **Analyze** page you can either:

- **Paste a job URL** from LinkedIn, Naukri, Indeed, Internshala, or almost any
  company careers page. The backend fetches the page server-side, extracts the
  title, company, location, salary, and description (using JSON-LD structured
  data when available, falling back to meta tags and visible text), shows you
  exactly what it found, and runs the full risk analysis automatically.
- **Enter details manually** if you'd rather type or paste the job text yourself.

Either way, the same scoring pipeline runs: keyword/urgency pattern matching,
a live domain-reputation lookup, a live recruiter lookup, a salary-anomaly check,
and a check against prior community scam reports for that company.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/analyze` | Score a manually-entered job post |
| POST | `/analyze-url` | Scrape a job URL, then score it |
| POST | `/domain-check` | Check domain trust / SSL / age |
| POST | `/recruiter-check` | Verify recruiter by email or company |
| GET  | `/recruiters` | List recruiter profiles (database browser) |
| POST | `/report` | Submit a scam report |
| GET  | `/reports` | List scam reports (feed + table) |
| GET  | `/dashboard` | Live aggregate stats |
| GET  | `/db-health` | Supabase connectivity check |
| POST | `/auth/login` | Login (returns JWT) |
| POST | `/auth/register` | Register new user |

### Test accounts

| Email | Password | Role |
|-------|----------|------|
| admin@scamdetector.com | admin123 | admin |
| analyst@scamdetector.com | analyst123 | analyst |
| reporter@scamdetector.com | reporter123 | reporter |
| user@scamdetector.com | user123 | user |

---

## Scoring logic

```
scam_score = 0.30 × keyword_risk        (fraud phrases + urgency language)
           + 0.20 × domain_risk         (Supabase domain_reputation lookup)
           + 0.15 × salary_risk         (unrealistic stipend/salary heuristic)
           + 0.15 × recruiter_risk      (Supabase recruiter_profiles lookup)
           + 0.10 × report_risk         (prior scam_reports for the same company)
           + 0.05 × fraud_phrase_flag
           + 0.05 × urgency_flag
```

Risk levels: LOW (0–30) · MEDIUM (31–60) · HIGH (61–80) · CONFIRMED SCAM (81–100)

Domain, recruiter, and report-history signals are **only as good as the data in your
Supabase tables** — an unlisted domain or recruiter scores a neutral default rather
than a fabricated "safe" or "risky" result, and the dashboard reports `0` across the
board until you've analyzed and reported real jobs.
