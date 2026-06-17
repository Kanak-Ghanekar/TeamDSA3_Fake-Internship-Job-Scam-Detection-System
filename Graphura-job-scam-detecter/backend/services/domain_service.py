from backend.db.supabase import SupabaseClient
from backend.models.schemas import DomainCheckRequest, DomainCheckResponse

SUSPICIOUS_TLDS = {"tk", "ml", "ga", "cf", "gq", "xyz"}


class DomainService:
    def __init__(self, db: SupabaseClient):
        self.db = db

    def check(self, payload: DomainCheckRequest) -> DomainCheckResponse:
        domain = payload.domain.lower().strip()
        reasons: list[str] = []
        score = 50.0

        tld = domain.rsplit(".", 1)[-1] if "." in domain else ""
        if tld in SUSPICIOUS_TLDS:
            score -= 30
            reasons.append(f"Domain uses an uncommon, often-abused TLD (.{tld})")

        return DomainCheckResponse(
            domain=domain, is_suspicious=score < 50,
            reputation_score=round(score, 2), reasons=reasons,
        )
