"""
Dashboard Service — aggregates REAL stats from Supabase for the frontend dashboard.

No hardcoded numbers. If the job_posts / scam_reports tables are empty or
unreachable, this returns honest zero/empty values (DashboardResponse defaults)
rather than fabricated sample statistics, so the UI can show a clear
"no data yet" state instead of misleading numbers.
"""

import logging
from collections import Counter

from backend.db.supabase import SupabaseClient
from backend.models.schemas import DashboardResponse

logger = logging.getLogger(__name__)


class DashboardService:
    def __init__(self, db: SupabaseClient):
        self.db = db

    def get_stats(self) -> DashboardResponse:
        from backend.core.config import get_settings

        settings = get_settings()
        jobs_table = settings.supabase_job_posts_table or "job_posts"
        reports_table = settings.supabase_reports_table or "scam_reports"

        try:
            jobs_resp = (
                self.db.table(jobs_table)
                .select("id, title, company_name, location, scam_score, is_flagged, created_at")
                .order("created_at", desc=True)
                .execute()
            )
            rows = getattr(jobs_resp, "data", []) or []
        except Exception as e:
            logger.warning("Dashboard: job_posts fetch failed, returning empty stats: %s", e)
            return DashboardResponse()

        if not rows:
            # No data has been analyzed yet — honest empty state, not fake numbers.
            return DashboardResponse()

        total = len(rows)
        flagged = sum(1 for r in rows if r.get("is_flagged"))
        legit = total - flagged
        scores = [float(r.get("scam_score") or 0) for r in rows]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        high_risk = sum(1 for s in scores if s > 60)

        recent = [
            {
                "id": str(r.get("id", "")),
                "title": r.get("title", ""),
                "company": r.get("company_name", ""),
                "score": round(float(r.get("scam_score") or 0), 1),
                "location": r.get("location", ""),
            }
            for r in rows
            if r.get("is_flagged")
        ][:10]

        # Top flagged companies — computed live from job_posts, not hardcoded.
        company_counter: Counter = Counter()
        for r in rows:
            if r.get("is_flagged"):
                name = (r.get("company_name") or "").strip()
                if name:
                    company_counter[name] += 1
        top_flagged_domains = dict(company_counter.most_common(8))

        # Top report reasons — live from scam_reports.
        top_reasons: dict = {}
        try:
            rep_resp = self.db.table(reports_table).select("report_reason").execute()
            rep_rows = getattr(rep_resp, "data", []) or []
            reason_counter: Counter = Counter()
            for rr in rep_rows:
                reason = (rr.get("report_reason") or "").strip()
                if reason:
                    reason_counter[reason] += 1
            top_reasons = dict(reason_counter.most_common(8))
        except Exception as e:
            logger.warning("Dashboard: scam_reports fetch failed: %s", e)

        return DashboardResponse(
            total_jobs=total,
            flagged_jobs=flagged,
            legit_jobs=legit,
            high_risk_jobs=high_risk,
            avg_scam_score=avg_score,
            report_reasons=top_reasons,
            top_flagged_domains=top_flagged_domains,
            recent_flagged=recent,
        )
