from fastapi import APIRouter, Depends

from backend.db.supabase import SupabaseClient, get_supabase_client
from backend.models.schemas import DomainCheckRequest, DomainCheckResponse
from backend.services.domain_service import DomainService

router = APIRouter(tags=["domain"])


@router.post("/domain-check", response_model=DomainCheckResponse)
def check_domain(
    payload: DomainCheckRequest,
    db: SupabaseClient = Depends(get_supabase_client),
) -> DomainCheckResponse:
    return DomainService(db).check(payload)
