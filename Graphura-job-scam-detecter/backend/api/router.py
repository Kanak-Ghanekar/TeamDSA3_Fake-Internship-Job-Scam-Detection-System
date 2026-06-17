from fastapi import APIRouter

from backend.api.routes import analyze, dashboard, domain, recruiter, report, auth
from backend.api.routes.db_health import router as db_health_router

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(analyze.router)
api_router.include_router(report.router)
api_router.include_router(recruiter.router)
api_router.include_router(domain.router)
api_router.include_router(dashboard.router)
api_router.include_router(db_health_router)
