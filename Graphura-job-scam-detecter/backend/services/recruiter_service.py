from backend.db.supabase import SupabaseClient
from backend.models.schemas import RecruiterCheckRequest, RecruiterCheckResponse

FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com"}


class RecruiterService:
    def __init__(self, db: SupabaseClient):
        self.db = db

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

        return RecruiterCheckResponse(
            is_verified=score >= 50, risk_score=round(100 - score, 2), reasons=reasons,
        )
