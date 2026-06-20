from functools import lru_cache
from typing import Any

from fastapi import HTTPException, status
from supabase import Client, create_client

from backend.core.config import get_settings

SupabaseClient = Client

@lru_cache
def get_supabase_client() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "SUPABASE_NOT_CONFIGURED",
                    "message": "Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY.",
                }
            },
        )
    return create_client(settings.supabase_url, settings.supabase_key)


def unwrap_supabase_data(response: Any) -> Any:
    return getattr(response, "data", response)

def test_supabase_connection(db: Client, table: str) -> None:
    """Performs a lightweight query to confirm connectivity/auth/table access."""
    # limit(1) keeps it cheap. Try different columns to prevent schema errors.
    try:
        db.table(table).select("id").limit(1).execute()
    except Exception:
        try:
            db.table(table).select("Report_id").limit(1).execute()
        except Exception:
            db.table(table).select("*").limit(1).execute()


