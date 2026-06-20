-- ============================================================
-- ScamRadar / ScamDetectAI — Supabase table setup
-- Run this in: Supabase Dashboard → SQL Editor → New Query
--
-- UPDATE: added "anon insert job_posts" policy below — required for
-- POST /analyze and POST /analyze-url to save results. If you already
-- ran this script before, just run this one statement again:
--
--   create policy "anon insert job_posts" on public.job_posts
--       for insert to anon with check (true);
--
-- (Re-running the whole file is also safe — every CREATE uses
-- "if not exists" / will simply error harmlessly on existing policies.)
-- ============================================================

-- 1. scam_reports — written to by POST /report (report.html "Submit Report")
create table if not exists public.scam_reports (
    id           bigint generated always as identity primary key,
    report_id    uuid not null default gen_random_uuid(),
    job_id       text,
    job_title    text,
    company_name text,
    report_reason text not null,
    user_comment  text,
    severity      int not null default 3 check (severity between 1 and 5),
    reporter_email text,
    reported_at    timestamptz not null default now()
);

-- 2. job_posts — used by dashboard + analyze lookups
create table if not exists public.job_posts (
    id            bigint generated always as identity primary key,
    report_id     text,
    title         text,
    company_name  text,
    location      text,
    scam_score    numeric,
    is_flagged    boolean default false,
    created_at    timestamptz default now()
);

-- 3. recruiter_profiles — used by /recruiter-check
create table if not exists public.recruiter_profiles (
    id                bigint generated always as identity primary key,
    email             text,
    company           text,
    recruiter_name    text,
    verified          boolean default false,
    previous_reports  int default 0,
    linkedin_url      text,
    created_at        timestamptz default now()
);

-- 4. domain_reputation — used by /domain-check
create table if not exists public.domain_reputation (
    id              bigint generated always as identity primary key,
    domain_name     text not null,
    domain_age_days int default 0,
    ssl_valid       boolean default false,
    trust_score     numeric default 50,
    blacklisted     boolean default false,
    created_at      timestamptz default now()
);

-- 5. flagged_keywords — optional, referenced in .env/config but not yet queried by any service
create table if not exists public.flagged_keywords (
    id          bigint generated always as identity primary key,
    keyword     text not null,
    weight      numeric default 1.0,
    created_at  timestamptz default now()
);

-- Helpful indexes
create index if not exists idx_scam_reports_reason on public.scam_reports (report_reason);
create index if not exists idx_domain_reputation_domain on public.domain_reputation (domain_name);
create index if not exists idx_recruiter_profiles_email on public.recruiter_profiles (email);

-- Row Level Security: enable + allow anon insert/select for the report flow.
-- (The backend currently uses the anon key, so these policies are required
--  for /report, /analyze, /domain-check, /recruiter-check, /dashboard to work.)
alter table public.scam_reports enable row level security;
alter table public.job_posts enable row level security;
alter table public.recruiter_profiles enable row level security;
alter table public.domain_reputation enable row level security;
alter table public.flagged_keywords enable row level security;

create policy "anon insert reports" on public.scam_reports
    for insert to anon with check (true);
create policy "anon read reports" on public.scam_reports
    for select to anon using (true);

create policy "anon read job_posts" on public.job_posts
    for select to anon using (true);

create policy "anon insert job_posts" on public.job_posts
    for insert to anon with check (true);

create policy "anon read recruiter_profiles" on public.recruiter_profiles
    for select to anon using (true);

create policy "anon read domain_reputation" on public.domain_reputation
    for select to anon using (true);

create policy "anon read flagged_keywords" on public.flagged_keywords
    for select to anon using (true);
