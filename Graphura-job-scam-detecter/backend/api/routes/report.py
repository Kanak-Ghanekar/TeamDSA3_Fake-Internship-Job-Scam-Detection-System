from fastapi import APIRouter, Depends

from backend.db.supabase import SupabaseClient, get_supabase_client
from backend.models.schemas import ReportRequest, ReportResponse
from backend.services.report_service import ReportService

router = APIRouter(tags=["report"])


@router.post("/report", response_model=ReportResponse)
def submit_report(
    payload: ReportRequest,
    db: SupabaseClient = Depends(get_supabase_client),
) -> ReportResponse:
    return ReportService(db).submit(payload)
