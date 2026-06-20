from fastapi import APIRouter, Depends

from backend.db.supabase import SupabaseClient, get_supabase_client
from backend.models.schemas import DashboardResponse
from backend.services.dashboard_service import DashboardService

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: SupabaseClient = Depends(get_supabase_client),
) -> DashboardResponse:
    return DashboardService(db).get_stats()
