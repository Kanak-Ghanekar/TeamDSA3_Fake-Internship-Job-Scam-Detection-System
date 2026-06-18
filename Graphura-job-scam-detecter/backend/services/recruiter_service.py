from backend.core.config import get_settings
from backend.db.supabase import SupabaseClient
from backend.models.schemas import RecruiterCheckRequest, RecruiterCheckResponse

FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com"}


class RecruiterService:
    def __init__(self, db: SupabaseClient):
        self.db = db
        self.settings = get_settings()

    def check(self, payload: RecruiterCheckRequest) -> RecruiterCheckResponse:
        reasons: list[str] = []
        score = 70.0

        if payload.email:
            domain = payload.email.split("@")[-1].lower()
            if domain in FREE_EMAIL_DOMAINS:
                score -= 25
                reasons.append(f"Recruiter is using a free email provider ({domain})")

        if not payload.linkedin_url:
            score -= 10
            reasons.append("No LinkedIn profile provided to verify identity")

        try:
            result = (
                self.db.table(self.settings.supabase_recruiter_table)
                .select("verified, previous_reports")
                .eq("company", payload.company)
                .limit(1)
                .execute()
            )
            rows = getattr(result, "data", None) or []
            if rows:
                record = rows[0]
                if record.get("verified"):
                    score += 15
                    reasons.append("Recruiter's company is verified in our records")
                else:
                    score -= 10
                    reasons.append("Recruiter's company is not verified in our records")
                prev_reports = record.get("previous_reports") or 0
                if float(prev_reports) > 0:
                    score -= min(30, float(prev_reports) * 10)
                    reasons.append(f"Company has {prev_reports} previous scam report(s)")
            else:
                reasons.append("Company not found in recruiter database; relying on basic checks only")
        except Exception as exc:
            reasons.append(f"Could not check recruiter database: {exc}")

        score = max(0.0, min(100.0, score))
        return RecruiterCheckResponse(
            is_verified=score >= 50, risk_score=round(100 - score, 2), reasons=reasons,
        )
