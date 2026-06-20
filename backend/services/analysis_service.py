"""
Analysis Service — composite scam-risk scorer.

Combines:
  - Keyword / urgency-phrase pattern matching (text heuristics)
  - REAL domain reputation lookup via DomainService (Supabase domain_reputation table)
  - REAL recruiter reputation lookup via RecruiterService (Supabase recruiter_profiles table)
  - Salary-anomaly heuristic
  - Historical report-count risk (Supabase scam_reports table, matched by company)

Nothing here is hardcoded sample data — every signal either comes from the
text the user/scraper supplied, or from a live Supabase query. If a lookup
table has no row for a given domain/recruiter/company, the service falls
back to a clearly-labeled neutral default (not a fake "found" result).
"""

import re
import logging
from typing import Optional

from backend.db.supabase import SupabaseClient
from backend.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    RiskBreakdown,
    DomainCheckRequest,
    RecruiterCheckRequest,
)
from backend.services.domain_service import DomainService
from backend.services.recruiter_service import RecruiterService

logger = logging.getLogger(__name__)

# ── Fraud phrase patterns ───────────────────────────────────────────────────
FRAUD_PATTERNS = [
    "registration fee", "training fee", "security deposit", "pay first",
    "instant joining", "no interview", "earn daily", "whatsapp hr",
    "limited seats", "guaranteed job", "guaranteed placement",
    "work 1 hour", "easy income", "urgent hiring", "click link",
    "work from home earn", "no experience required earn",
    "part time earn", "daily payout", "weekly payout",
    "send otp", "kyc required", "bank details required",
    "telegram group", "whatsapp group join", "refer and earn",
]

URGENCY_WORDS = [
    "urgent", "immediate", "limited", "hurry", "instant",
    "today only", "last date", "apply now", "limited seats",
    "act fast", "don't miss", "closing soon",
]

FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "yahoo.in", "outlook.com",
    "hotmail.com", "rediffmail.com", "ymail.com", "protonmail.com",
}


def _clean(text: Optional[str]) -> str:
    if not text:
        return ""
    t = str(text).lower()
    t = re.sub(r"http\S+|www\S+", " ", t)
    t = re.sub(r"<.*?>", " ", t)
    t = re.sub(r"[^a-z0-9₹$@.\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _extract_number(value) -> float:
    if value is None:
        return 0.0
    s = str(value).replace(",", "").replace("₹", "").replace("$", "").strip()
    nums = re.findall(r"\d+\.?\d*", s)
    return float(nums[0]) if nums else 0.0


def _normalize_to_monthly(value, raw_amount: float) -> float:
    """Best-effort normalization of a salary figure to a monthly equivalent,
    based on the unit words present in the original text (day/hour/week/year).
    Falls back to treating the figure as already-monthly if no unit is found."""
    if raw_amount <= 0:
        return 0.0
    s = str(value).lower()
    if re.search(r"\b(per\s*day|/day|daily|per\s*hour|/hr|/hour|hourly)\b", s):
        if re.search(r"\b(per\s*hour|/hr|/hour|hourly)\b", s):
            return raw_amount * 8 * 26  # ~8hr/day, ~26 working days/month
        return raw_amount * 26  # daily rate -> monthly
    if re.search(r"\b(per\s*week|/week|weekly)\b", s):
        return raw_amount * 4.33
    if re.search(r"\b(per\s*year|/year|annual|annually|p\.a\.|lpa)\b", s):
        return raw_amount / 12
    return raw_amount


def _risk_label(score: float) -> str:
    if score <= 30:
        return "LOW RISK"
    if score <= 60:
        return "MEDIUM RISK"
    if score <= 80:
        return "HIGH RISK"
    return "CONFIRMED SCAM"


class AnalysisService:
    """Composite scam scorer: text heuristics + live Supabase domain/recruiter data."""

    def __init__(self, db: Optional[SupabaseClient] = None):
        self.db = db
        self.domain_service = DomainService(db) if db is not None else None
        self.recruiter_service = RecruiterService(db) if db is not None else None

    def analyze(self, payload: AnalyzeRequest) -> AnalyzeResponse:
        title = _clean(payload.job_title or payload.title or "")
        desc = _clean(payload.job_description or payload.description or "")
        combined = f"{title} {desc}"
        salary_raw = payload.salary
        source_url = str(payload.job_url or payload.source_url or "")
        recruiter_email = str(payload.recruiter_email or "")

        # ── 1. Keyword risk ──────────────────────────────────────────────
        fraud_hits = [p for p in FRAUD_PATTERNS if p in combined]
        urgency_hits = [w for w in URGENCY_WORDS if w in combined]
        keyword_score_raw = len(fraud_hits) * 0.15 + len(urgency_hits) * 0.08
        keyword_risk = min(keyword_score_raw, 1.0)

        # ── 2. Domain risk — REAL Supabase lookup, no hardcoded default ──
        domain_name = str(payload.domain or "").lower().strip()
        if not domain_name and source_url:
            try:
                domain_name = source_url.split("//")[-1].split("/")[0].replace("www.", "")
            except Exception:
                pass

        domain_risk = 0.5  # neutral prior used only if we truly cannot look anything up
        domain_info: dict = {}
        if domain_name and self.domain_service is not None:
            try:
                d = self.domain_service.check(DomainCheckRequest(domain_name=domain_name))
                domain_risk = min(max(d.risk_score / 100.0, 0.0), 1.0)
                if d.found:
                    # Real DB-sourced facts — safe to show as-is.
                    domain_info = {
                        "domain_name": d.domain_name,
                        "domain_age_days": d.domain_age_days,
                        "ssl_valid": d.ssl_valid,
                        "trust_score": d.trust_score,
                        "blacklisted": d.blacklisted,
                        "found_in_database": d.found,
                        "pattern_flags": d.pattern_flags,
                    }
                elif d.pattern_flags:
                    # Domain isn't in domain_reputation, so we deliberately
                    # withhold fabricated DB-style fields (age/SSL/trust
                    # score). But pattern_flags are genuine, computed
                    # directly from the domain string with no DB lookup
                    # involved — safe and useful to surface on their own.
                    domain_info = {
                        "domain_name": d.domain_name,
                        "found_in_database": False,
                        "pattern_flags": d.pattern_flags,
                    }
            except Exception as e:
                logger.warning("Domain lookup failed during analysis for %s: %s", domain_name, e)

        # ── 3. Salary anomaly ────────────────────────────────────────────
        # Real fake-job listings tend to advertise unusually generous pay
        # for little/no work (e.g. "earn ₹2000/day, 1 hour work, no
        # experience needed" -> ~₹52k/month effective for an unskilled,
        # low-effort role). We normalize whatever figure was given to an
        # effective monthly amount and flag it only when it's paired with
        # low-effort/no-experience language, since that combination is the
        # actual scam signal — a high monthly salary on its own (e.g. a
        # senior engineer role) is not penalized.
        salary_val = _extract_number(salary_raw)
        effective_monthly = _normalize_to_monthly(salary_raw, salary_val)
        low_effort_signals = any(
            phrase in combined
            for phrase in (
                "no experience", "no experience required", "work 1 hour",
                "part time earn", "easy income", "daily payout", "weekly payout",
            )
        )
        salary_risk = 0.0
        if effective_monthly > 0:
            if low_effort_signals and effective_monthly > 40000:
                salary_risk = 1.0
            elif low_effort_signals and effective_monthly > 20000:
                salary_risk = 0.6
            elif effective_monthly > 300000:
                # Even without explicit low-effort phrasing, an extreme
                # effective monthly figure (e.g. a "₹10,000/day" listing)
                # is itself a red flag worth a moderate score.
                salary_risk = 0.4

        # ── 4. Recruiter risk — REAL Supabase lookup ─────────────────────
        recruiter_risk = 0.0
        recruiter_info: dict = {}
        if recruiter_email:
            email_domain = recruiter_email.split("@")[-1].lower() if "@" in recruiter_email else ""
            is_free = email_domain in FREE_EMAIL_DOMAINS
            if is_free:
                recruiter_risk += 0.40
            recruiter_info["free_email"] = is_free

            company_name = payload.company_name or payload.company or ""
            if self.recruiter_service is not None:
                try:
                    r = self.recruiter_service.check(
                        RecruiterCheckRequest(email=recruiter_email, company_name=company_name)
                    )
                    if r.found:
                        recruiter_risk = max(recruiter_risk, r.risk_score / 100.0)
                        recruiter_info.update(
                            {
                                "recruiter_name": r.recruiter_name,
                                "company": r.company,
                                "verified": r.verified,
                                "previous_reports": r.previous_reports,
                                "linkedin_url": r.linkedin_url,
                                "flags": r.flags,
                                "found_in_database": True,
                            }
                        )
                    else:
                        recruiter_info["found_in_database"] = False
                except Exception as e:
                    logger.warning("Recruiter lookup failed during analysis: %s", e)

        # ── 5. Historical report risk — REAL Supabase lookup ─────────────
        report_risk = 0.0
        company_for_reports = (payload.company_name or payload.company or "").strip()
        if self.db is not None and company_for_reports:
            try:
                from backend.core.config import get_settings

                settings = get_settings()
                table = settings.supabase_reports_table or "scam_reports"
                resp = (
                    self.db.table(table)
                    .select("id")
                    .ilike("company_name", f"%{company_for_reports}%")
                    .execute()
                )
                rows = getattr(resp, "data", []) or []
                if rows:
                    report_risk = min(len(rows) * 0.15, 1.0)
                    recruiter_info.setdefault("prior_reports_for_company", len(rows))
            except Exception as e:
                logger.warning("Report-history lookup failed during analysis: %s", e)

        # ── 6. Composite scam score ──────────────────────────────────────
        raw_score = (
            0.30 * keyword_risk
            + 0.20 * domain_risk
            + 0.15 * salary_risk
            + 0.15 * recruiter_risk
            + 0.10 * report_risk
            + 0.05 * (1 if len(fraud_hits) > 0 else 0)
            + 0.05 * (1 if len(urgency_hits) > 0 else 0)
        )
        scam_score = round(min(raw_score * 100, 100), 2)

        breakdown = RiskBreakdown(
            keyword_risk=round(keyword_risk * 100, 1),
            domain_risk=round(domain_risk * 100, 1),
            recruiter_risk=round(recruiter_risk * 100, 1),
            salary_risk=round(salary_risk * 100, 1),
            report_risk=round(report_risk * 100, 1),
        )

        flagged_keywords = list(set(fraud_hits + urgency_hits))[:10]

        return AnalyzeResponse(
            scam_score=scam_score,
            risk_level=_risk_label(scam_score),
            is_flagged=scam_score >= 35,
            flagged_keywords=flagged_keywords,
            risk_breakdown=breakdown,
            recommendation=(
                "This job posting shows multiple red flags. Do NOT pay any fees, "
                "share bank details, or click unknown links."
                if scam_score >= 60
                else (
                    "Exercise caution. Verify the company independently before applying."
                    if scam_score >= 35
                    else "This posting appears legitimate. Still verify before sharing personal data."
                )
            ),
            domain_info=domain_info if domain_info else None,
            recruiter_info=recruiter_info if recruiter_info else None,
        )
