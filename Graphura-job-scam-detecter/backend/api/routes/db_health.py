from __future__ import annotations

from fastapi import APIRouter, Depends
from supabase import Client

from backend.db.supabase import SupabaseClient, get_supabase_client
from backend.models.schemas import DbHealthResponse
from backend.services.health_service import HealthService

router = APIRouter(tags=["health"])


@router.get("/db-health", response_model=DbHealthResponse)
def db_health(db: SupabaseClient = Depends(get_supabase_client)) -> DbHealthResponse:
    return HealthService(db).db_health()

