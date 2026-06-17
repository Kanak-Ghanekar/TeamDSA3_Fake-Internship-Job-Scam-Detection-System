from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Fake Internship & Job Scam Detection System Backend"
    app_version: str = "1.0.0"
    debug: bool = False

    supabase_url: str
    supabase_key: str

    supabase_job_posts_table: str = "job_posts"
    supabase_recruiter_table: str = "recruiter_profiles"
    supabase_scam_reports_table: str = "scam_reports"
    supabase_domain_table: str = "domain_reputation"
    supabase_keywords_table: str = "flagged_keywords"

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
