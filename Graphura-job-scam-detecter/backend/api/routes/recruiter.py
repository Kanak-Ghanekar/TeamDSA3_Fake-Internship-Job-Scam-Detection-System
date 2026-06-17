from fastapi import APIRouter, Depends

from backend.db.supabase import SupabaseClient, get_supabase_client
from backend.models.schemas import RecruiterCheckRequest, RecruiterCheckResponse
from backend.services.recruiter_service import RecruiterService

router = APIRouter(tags=["recruiter"])


@router.post("/recruiter-check", response_model=RecruiterCheckResponse)
def check_recruiter(
    payload: RecruiterCheckRequest,
    db: SupabaseClient = Depends(get_supabase_client),
) -> RecruiterCheckResponse:
    return RecruiterService(db).check(payload)
