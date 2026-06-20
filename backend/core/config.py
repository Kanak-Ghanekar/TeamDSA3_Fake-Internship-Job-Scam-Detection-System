from functools import lru_cache
import os
from typing import Any

# pyrefly: ignore [missing-import]

from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    app_name: str = "Graphura Scam Detector API"
    app_version: str = "1.0.0"
    debug: bool = False

    supabase_url: str = "https://spavuyqucbrduccrgawk.supabase.co"
    supabase_key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNwYXZ1eXF1Y2JyZHVjY3JnYXdrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA4MzQ4MjcsImV4cCI6MjA5NjQxMDgyN30.2-P6S_xaPO62l8XPJ01qsYduUeZPcZWJ-Ku0222zrw4"
    supabase_job_posts_table: str = "job_posts"
    supabase_reports_table: str = "scam_reports"
    supabase_recruiters_table: str = "recruiter_profiles"
    supabase_domains_table: str = "domain_reputation"
    supabase_flagged_table: str = "flagged_keywords"

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            "http://localhost:8080",
            "http://127.0.0.1:8000/",
            "null",  # file:// origin
        ],
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str] | Any:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    from pathlib import Path
    backend_env = Path(__file__).resolve().parent.parent / ".env"
    if backend_env.exists():
        load_dotenv(dotenv_path=backend_env)
    else:
        load_dotenv()
    return Settings(
        app_name=os.getenv("APP_NAME", "Graphura Scam Detector API"),
        app_version=os.getenv("APP_VERSION", "1.0.0"),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_key=os.getenv("SUPABASE_KEY", ""),
        supabase_job_posts_table=os.getenv("SUPABASE_JOB_POSTS_TABLE", "job_posts"),
        supabase_reports_table=os.getenv("SUPABASE_REPORTS_TABLE", "scam_reports"),
        supabase_recruiters_table=os.getenv("SUPABASE_RECRUITERS_TABLE", "recruiter_profiles"),
        supabase_domains_table=os.getenv("SUPABASE_DOMAINS_TABLE", "domain_reputation"),
        supabase_flagged_table=os.getenv("SUPABASE_FLAGGED_KEYWORDS", "flagged_keywords"),

        cors_origins=os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://localhost:5500,http://127.0.0.1:5500,http://localhost:8080,null",
        ),
    )
