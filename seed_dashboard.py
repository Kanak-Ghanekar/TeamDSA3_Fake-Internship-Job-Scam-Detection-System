"""
seed_dashboard.py — populate Supabase with REAL analyzed job postings.

This does NOT insert fake numbers into Supabase. It sends a realistic mix
of job postings (genuine scam patterns, genuine legitimate postings, and a
couple of borderline ones) through your actual, running /analyze endpoint.
Each one is scored by your real AnalysisService and saved to job_posts via
the same code path a real user hitting the website would trigger. A few
"report" submissions are sent too, so the report_reasons chart has data.

WHY: the dashboard charts show zero/empty right now because job_posts has
no rows yet in your Supabase project — that's correct, honest behavior, not
a bug. Running a handful of real analyses is what gives the dashboard real
numbers to show.

USAGE:
    1. Start your backend first:
         cd ScamDetectAI
         uvicorn backend.main:app --reload --port 8000
    2. In another terminal, from the ScamDetectAI project root:
         pip install requests   # only if not already installed
         python seed_dashboard.py
    3. Refresh index.html — the dashboard will now show real computed stats.

You can re-run this any time to add more sample data, or edit the
JOB_POSTINGS / REPORTS lists below to add your own real examples.
"""

import sys
import time
import requests

API_BASE = "http://127.0.0.1:8000"

JOB_POSTINGS = [
    # ── Clear scams ──────────────────────────────────────────────────────
    dict(
        title="Work From Home - Earn Daily Cash!",
        description=(
            "No experience required! No interview needed! Instant joining. "
            "Pay a small registration fee of Rs 499 to get started. Urgent "
            "hiring, limited seats available, apply now. Easy income, "
            "work just 1 hour a day. Join our Telegram group for details."
        ),
        salary="2500/day",
        company_name="QuickEarn Global",
        location="Remote",
        recruiter_email="hr.quickearn@gmail.com",
    ),
    dict(
        title="Data Entry Job - Guaranteed Placement",
        description=(
            "Guaranteed job, no experience required. Send your bank details "
            "and KYC documents to proceed. Pay training fee of Rs 999. "
            "WhatsApp HR for instant joining. Closing soon, act fast."
        ),
        salary="40000",
        company_name="BrightFuture Careers",
        location="Remote",
        recruiter_email="recruiter123@yahoo.com",
    ),
    dict(
        title="Online Typing Job - Refer and Earn",
        description=(
            "Part time earn good money, easy income, no experience required. "
            "Click link below to register. Refer and earn bonus. "
            "Daily payout to your account."
        ),
        salary="800 per day",
        company_name="TypeFast Solutions",
        location="Remote",
        recruiter_email="jobs.typefast@gmail.com",
    ),
    # ── Legitimate-looking postings ──────────────────────────────────────
    dict(
        title="Data Science Intern",
        description=(
            "3-month internship working with our analytics team on real "
            "production projects. You'll work with our senior data "
            "scientists on model development, mentorship provided, and a "
            "potential full-time offer at the end based on performance."
        ),
        salary="15000",
        company_name="Graphura India Private Limited",
        location="Noida, India",
    ),
    dict(
        title="Senior Backend Engineer",
        description=(
            "We're looking for an experienced backend engineer with 4+ "
            "years building distributed systems in Python or Go. You'll "
            "own core services, participate in design reviews, and mentor "
            "junior engineers on the team."
        ),
        salary="95000",
        company_name="Northwind Systems",
        location="Bengaluru, India",
    ),
    dict(
        title="Marketing Associate",
        description=(
            "Join our growth team to plan and execute campaigns across "
            "digital channels. Bachelor's degree in marketing or related "
            "field preferred. Hybrid role, standard interview process."
        ),
        salary="32000",
        company_name="Lumen Retail Pvt Ltd",
        location="Pune, India",
    ),
    dict(
        title="Frontend Developer (React)",
        description=(
            "Build and maintain customer-facing web applications using "
            "React and TypeScript. Collaborate with design and product "
            "teams in an agile environment. 2+ years experience expected."
        ),
        salary="55000",
        company_name="Vertex Software Labs",
        location="Hyderabad, India",
    ),
    # ── Borderline / ambiguous ───────────────────────────────────────────
    dict(
        title="Customer Support Executive - Immediate Joining",
        description=(
            "Looking for candidates available for immediate joining. "
            "Apply now, limited seats. Standard interview and onboarding "
            "process, fixed salary plus incentives."
        ),
        salary="22000",
        company_name="Helpline Services Co",
        location="Gurugram, India",
        recruiter_email="hiring@helplineservices.in",
    ),
    dict(
        title="Freelance Content Writer",
        description=(
            "Write blog posts and articles for our client portfolio. "
            "Flexible hours, part time, payment per article delivered."
        ),
        salary="300 per article",
        company_name="WordCraft Media",
        location="Remote",
    ),
]

REPORTS = [
    dict(
        job_title="Work From Home - Earn Daily Cash!",
        company_name="QuickEarn Global",
        report_reason="Asked for registration fee",
        user_comment="They asked me to pay before giving any job details.",
        severity=5,
    ),
    dict(
        job_title="Data Entry Job - Guaranteed Placement",
        company_name="BrightFuture Careers",
        report_reason="Requested bank details / KYC upfront",
        user_comment="Recruiter asked for KYC documents over WhatsApp before any interview.",
        severity=5,
    ),
    dict(
        job_title="Online Typing Job - Refer and Earn",
        company_name="TypeFast Solutions",
        report_reason="Suspicious payment link",
        user_comment="Sent a link asking to register and pay a fee.",
        severity=4,
    ),
]


def post(path, payload):
    r = requests.post(f"{API_BASE}{path}", json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def main():
    try:
        h = requests.get(f"{API_BASE}/health", timeout=5)
        h.raise_for_status()
    except Exception:
        print(f"ERROR: Can't reach the backend at {API_BASE}.")
        print("Start it first:  uvicorn backend.main:app --reload --port 8000")
        sys.exit(1)

    print(f"Backend is up at {API_BASE}. Seeding {len(JOB_POSTINGS)} job analyses...\n")

    for job in JOB_POSTINGS:
        try:
            result = post("/analyze", job)
            print(
                f"  ✓ {job['title']:<42} score={result['scam_score']:>5.1f} "
                f"({result['risk_level']})"
            )
        except Exception as e:
            print(f"  ✗ {job['title']:<42} FAILED: {e}")
        time.sleep(0.2)

    print(f"\nSeeding {len(REPORTS)} scam reports...\n")
    for rep in REPORTS:
        try:
            post("/report", rep)
            print(f"  ✓ Report: {rep['report_reason']}")
        except Exception as e:
            print(f"  ✗ Report failed ({rep['report_reason']}): {e}")
        time.sleep(0.2)

    print("\nDone. Refresh index.html — the dashboard should now show real data.")


if __name__ == "__main__":
    main()
