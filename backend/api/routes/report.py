from fastapi import APIRouter, Depends, status

from backend.core.config import get_settings
from backend.db.supabase import SupabaseClient, get_supabase_client
from backend.models.schemas import ReportListResponse, ReportRequest, ReportResponse
from backend.services.report_service import ReportService


router = APIRouter(tags=["reports"])


@router.post("/report", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    payload: ReportRequest,
    db: SupabaseClient = Depends(get_supabase_client),
) -> ReportResponse:
    return ReportService(db).create_report(payload)


@router.get("/reports", response_model=ReportListResponse)
def list_reports(
    db: SupabaseClient = Depends(get_supabase_client),
) -> ReportListResponse:
    """Lists scam reports from Supabase, most recent first, for the report feed
    and table. Returns an empty list (not seeded examples) if there's no data."""
    settings = get_settings()
    table = settings.supabase_reports_table or "scam_reports"
    try:
        resp = (
            db.table(table)
            .select("report_id, job_title, company_name, report_reason, user_comment, severity, reported_at")
            .order("reported_at", desc=True)
            .limit(200)
            .execute()
        )
        rows = getattr(resp, "data", []) or []
    except Exception:
        rows = []
    return ReportListResponse(reports=rows)
