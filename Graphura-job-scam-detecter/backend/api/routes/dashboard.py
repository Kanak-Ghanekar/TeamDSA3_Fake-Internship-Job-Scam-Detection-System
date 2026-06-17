from fastapi import APIRouter, Depends

from db.supabase import SupabaseClient, get_supabase_client
from models.schemas import DashboardResponse
from services.dashboard_service import DashboardService

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: SupabaseClient = Depends(get_supabase_client),
) -> DashboardResponse:
    return DashboardService(db).get_stats()
