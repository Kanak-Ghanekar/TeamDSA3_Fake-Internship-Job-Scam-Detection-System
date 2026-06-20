import logging

from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.config import get_settings
from backend.db.supabase import SupabaseClient, get_supabase_client
from backend.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    AnalyzeUrlRequest,
    AnalyzeUrlResponse,
)
from backend.services.analysis_service import AnalysisService
from backend.services.scrape_service import ScrapeError, scrape_job_url

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])


def _persist_job_post(db: SupabaseClient, payload: AnalyzeRequest, analysis: AnalyzeResponse) -> None:
    """Insert the analyzed job post into Supabase using the REAL job_posts schema
    (lowercase columns — see supabase_setup.sql). Never raises; logs and returns
    on failure so a DB hiccup never breaks the user-facing analysis response."""
    settings = get_settings()

    company = payload.company_name or payload.company or "Unknown"
    source = payload.job_url or payload.source_url or ""

    domain_name = payload.domain or ""
    if not domain_name and source:
        try:
            domain_name = source.split("//")[-1].split("/")[0].replace("www.", "")
        except Exception:
            pass

    row = {
        "title": payload.job_title or payload.title or "Job Post",
        "company_name": company,
        "location": payload.location or "Remote",
        "scam_score": float(analysis.scam_score),
        "is_flagged": analysis.is_flagged,
    }

    try:
        db.table(settings.supabase_job_posts_table).insert(row).execute()
    except Exception as e:
        logger.warning("Could not persist job post to Supabase (%s): %s", row.get("title"), e)


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_job(
    payload: AnalyzeRequest,
    db: SupabaseClient = Depends(get_supabase_client),
) -> AnalyzeResponse:
    analysis_service = AnalysisService(db)
    analysis = analysis_service.analyze(payload)
    _persist_job_post(db, payload, analysis)
    return analysis


@router.post("/analyze-url", response_model=AnalyzeUrlResponse)
def analyze_job_url(
    payload: AnalyzeUrlRequest,
    db: SupabaseClient = Depends(get_supabase_client),
) -> AnalyzeUrlResponse:
    """
    Paste a job posting URL from any platform — this endpoint scrapes the page
    server-side, extracts the job fields, runs the same real ML/heuristic +
    Supabase-backed analysis used by /analyze, and returns both the scraped
    fields (so the UI can show what was found) and the full risk analysis.
    """
    try:
        scraped = scrape_job_url(payload.url)
    except ScrapeError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "SCRAPE_FAILED",
                    "message": str(e),
                }
            },
        )

    analyze_payload = AnalyzeRequest(
        job_title=scraped.get("title", ""),
        company_name=scraped.get("company", ""),
        job_description=scraped.get("description", ""),
        salary=scraped.get("salary", ""),
        location=scraped.get("location", ""),
        job_url=scraped.get("source_url", payload.url),
        domain=scraped.get("domain", ""),
        recruiter_email=payload.recruiter_email,
    )

    analysis_service = AnalysisService(db)
    analysis = analysis_service.analyze(analyze_payload)
    _persist_job_post(db, analyze_payload, analysis)

    return AnalyzeUrlResponse(
        scraped_title=scraped.get("title", ""),
        scraped_company=scraped.get("company", ""),
        scraped_location=scraped.get("location", ""),
        scraped_salary=scraped.get("salary", ""),
        scraped_description=scraped.get("description", ""),
        domain=scraped.get("domain", ""),
        source_url=scraped.get("source_url", payload.url),
        extraction_method=scraped.get("extraction_method", "unknown"),
        partial_extraction=scraped.get("partial", False),
        analysis=analysis,
    )
