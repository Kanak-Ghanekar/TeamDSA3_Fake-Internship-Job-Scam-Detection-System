"""
Report Service — saves a user scam report to Supabase.
Falls back to a local JSON log if Supabase is unavailable.

Also defensively handles the case where the live Supabase table is missing
a column the app expects (PostgREST error PGRST204, "Could not find the
'X' column..."). Rather than failing the whole report, we detect exactly
which column PostgREST says is missing, drop only that field, and retry
once. This means a schema drift between this codebase and your actual
Supabase table doesn't block reporting — and if you later add the missing
column in Supabase, the full data starts saving again automatically with
no code change needed.
"""

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.db.supabase import SupabaseClient
from backend.models.schemas import ReportRequest, ReportResponse

logger = logging.getLogger(__name__)

LOCAL_REPORTS_FILE = Path(__file__).resolve().parent.parent / "local_reports.json"

# Matches PostgREST's "Could not find the 'company_name' column of
# 'scam_reports' in the schema cache" style error message.
_MISSING_COLUMN_RE = re.compile(r"Could not find the '([^']+)' column")


def _local_save(data: dict) -> None:
    try:
        existing: list = []
        if LOCAL_REPORTS_FILE.exists():
            with open(LOCAL_REPORTS_FILE, "r") as f:
                existing = json.load(f)
        existing.append(data)
        with open(LOCAL_REPORTS_FILE, "w") as f:
            json.dump(existing, f, indent=2, default=str)
    except Exception as e:
        logger.error("Local report save failed: %s", e)


class ReportService:
    def __init__(self, db: SupabaseClient):
        self.db = db

    def create_report(self, payload: ReportRequest) -> ReportResponse:
        report_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        record = {
            "report_id": report_id,
            "job_id": payload.job_id,
            "job_title": payload.job_title,
            "company_name": payload.company_name,
            "report_reason": payload.report_reason,
            "user_comment": payload.user_comment,
            "severity": payload.severity,
            "reporter_email": payload.reporter_email,
            "reported_at": now,
        }

        settings = __import__("backend.core.config", fromlist=["get_settings"]).get_settings()
        table = settings.supabase_reports_table or "scam_reports"

        dropped_fields: list = []
        attempt = dict(record)

        # Try the insert; if Supabase/PostgREST reports a specific missing
        # column, drop just that field and retry — up to a small number of
        # times in case more than one column is missing from the live table.
        for _ in range(len(record)):
            try:
                self.db.table(table).insert(attempt).execute()
                if dropped_fields:
                    logger.warning(
                        "Report saved to Supabase, but these fields don't exist in "
                        "the live '%s' table and were dropped: %s. Add the column(s) "
                        "in Supabase to start saving this data again.",
                        table, dropped_fields,
                    )
                    return ReportResponse(
                        report_id=report_id,
                        message=(
                            "Report submitted, but your Supabase 'scam_reports' table "
                            f"is missing the column(s) {', '.join(dropped_fields)}, so "
                            "that part of the report wasn't saved. Add the missing "
                            "column(s) in Supabase to capture this data going forward."
                        ),
                        success=True,
                        saved_to_database=True,
                    )
                return ReportResponse(
                    report_id=report_id,
                    message="Report submitted successfully. Thank you for helping keep the community safe.",
                    success=True,
                    saved_to_database=True,
                )
            except Exception as e:
                match = _MISSING_COLUMN_RE.search(str(e))
                if match and match.group(1) in attempt:
                    missing_col = match.group(1)
                    dropped_fields.append(missing_col)
                    del attempt[missing_col]
                    logger.warning(
                        "Supabase insert failed: column '%s' missing from '%s'. "
                        "Retrying without it.", missing_col, table,
                    )
                    continue
                # Not a recognizable missing-column error — give up and fall
                # back to local storage, being honest about it.
                logger.warning("Supabase insert failed, saving locally: %s", e)
                _local_save(record)
                return ReportResponse(
                    report_id=report_id,
                    message=(
                        "We couldn't reach the shared database right now, so your report "
                        "was saved locally instead. It won't appear in the community feed "
                        "or dashboard until this is resolved. "
                        f"Details: {e}"
                    ),
                    success=True,
                    saved_to_database=False,
                )

        # Exhausted retries without success (shouldn't normally happen).
        logger.warning("Supabase insert failed after dropping columns %s, saving locally", dropped_fields)
        _local_save(record)
        return ReportResponse(
            report_id=report_id,
            message=(
                "We couldn't save your report to the shared database after several "
                "attempts, so it was saved locally instead."
            ),
            success=True,
            saved_to_database=False,
        )
