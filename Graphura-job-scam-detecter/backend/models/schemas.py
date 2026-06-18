from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    company: Optional[str] = None
    job_description: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    job_url: Optional[str] = None
    source_url: Optional[str] = None
    domain: Optional[str] = None
    email: Optional[str] = None


class AnalyzeResponse(BaseModel):
    scam_score: float
    is_flagged: bool = False
    recommendation: Optional[str] = None
    reasons: list[str] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    total_jobs: int = 0
    flagged_jobs: int = 0
    average_scam_score: float = 0.0
    top_flagged_domains: list[str] = Field(default_factory=list)


class DbHealthResponse(BaseModel):
    status: str
    supabase_connected: bool
    message: Optional[str] = None


class DomainCheckRequest(BaseModel):
    domain: str


class DomainCheckResponse(BaseModel):
    domain: str
    is_suspicious: bool
    reputation_score: float
    reasons: list[str] = Field(default_factory=list)


class RecruiterCheckRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    linkedin_url: Optional[str] = None


class RecruiterCheckResponse(BaseModel):
    is_verified: bool
    risk_score: float
    reasons: list[str] = Field(default_factory=list)
    

class ReportRequest(BaseModel):
    job_id: Optional[str] = None
    report_reason: str
    user_comment: Optional[str] = None
    severity: float = 50.0


class ReportResponse(BaseModel):
    message: str
    report_id: Optional[str] = None
