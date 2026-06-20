from __future__ import annotations

import logging
from typing import Iterable

from backend.core.config import get_settings

logger = logging.getLogger(__name__)


def get_missing_supabase_env_vars(settings=None) -> list[str]:
    settings = settings or get_settings()

    missing: list[str] = []
    if not settings.supabase_url:
        missing.append("SUPABASE_URL")
    if not settings.supabase_key:
        missing.append("SUPABASE_KEY")

    # Table names are optional only in config, but required by workflow.
    if not settings.supabase_job_posts_table:
        missing.append("SUPABASE_JOB_POSTS_TABLE")
    if not settings.supabase_reports_table:
        missing.append("SUPABASE_REPORTS_TABLE")
    if not settings.supabase_recruiters_table:
        missing.append("SUPABASE_RECRUITERS_TABLE")
    if not settings.supabase_domains_table:
        missing.append("SUPABASE_DOMAINS_TABLE")

    return missing


def validate_supabase_startup(*, fail_fast: bool = True) -> None:
    missing = get_missing_supabase_env_vars()
    if not missing:
        return

    logger.error("Missing required Supabase configuration env vars: %s", ", ".join(missing))

    if fail_fast:
        raise RuntimeError(
            "Supabase is not configured. Missing: " + ", ".join(missing)
        )

