from fastapi import APIRouter, Depends

from backend.core.config import get_settings
from backend.db.supabase import SupabaseClient, get_supabase_client
from backend.models.schemas import (
    RecruiterCheckRequest,
    RecruiterCheckResponse,
    RecruiterListResponse,
)
from backend.services.recruiter_service import RecruiterService

router = APIRouter(tags=["recruiter"])


@router.post("/recruiter-check", response_model=RecruiterCheckResponse)
def check_recruiter(
    payload: RecruiterCheckRequest,
    db: SupabaseClient = Depends(get_supabase_client),
) -> RecruiterCheckResponse:
    return RecruiterService(db).check(payload)


@router.get("/recruiters", response_model=RecruiterListResponse)
def list_recruiters(
    db: SupabaseClient = Depends(get_supabase_client),
) -> RecruiterListResponse:
    """Lists recruiter profiles from Supabase for the database browser table.
    Returns an empty list (not fake rows) if the table is empty or unreachable."""
    settings = get_settings()
    table = settings.supabase_recruiters_table or "recruiter_profiles"
    try:
        resp = db.table(table).select(
            "email, company, recruiter_name, verified, previous_reports, linkedin_url"
        ).limit(200).execute()
        rows = getattr(resp, "data", []) or []
    except Exception:
        rows = []
    return RecruiterListResponse(recruiters=rows)
