from backend.core.config import get_settings
from backend.db.supabase import SupabaseClient
from backend.models.schemas import DashboardResponse


class DashboardService:
    def __init__(self, db: SupabaseClient):
        self.db = db
        self.settings = get_settings()

    def get_stats(self) -> DashboardResponse:
        table = self.settings.supabase_job_posts_table
        try:
            result = self.db.table(table).select("Scam_score, is_flagged, Domain_name").execute()
            rows = result.data or []
        except Exception:
            rows = []

        total = len(rows)
        flagged = sum(1 for r in rows if r.get("is_flagged"))
        avg_score = sum(r.get("Scam_score", 0) or 0 for r in rows) / total if total else 0.0
        flagged_domains = [r.get("Domain_name") for r in rows if r.get("is_flagged") and r.get("Domain_name")]
        top_domains = list(dict.fromkeys(flagged_domains))[:5]

        return DashboardResponse(
            total_jobs=total, flagged_jobs=flagged,
            average_scam_score=round(avg_score, 2), top_flagged_domains=top_domains,
        )
