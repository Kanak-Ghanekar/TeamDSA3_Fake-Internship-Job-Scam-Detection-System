from backend.core.config import get_settings
from backend.db.supabase import SupabaseClient
from backend.models.schemas import ReportRequest, ReportResponse


class ReportService:
    def __init__(self, db: SupabaseClient):
        self.db = db
        self.settings = get_settings()

    def submit(self, payload: ReportRequest) -> ReportResponse:
        row = {
            "Job_title": payload.job_title or "Unknown",
            "Company_name": payload.company_name or "Unknown",
            "Description": payload.description or "",
            "Reporter_email": payload.reporter_email or "",
            "Reason": payload.reason or "",
            "Evidence_url": payload.evidence_url or "",
        }
        try:
            result = self.db.table(self.settings.supabase_scam_reports_table).insert(row).execute()
            data = getattr(result, "data", None)
            report_id = data[0].get("id") if data else None
            return ReportResponse(message="Report submitted successfully", report_id=report_id)
        except Exception as exc:
            return ReportResponse(message=f"Failed to submit report: {exc}", report_id=None)
