from fastapi import APIRouter, Depends
from backend.db.supabase import SupabaseClient, get_supabase_client
from backend.models.schemas import AnalyzeRequest, MLAnalyzeResponse
from backend.services.ml_analysis_service import MLAnalysisService

router = APIRouter(tags=["ml-analysis"])

@router.post("/analyze-ml", response_model=MLAnalyzeResponse)
def analyze_job_ml(
    payload: AnalyzeRequest,
    db: SupabaseClient = Depends(get_supabase_client),
) -> MLAnalyzeResponse:
    return MLAnalysisService(db).analyze(payload)
