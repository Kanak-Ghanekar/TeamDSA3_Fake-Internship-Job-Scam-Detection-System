"""
Health Service — checks Supabase connectivity for all configured tables.
"""

import logging
from backend.db.supabase import SupabaseClient
from backend.models.schemas import DbHealthResponse

logger = logging.getLogger(__name__)


class HealthService:
    def __init__(self, db: SupabaseClient):
        self.db = db

    def check(self) -> DbHealthResponse:
        settings = __import__("backend.core.config", fromlist=["get_settings"]).get_settings()
        tables = {
            "job_posts": settings.supabase_job_posts_table,
            "scam_reports": settings.supabase_reports_table,
            "recruiter_profiles": settings.supabase_recruiters_table,
            "domain_reputation": settings.supabase_domains_table,
        }

        results: dict = {}
        all_ok = True

        for alias, table_name in tables.items():
            try:
                self.db.table(table_name).select("*").limit(1).execute()
                results[alias] = "ok"
            except Exception as e:
                results[alias] = f"error: {str(e)[:80]}"
                all_ok = False

        return DbHealthResponse(
            status="healthy" if all_ok else "degraded",
            tables=results,
            message="All tables reachable." if all_ok else "Some tables unreachable.",
        )
