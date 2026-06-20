from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# ANALYZE
# ─────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    job_title: Optional[str] = None
    title: Optional[str] = None
    company_name: Optional[str] = None
    company: Optional[str] = None
    job_description: Optional[str] = None
    description: Optional[str] = None
    salary: Optional[Any] = None
    location: Optional[str] = None
    job_url: Optional[str] = None
    source_url: Optional[str] = None
    domain: Optional[str] = None
    recruiter_email: Optional[str] = None

    class Config:
        extra = "allow"


class RiskBreakdown(BaseModel):
    keyword_risk: float = 0.0
    domain_risk: float = 0.0
    recruiter_risk: float = 0.0
    salary_risk: float = 0.0
    report_risk: float = 0.0


class AnalyzeResponse(BaseModel):
    scam_score: float
    risk_level: str
    is_flagged: bool
    flagged_keywords: List[str] = []
    risk_breakdown: RiskBreakdown = Field(default_factory=RiskBreakdown)
    recommendation: Optional[str] = None
    domain_info: Optional[Dict[str, Any]] = None
    recruiter_info: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────
# ANALYZE BY URL (auto-scrape + analyze)
# ─────────────────────────────────────────────

class AnalyzeUrlRequest(BaseModel):
    url: str
    recruiter_email: Optional[str] = None


class AnalyzeUrlResponse(BaseModel):
    scraped_title: str = ""
    scraped_company: str = ""
    scraped_location: str = ""
    scraped_salary: str = ""
    scraped_description: str = ""
    domain: str = ""
    source_url: str = ""
    extraction_method: str = "unknown"
    partial_extraction: bool = False
    analysis: AnalyzeResponse


# ─────────────────────────────────────────────
# DOMAIN CHECK
# ─────────────────────────────────────────────

class DomainCheckRequest(BaseModel):
    domain_name: str


class DomainCheckResponse(BaseModel):
    domain_name: str
    domain_age_days: int = 0
    ssl_valid: bool = False
    trust_score: float = 0.0
    blacklisted: bool = False
    risk_level: str = "UNKNOWN"
    risk_score: float = 0.0
    found: bool = False
    # Real, computed-on-the-spot signal from analyzing the domain string
    # itself (TLD, digit ratio, length, hyphens, known job-board allowlist).
    # Available regardless of whether the domain is in domain_reputation,
    # since it requires no database lookup at all.
    pattern_flags: List[str] = []
    pattern_score: float = 0.0


# ─────────────────────────────────────────────
# RECRUITER CHECK
# ─────────────────────────────────────────────

class RecruiterCheckRequest(BaseModel):
    email: Optional[str] = None
    company_name: Optional[str] = None
    recruiter_name: Optional[str] = None


class RecruiterCheckResponse(BaseModel):
    recruiter_name: Optional[str] = None
    company: Optional[str] = None
    email_domain: Optional[str] = None
    verified: bool = False
    previous_reports: int = 0
    linkedin_url: Optional[str] = None
    risk_level: str = "UNKNOWN"
    risk_score: float = 0.0
    found: bool = False
    flags: List[str] = []


class RecruiterListResponse(BaseModel):
    recruiters: List[Dict[str, Any]] = []


# ─────────────────────────────────────────────
# REPORT
# ─────────────────────────────────────────────

class ReportRequest(BaseModel):
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    report_reason: str
    user_comment: Optional[str] = None
    severity: int = Field(default=3, ge=1, le=5)
    reporter_email: Optional[str] = None


class ReportResponse(BaseModel):
    report_id: Optional[str] = None
    message: str
    success: bool = True
    # True only when the report was actually written to Supabase and will
    # therefore show up in /reports, the dashboard charts, and the Scam
    # Reports Database page. False means it only landed in local fallback
    # storage (e.g. a Supabase/network/RLS issue) — still saved, but not
    # yet visible anywhere else, and the frontend should say so clearly.
    saved_to_database: bool = True


class ReportListResponse(BaseModel):
    reports: List[Dict[str, Any]] = []


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────

class DashboardResponse(BaseModel):
    total_jobs: int = 0
    flagged_jobs: int = 0
    legit_jobs: int = 0
    high_risk_jobs: int = 0
    avg_scam_score: float = 0.0
    report_reasons: Dict[str, int] = {}
    top_flagged_domains: Dict[str, int] = {}
    recent_flagged: List[Dict[str, Any]] = []


# ─────────────────────────────────────────────
# DB HEALTH
# ─────────────────────────────────────────────

class DbHealthResponse(BaseModel):
    status: str
    tables: Dict[str, str] = {}
    message: Optional[str] = None
