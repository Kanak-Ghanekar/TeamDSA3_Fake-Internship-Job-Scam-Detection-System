# Fixes Applied — ScamDetectAI

This documents every bug found and fixed in this build, with how each was verified.

---

## 1. `backend/requirements.txt` — broken dependency pin (blocked ALL backend startup)

**Bug:** `postgrest==0.17.0` was pinned directly, but `supabase==2.7.4` requires
`postgrest<0.17.0`. This made `pip install -r requirements.txt` fail with
`ResolutionImpossible` every time — meaning the backend could never even be
installed, let alone started. This is the direct cause of the
"Can't reach the Scam Detect AI server at http://127.0.0.1:8000" error in the
dashboard: there was no way to get a server running in the first place.

**Fix:** Removed the explicit `postgrest` pin and let `supabase` install its
own compatible version (resolves to `postgrest==0.16.11`).

**Verified:** Fresh venv install now completes with exit code 0; `supabase`
and `postgrest` import and the app boots (`uvicorn backend.main:app`) and
answers `/health` and `/analyze` with `200 OK`.

---

## 2. `backend/services/analysis_service.py` — inverted salary-risk heuristic

**Bug:** The salary-anomaly check flagged **high monthly salaries** as risky
and **low salaries** as zero-risk:
```python
if salary_val > 50000: salary_risk = 1.0
elif salary_val > 20000: salary_risk = 0.4
```
This is backwards for a fake-job/scam detector. Real scam postings advertise
unrealistically generous pay for little/no effort (e.g. "earn ₹2000/day,
1 hour work, no experience needed"), not simply "a high monthly number."
As written, a legitimate ₹80,000/month senior engineering job scored
`salary_risk = 100` (max risk) while a real fee-demanding scam advertising
₹500/day scored `salary_risk = 0`.

**Fix:** Added `_normalize_to_monthly()` to convert day/hour/week/year-stated
figures to an effective monthly amount, then only flag salary as risky when
that effective amount is high **and** paired with low-effort/no-experience
language already present elsewhere in the posting (e.g. "no experience",
"work 1 hour", "easy income"). A high salary alone — with no other red flags
— is no longer penalized.

**Verified** with six scenarios (see test output during the fix):
- Real scam (₹2000/day, "work 1 hour", "no experience") → `salary_risk = 100`, HIGH RISK
- Legit ₹80k/month senior engineer job, no scam language → `salary_risk = 0`, LOW RISK
- Legit ₹35 LPA management role → `salary_risk = 0`, LOW RISK
- Normal ₹15k/month internship → `salary_risk = 0`, LOW RISK
- Scam with hourly framing (₹250/hr, "easy income") → `salary_risk = 100`
- Very high salary (₹2L/month) with zero scam language → `salary_risk = 0`

---

## 3. `backend/core/config.py` — wrong table name casing

**Bug:** The fallback default for the flagged-keywords table was
`"FLAGGED_KEYWORDS"` (uppercase), but the actual table created in
`supabase_setup.sql` is `flagged_keywords` (lowercase). This table isn't
queried by any service yet, so it was dormant, but would have caused a
silent table-not-found failure the moment it was wired up.

**Fix:** Changed the fallback default to `"flagged_keywords"` to match the
real schema.

---

## 4. `backend/services/recruiter_service.py` — risk_score/risk_level could disagree

**Bug:** `risk_level` was computed from the raw, uncapped `risk_score`, while
the `risk_score` field returned to the client was capped at 100
(`round(min(risk_score, 100), 1)`). In the current scoring weights the
uncapped max is 95, so this never actually misfired today — but it was one
weight-tuning change away from returning a `risk_score` of `100` labeled
`"HIGH RISK"` instead of `"CONFIRMED SCAM"`, or similar mismatches.

**Fix:** Compute the capped score once, then derive both `risk_score` and
`risk_level` from that same capped value, in both the "found" and "not
found" branches — so they can never disagree regardless of future scoring
changes.

---

## 5. `seed_dashboard.py` (new) — gives the dashboard real data to show

**Issue:** The dashboard charts (Risk Distribution, Score Trend, Top Scam
Reasons, Most Impersonated Companies) were rendering as empty/zero. This
was not a code bug — `dashboard_service.py` is intentionally honest and
returns real zeros when `job_posts` has no rows yet, rather than fabricating
sample numbers. The chart rendering JS itself (`renderRiskDonut`,
`renderChartBars`, `renderTrend`) is correct and will draw real shapes the
moment real data exists.

**Fix:** Added `seed_dashboard.py`, a small script that sends a realistic
mix of 9 job postings (genuine scam patterns, genuine legitimate postings,
and a couple of borderline ones) through your actual, running `/analyze`
endpoint, plus 3 scam reports through `/report`. Every score is computed
by your real, fixed `AnalysisService` — nothing is hardcoded or inserted
directly into Supabase. Run it once after starting the backend and the
dashboard will show real, honestly-computed numbers and charts.

**Usage:**
```bash
cd ScamDetectAI
uvicorn backend.main:app --reload --port 8000   # terminal 1
python seed_dashboard.py                         # terminal 2
```

**Verified:** Ran the script end-to-end against the local backend. All 9
`/analyze` calls and 3 `/report` calls returned `200`/`201` with sensible,
correctly-differentiated scores (e.g. fee-demanding scam postings scored
52–71 MEDIUM/HIGH RISK; legitimate postings scored 10 LOW RISK). The only
failures observed were the Supabase writes themselves, blocked by this
sandbox's network allowlist (`Host not in allowlist: *.supabase.co`) — on
your machine, with normal internet access, those writes will succeed and
land in your real `job_posts` / `scam_reports` tables.

This sandbox cannot reach `*.supabase.co` (outbound network is restricted to
a small allowlist), so the Supabase-backed read/write paths (`/dashboard`,
`/report`, `/recruiter-check`, `/domain-check` DB lookups) could not be
integration-tested against your real Supabase project from here. They were
verified by:
- Static review of every query against the actual schema in `supabase_setup.sql`
  (table names, column names, and RLS policies all match)
- Running the app and confirming it boots, serves `/health`, and serves
  `/analyze` end-to-end, with the Supabase write failing only because of
  this sandbox's network allowlist (confirmed via the error message itself:
  `Host not in allowlist: spavuyqucbrduccrgawk.supabase.co`)

On your machine, with normal internet access and the SQL script already run
against your Supabase project, the full flow (dashboard stats, report
submission, recruiter/domain checks) should work end-to-end.

---

## 6. Dashboard demo-mode fallback (`frontend/demo-data.js`, `index.html`, `style.css`)

**Request:** Show real-looking, non-zero charts on the dashboard even before
any job has been analyzed, instead of everything reading zero/empty.

**Approach:** No numbers were hand-invented. `demo-data.js` holds the output
of running 16 sample job postings (a deliberate mix of clear scams,
legitimate postings, and borderline cases) through the real, fixed
`AnalysisService.analyze()` — every `scam_score`, `risk_level`,
`flagged_keywords` list, and `risk_breakdown` value in that file is genuine
model output, generated once and saved (see the file's header comment for
exactly which two fields — `report_reasons` counts and per-company counts —
are illustrative placeholders rather than from real `/report` submissions,
since no real reports exist yet either).

`index.html`'s `init()` now checks `stats.total_jobs` from the real
`/dashboard` response. If it's `0` (Supabase has no rows yet), it swaps in
`DEMO_DASHBOARD_DATA` and shows a clearly labeled amber banner explaining
the numbers are sample data generated by the real model, not live. The
moment your Supabase `job_posts` table has at least one real analyzed job,
`total_jobs > 0` and the dashboard automatically switches to live data —
the banner disappears on its own, no manual toggle needed.

**New charts added** (also requested, built from the same real model
output):
- **Top Flagged Keywords** — frequency count of every keyword phrase that
  triggered across the 6 flagged sample postings (e.g. "instant" appeared
  in 4, "limited seats" in 3).
- **Avg. Risk Factor Breakdown (Flagged Jobs)** — average of each of the 5
  components your model scores (`keyword_risk`, `domain_risk`,
  `recruiter_risk`, `salary_risk`, `report_risk`) across the flagged sample
  postings, shown as colored bars matching the existing risk-level palette.

**Verified:** Built a headless jsdom test that loads the real `index.html`,
mocks `fetch` to return genuinely empty dashboard stats (matching the exact
scenario in the reported screenshot — backend reachable, zero rows), and
confirmed every chart renders with real values: stat cards show
`16 / 6 / 3 / 10 / 30.4%`, the donut legend shows real segment values, the
trend strip renders 6 bars, the keyword chart renders 8 rows, the factor
chart renders 5 bars with the exact values from the model run, and the job
table renders all 16 sample rows with correct risk badges and colors.

---

## 7. Removed the "Showing sample data" banner

**Request:** Drop the amber disclaimer banner above the dashboard — it
wasn't wanted in the project.

**Change:** Removed the `#demoBanner` element from `index.html`, its
toggle logic in `init()`, and the now-unused `.demo-banner` CSS rules from
`style.css`. The sample-data fallback behavior itself (`demo-data.js`,
auto-switching to live data once Supabase has real rows) is unchanged —
only the visible banner text is gone. Re-verified with the same headless
render test: all stat cards, charts, and the job table still populate
correctly with no banner element in the DOM.

---

## 8. Domain Intelligence card no longer shows fake placeholder data

**Issue:** When a job's domain wasn't found in the Supabase `domain_reputation`
table, the analysis page still showed a "Domain Intelligence" card with
values like "Domain Age: 0 days" and "Trust Score: 50.0" — these aren't real
facts about the domain, they're internal heuristic defaults
(`backend/services/domain_service.py`) used only to nudge the risk score
when nothing is known. Displaying them as if they were real data was
misleading.

**Fix:** `analysis_service.py` now only attaches `domain_info` to the
`/analyze` response when the domain was actually found in
`domain_reputation` (`d.found == True`). When it's not found, `domain_info`
is `None` and the frontend's existing `renderDomain()` logic — which
already hid the card for empty `domain_info` — now correctly hides it in
this case too. The dead "(not in database — using neutral defaults)" label
branch in `scamanalysis.html` was removed since it can no longer fire.

**Important:** the risk *scoring* is unaffected — `domain_risk` still
applies the same cautious heuristic value internally for unknown domains,
it's only the misleading display that was removed.

**Verified** with three scenarios: `db=None` → `domain_info: None`,
`domain_risk: 50.0` (scoring still applied); mocked Supabase client with no
matching row (the real "not found" path) → `domain_info: None`,
`domain_risk: 40.0` (scoring still applied); mocked Supabase client with a
matching row → `domain_info` populated with the real values as before.

---

## 9. Domain check no longer shows fake placeholder facts — real pattern analysis added instead

**Issue:** Both `recruiter.html`'s "Domain Intelligence Check" and
`scamanalysis.html`'s "Domain Intelligence" panel showed fabricated values
("Domain Age: 0 days", "Trust Score: 50.0 / 100") whenever a domain wasn't
in the Supabase `domain_reputation` table — including for completely
legitimate, major platforms like `internshala.com`.

**Fix:**
- `backend/services/domain_service.py` now also runs a **real, computed-
  on-the-spot pattern analysis** directly on the domain string — no
  database or network call needed, so it's always genuine: suspicious TLD
  detection (`.xyz`, `.tk`, `.top`, etc., commonly abused for scam sites),
  digit-ratio and hyphen-count checks (classic mass-registered scam-domain
  patterns), excessive length, and a small allowlist of well-known
  legitimate job platforms (`linkedin.com`, `naukri.com`,
  `internshala.com`, `indeed.com`, etc.) that's checked first.
- When a domain is found in `domain_reputation`, the UI shows the real
  DB-sourced facts as before.
- When it's **not** found, the UI now shows the real pattern-analysis tags
  instead of fake DB facts — e.g. `internshala.com` correctly shows
  "Recognized as a well-known job platform," and a domain like
  `quickjobs73891.xyz` would show "Uses a TLD ('.xyz') commonly abused for
  throwaway scam sites" + "Domain name contains an unusually high
  proportion of digits."
- The not-found risk score now blends a cautious neutral prior with the
  real pattern score, instead of being a flat hardcoded `40.0` for every
  unknown domain regardless of how suspicious or unremarkable it looks.

**Verified** with `internshala.com`, a synthetic scam-style domain
(`quickjobs73891.xyz`), a synthetic phishing-style domain
(`hr-careers-apply-now.tk`), and an unremarkable domain
(`realcompanyhq.com`) — each produced correct, distinct, real flags. Also
verified via headless DOM render test that both `recruiter.html` and
`scamanalysis.html` correctly branch between "found" (real DB facts) and
"not found" (real pattern tags, no fabricated numbers) rendering paths.

## 10. Submitted scam reports could silently vanish (never reached the dashboard / report feed)

**Root cause found:** `report_service.py`'s `create_report()` wrapped the
Supabase insert in a bare `try/except`. If the insert failed for **any**
reason — table missing, RLS misconfigured, transient network issue — it
silently fell back to writing the report into a local JSON file on the
server's filesystem (`backend/local_reports.json`) and still returned
`success: true` with a generic "submitted" message. Since `/reports`, the
dashboard's "Report Reason Breakdown" chart, and the "Scam Reports
Database" page all query Supabase exclusively, a report that hit this path
would never appear anywhere — exactly matching the reported symptom
(submit succeeds, but the report never shows up in any of the report
widgets). Confirmed by simulating a Supabase insert failure: the report
correctly landed in `local_reports.json`, completely invisible to every
other part of the app.

**Fix:**
- `ReportResponse` now includes a `saved_to_database: bool` field that's
  `true` only when the write actually reached Supabase.
- `report_service.py` sets this honestly and includes the real underlying
  exception message in the response when the Supabase write fails, instead
  of a generic message — so if this happens on your real project, you'll
  see exactly why (e.g. "relation 'scam_reports' does not exist") instead
  of a false "submitted successfully."
- `report.html` now checks `saved_to_database`: if `false`, it shows a
  clear warning panel with the real error detail instead of the success
  message, and does **not** pretend the feed/sidebar/table were updated.
- On genuine success, `report.html` now **re-fetches from `/reports`**
  (the real server state) instead of optimistically patching the DOM
  locally — removing the now-unnecessary `prependFeedItem()` /
  `bumpReasonSidebar()` functions, which were a source of the UI looking
  "updated" even when the underlying write hadn't actually succeeded.

**If you still see reports not appearing after this fix**, the new error
message in the warning panel will tell you exactly why the Supabase write
is failing (most likely: `supabase_setup.sql` wasn't fully run against your
project, or the `scam_reports` table / its RLS insert policy is missing) —
re-run that script against your Supabase project's SQL editor to resolve.

---

## 11. Fixed root cause: reports failing due to missing `company_name` column in live Supabase table

**Found via the error message added in fix #10** — exactly as intended,
the new honest error reporting surfaced the real problem:

```
'message': "Could not find the 'company_name' column of 'scam_reports' in the schema cache"
```

This is PostgREST error `PGRST204`, meaning the live `scam_reports` table
in your actual Supabase project does not have a `company_name` column
(even though `supabase_setup.sql` defines one — the live table was likely
created before that column was added to the script, or `create table if
not exists` no-op'd against an already-existing older table).

**Fix (per your choice — backend stops sending the missing field, no
Supabase changes required):** `report_service.py` now catches PostgREST's
specific "missing column" error, parses out exactly which column is
missing, drops only that field from the insert, and retries — looping if
more than one column is missing. The report then saves successfully to
Supabase (`saved_to_database: true`) and will correctly show up in
`/reports`, the dashboard, and the Scam Reports Database page. The
response message tells you plainly which field(s) were dropped, e.g.:

> "Report submitted, but your Supabase 'scam_reports' table is missing the
> column(s) company_name, so that part of the report wasn't saved. Add the
> missing column(s) in Supabase to capture this data going forward."

**Trade-off to be aware of:** the Company / Org Name typed into the report
form is **not currently stored anywhere** for reports submitted this way —
it's silently dropped on the way in. If you want that field captured in
the future, the column needs to be added to your live Supabase table; once
it exists, this same retry logic will detect that the insert now succeeds
on the first try and the field will start saving automatically, with zero
code changes needed (the SQL to add it yourself, if you change your mind
later, is `alter table public.scam_reports add column company_name text;`
run in the Supabase SQL editor).

**Verified** with the exact error text from the screenshot (mocked), a
multi-missing-column scenario, a clean success with no missing columns,
and a genuine unrelated failure (e.g. network timeout) to confirm the
local-fallback path still works correctly for cases that aren't a
recognizable missing-column error.

---

## 12. Simplified the report success message

**Request:** Drop the schema/column diagnostic detail from the on-page
success message — just show a plain "Report submitted" confirmation.

**Change:** `report.html`'s success panel now always shows "Your report
has been submitted. Thank you for helping keep the community safe."
regardless of whether the backend had to drop any unrecognized columns
(see fix #11). That diagnostic detail (which columns were missing) is
still logged server-side via `logger.warning(...)` in `report_service.py`
for debugging, it's just no longer shown to the person submitting the
report. The Report ID line was also removed from the success panel for the
same reason — it's not the noise people need to see after reporting a
scam.

The genuine-failure warning (when a report couldn't reach Supabase at all
and only saved locally) is unchanged — that's a real "your data isn't
where it should be yet" case worth surfacing, distinct from the
field-dropped case this fix addresses.

---

## 12. Simplified the report submission success message

**Request:** The success panel showed the full dropped-column diagnostic
text (e.g. "Report submitted, but your Supabase 'scam_reports' table is
missing the column(s) company_name, job_title, reporter_email...") plus a
Report ID — too much detail for what should just confirm the action
worked.

**Fix:** `report.html`'s success panel now always shows a plain
"✓ Report submitted" with no extra detail or Report ID, regardless of
whether some optional fields were dropped due to the schema mismatch in
fix #11. The detailed diagnostic still gets logged on the backend (via
`logger.warning(...)` in `report_service.py`) so it's available if you
ever need to debug it, but it no longer surfaces in the UI.

**Kept as-is, deliberately:** if a report genuinely fails to reach
Supabase at all (e.g. it's truly unreachable, falls back to local-only
storage), the page still shows a visible warning — that's a materially
different, more serious situation since the report would otherwise be
completely invisible everywhere, so it stays flagged.

**Verified** via headless render test across three cases: dropped-column
success → plain "✓ Report submitted"; clean success → same; genuine
Supabase-unreachable failure → warning panel still shown correctly.

---

## 13. Simplified report.html to a standalone full-width form

**Request:** Remove the "Report Reason Breakdown" and "Recent Community
Reports" sidebar boxes, and the "Scam Reports Database" table below the
form — keep just the submission form, centered and wider.

**Change:** `report.html` no longer fetches or renders any report list at
all. Removed:
- The sidebar (`Report Reason Breakdown` chart, `Recent Community Reports`
  feed) and its two-column grid layout.
- The full "Scam Reports Database" table with search/severity filter pills.
- All now-dead JS that powered those: `renderReasonSidebar()`,
  `feedItemHTML()`, `renderFeed()`, `renderRepTable()`, `loadReports()`,
  and the filter-pill / search-input event listeners.
- The post-submit `await loadReports()` call, since there's no longer
  anything on this page for it to refresh.

The page container widened from a `1fr 400px` two-column grid (`1000px`
max) to a single centered form card (`760px` max), so the form now reads
as a standalone, full-width submission page rather than a dashboard with a
form embedded in it.

**Verified** via headless render test: all five removed element IDs
(`#reasonSidebar`, `#reportFeed`, `#repTableBody`, `#repFilterPills`,
`#repSearch`) are confirmed absent from the DOM, the form fields and
submit button are still present and functional, and a full submit cycle
still correctly shows the "✓ Report submitted" message.
