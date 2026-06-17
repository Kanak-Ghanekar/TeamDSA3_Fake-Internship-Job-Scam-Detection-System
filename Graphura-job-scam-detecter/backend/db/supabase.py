from functools import lru_cache

from supabase import Client as SupabaseClient
from supabase import create_client

from backend.core.config import get_settings

__all__ = ["SupabaseClient", "get_supabase_client"]


@lru_cache
def get_supabase_client() -> SupabaseClient:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)
