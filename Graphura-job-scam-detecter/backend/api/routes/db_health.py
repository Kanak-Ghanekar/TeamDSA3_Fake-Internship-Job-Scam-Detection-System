from __future__ import annotations

from fastapi import APIRouter, Depends
from supabase import Client

from db.supabase import SupabaseClient, get_supabase_client
from models.schemas import DbHealthResponse
from services.health_service import HealthService

router = APIRouter(tags=["health"])


@router.get("/db-health", response_model=DbHealthResponse)
def db_health(db: SupabaseClient = Depends(get_supabase_client)) -> DbHealthResponse:
    return HealthService(db).db_health()

