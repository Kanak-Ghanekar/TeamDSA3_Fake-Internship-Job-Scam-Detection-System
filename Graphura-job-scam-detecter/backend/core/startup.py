import logging

from backend.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)


def validate_supabase_startup(fail_fast: bool = True) -> None:
    try:
        get_supabase_client()
        logger.info("Supabase client initialized successfully.")
    except Exception as exc:
        message = f"Supabase startup validation failed: {exc}"
        if fail_fast:
            logger.error(message)
            raise RuntimeError(message) from exc
        logger.warning(message)
