"""
Recruiter Service — looks up a recruiter by email / company in Supabase.
"""

import logging
from typing import List
from backend.db.supabase import SupabaseClient
from backend.models.schemas import RecruiterCheckRequest, RecruiterCheckResponse

logger = logging.getLogger(__name__)

FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "yahoo.in", "outlook.com",
    "hotmail.com", "rediffmail.com", "ymail.com", "protonmail.com",
}


def _risk_label(score: float) -> str:
    if score <= 25:
        return "LOW RISK"
    if score <= 55:
        return "MEDIUM RISK"
    if score <= 80:
        return "HIGH RISK"
    return "CONFIRMED SCAM"


class RecruiterService:
    def __init__(self, db: SupabaseClient):
        self.db = db

    def check(self, payload: RecruiterCheckRequest) -> RecruiterCheckResponse:
        email = (payload.email or "").lower().strip()
        company = (payload.company_name or "").strip()
        email_domain = email.split("@")[-1] if "@" in email else ""

        flags: List[str] = []
        found = False
        row = None

        try:
            settings = __import__("backend.core.config", fromlist=["get_settings"]).get_settings()
            table = settings.supabase_recruiters_table or "recruiter_profiles"

            if email:
                resp = self.db.table(table).select("*").ilike("email", email).limit(1).execute()
                rows = getattr(resp, "data", []) or []
                if rows:
                    row = rows[0]
                    found = True

            if not found and company:
                resp = self.db.table(table).select("*").ilike("company", f"%{company}%").limit(1).execute()
                rows = getattr(resp, "data", []) or []
                if rows:
                    row = rows[0]
                    found = True
        except Exception as e:
            logger.warning("Recruiter DB lookup failed: %s", e)

        # Build flags & risk score
        risk_score = 0.0

        if email_domain in FREE_EMAIL_DOMAINS:
            flags.append("Uses free email provider (not a corporate email)")
            risk_score += 30

        if found and row:
            verified = bool(row.get("verified", False))
            prev = int(row.get("previous_reports", 0) or 0)
            linkedin = str(row.get("linkedin_url", "") or "")
            name = str(row.get("recruiter_name", "") or "")
            comp = str(row.get("company", company) or company)

            if not verified:
                flags.append("Recruiter is not verified")
                risk_score += 25
            if prev > 0:
                flags.append(f"{prev} previous scam report(s) filed against this recruiter")
                risk_score += min(prev * 10, 30)
            if not linkedin:
                flags.append("No LinkedIn profile linked")
                risk_score += 10

            capped_score = round(min(risk_score, 100), 1)
            return RecruiterCheckResponse(
                recruiter_name=name,
                company=comp,
                email_domain=email_domain or None,
                verified=verified,
                previous_reports=prev,
                linkedin_url=linkedin or None,
                risk_score=capped_score,
                risk_level=_risk_label(capped_score),
                found=True,
                flags=flags,
            )

        # Not found
        if not email_domain or email_domain in FREE_EMAIL_DOMAINS:
            risk_score = max(risk_score, 40.0)

        capped_score = round(min(risk_score, 100), 1)
        return RecruiterCheckResponse(
            recruiter_name=None,
            company=company or None,
            email_domain=email_domain or None,
            verified=False,
            previous_reports=0,
            linkedin_url=None,
            risk_score=capped_score,
            risk_level=_risk_label(capped_score),
            found=False,
            flags=flags,
        )
