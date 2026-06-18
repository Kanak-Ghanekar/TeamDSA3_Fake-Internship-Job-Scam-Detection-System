from backend.core.config import get_settings
from backend.db.supabase import SupabaseClient
from backend.models.schemas import DomainCheckRequest, DomainCheckResponse

SUSPICIOUS_TLDS = {"tk", "ml", "ga", "cf", "gq", "xyz"}


class DomainService:
    def __init__(self, db: SupabaseClient):
        self.db = db
        self.settings = get_settings()

    def check(self, payload: DomainCheckRequest) -> DomainCheckResponse:
        domain = payload.domain.lower().strip()
        reasons: list[str] = []
        score = 50.0

        tld = domain.rsplit(".", 1)[-1] if "." in domain else ""
        if tld in SUSPICIOUS_TLDS:
            score -= 30
            reasons.append(f"Domain uses an uncommon, often-abused TLD (.{tld})")

        try:
            result = (
                self.db.table(self.settings.supabase_domain_table)
                .select("domain_age_days, ssl_valid, trust_score, blacklisted")
                .eq("domain_name", domain)
                .limit(1)
                .execute()
            )
            rows = getattr(result, "data", None) or []
            if rows:
                record = rows[0]
                if record.get("blacklisted"):
                    score -= 40
                    reasons.append("Domain is on the known blacklist")
                if record.get("ssl_valid") is False:
                    score -= 15
                    reasons.append("Domain does not have a valid SSL certificate")
                trust_score = record.get("trust_score")
                if trust_score is not None:
                    score = (score + float(trust_score) * 100) / 2
                age_days = record.get("domain_age_days")
                if age_days is not None and age_days < 90:
                    score -= 10
                    reasons.append("Domain was registered recently (under 90 days old)")
            else:
                reasons.append("Domain not found in reputation database; relying on basic checks only")
        except Exception as exc:
            reasons.append(f"Could not check reputation database: {exc}")

        score = max(0.0, min(100.0, score))
        return DomainCheckResponse(
            domain=domain, is_suspicious=score < 50,
            reputation_score=round(score, 2), reasons=reasons,
        )
