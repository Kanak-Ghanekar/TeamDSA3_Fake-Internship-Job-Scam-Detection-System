from backend.db.supabase import SupabaseClient
from backend.models.schemas import DbHealthResponse


class HealthService:
    def __init__(self, db: SupabaseClient):
        self.db = db

    def db_health(self) -> DbHealthResponse:
        try:
            self.db.table("job_posts").select("Report_id").limit(1).execute()
            return DbHealthResponse(status="ok", supabase_connected=True)
        except Exception as exc:
            return DbHealthResponse(status="error", supabase_connected=False, message=str(exc))
