from fastapi import APIRouter, Depends

from backend.core.config import get_settings
from backend.db.supabase import SupabaseClient, get_supabase_client
from backend.models.schemas import AnalyzeRequest, AnalyzeResponse
from backend.services.analysis_service import AnalysisService

router = APIRouter(tags=["analysis"])
analysis_service = AnalysisService()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_job(
    payload: AnalyzeRequest,
    db: SupabaseClient = Depends(get_supabase_client),
) -> AnalyzeResponse:
    settings = get_settings()
    analysis = analysis_service.analyze(payload)

    company = payload.company_name or payload.company or "Unknown"
    desc = payload.job_description or payload.description or ""
    source = payload.job_url or payload.source_url or ""
    
    domain_name = payload.domain or ""
    if not domain_name and source:
        try:
            domain_name = source.split("//")[-1].split("/")[0].replace("www.", "")
        except Exception:
            pass

    row = {
        "Title": payload.job_title or "Job Post",
        "Company_name": company,
        "Location": payload.location or "Remote",
        "Description": desc,
        "Source_URL": source,
        "Domain_name": domain_name,
        "is_flagged": analysis.scam_score >= 35,
        "Scam_score": float(analysis.scam_score),
        "Salary": str(payload.salary) if payload.salary else "0",
    }

    try:
        # Persist to job_posts table
        insert_resp = db.table(settings.supabase_job_posts_table).insert(row).execute()
        # Capture generated Report_id if returned
        data = getattr(insert_resp, "data", None)
        if data and len(data) > 0:
            analysis.recommendation = data[0].get("Report_id")  # Store generated ID in recommendation temporarily if needed, or pass it back
    except Exception as e:
        print(f"Error persisting job post to Supabase: {e}")

    return analysis