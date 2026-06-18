from backend.core.config import get_settings
from backend.db.supabase import SupabaseClient
from backend.models.schemas import ReportRequest, ReportResponse


class ReportService:
    def __init__(self, db: SupabaseClient):
        self.db = db
        self.settings = get_settings()

    def submit(self, payload: ReportRequest) -> ReportResponse:
        row = {
            "job_id": payload.job_id,
            "report_reason": payload.report_reason,
            "user_comment": payload.user_comment or "",
            "severity": payload.severity,
        }
        try:
            result = self.db.table(self.settings.supabase_scam_reports_table).insert(row).execute()
            data = getattr(result, "data", None)
            report_id = data[0].get("id") if data else None
            return ReportResponse(message="Report submitted successfully", report_id=report_id)
        except Exception as exc:
            return ReportResponse(message=f"Failed to submit report: {exc}", report_id=None)
