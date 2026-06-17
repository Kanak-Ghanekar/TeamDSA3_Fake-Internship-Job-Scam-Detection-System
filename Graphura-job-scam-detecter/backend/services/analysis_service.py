import re
from backend.models.schemas import AnalyzeRequest, AnalyzeResponse

SCAM_KEYWORDS: dict[str, int] = {
    "registration fee": 30, "processing fee": 25, "pay before you start": 30,
    "deposit required": 25, "western union": 35, "wire transfer": 20,
    "no interview required": 20, "send your bank details": 35,
    "telegram": 15, "whatsapp only": 15, "urgent hiring": 10,
}
FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com"}


class AnalysisService:
    def analyze(self, payload: AnalyzeRequest) -> AnalyzeResponse:
        text = f"{payload.job_title or ''} {payload.job_description or payload.description or ''}".lower()
        reasons: list[str] = []
        score = 0.0

        for phrase, weight in SCAM_KEYWORDS.items():
            if phrase in text:
                score += weight
                reasons.append(f"Contains suspicious phrase: '{phrase}'")

        salary_value = self._parse_salary(payload.salary)
        if salary_value is not None:
            if salary_value > 500000:
                score += 25
                reasons.append("Salary is unrealistically high for the role described")
            elif salary_value <= 0:
                score += 5
                reasons.append("Salary missing or zero")

        if payload.email:
            domain = payload.email.split("@")[-1].lower()
            if domain in FREE_EMAIL_DOMAINS:
                score += 15
                reasons.append(f"Recruiter is using a free email provider ({domain}) instead of a company domain")

        score = min(score, 100.0)
        return AnalyzeResponse(
            scam_score=score,
            is_flagged=score >= 35,
            recommendation="Proceed with caution" if score >= 35 else "Looks reasonably safe",
            reasons=reasons,
        )

    @staticmethod
    def _parse_salary(raw):
        if not raw:
            return None
        digits = re.sub(r"[^\d.]", "", str(raw))
        if not digits:
            return None
        try:
            return float(digits)
        except ValueError:
            return None
