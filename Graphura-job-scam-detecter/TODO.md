# TODO - Graphura Scam Detector Backend Workflow Integration

## Phase 1: Supabase configuration
- [ ] Add startup validation for required SUPABASE_* env vars
- [ ] Add `/db-health` endpoint that tests Supabase connectivity
- [ ] Enhance Supabase dependency with test helper

## Phase 2: Error handling
- [ ] Add global exception handler for validation errors
- [ ] Add standardized JSON error responses
- [ ] Map Supabase/database errors to stable error codes

## Phase 3: Workflow validation & persistence
- [ ] Confirm `/analyze` persists to `job_posts` with correct fields
- [ ] Confirm `/report` persists to `scam_reports` with correct fields

## Phase 4: Recruiter + Domain workflows
- [ ] Update recruiter-check to query `recruiters` table
- [ ] Update domain-check to query `domains` table + normalize domain

## Phase 5: Dashboard
- [ ] Ensure dashboard uses persisted `risk_level` for accurate stats

## Phase 6: ML-ready architecture (no ML prediction yet)
- [ ] Add `backend/ml/model_service.py` placeholder with load/predict/predict_proba
- [ ] Add feature engineering layer that can plug ML later

## Phase 7: Testing
- [ ] Add `tests/test_analyze.py`
- [ ] Add `tests/test_report.py`
- [ ] Add `tests/test_recruiter.py`
- [ ] Add `tests/test_domain.py`
- [ ] Add `tests/test_dashboard.py`

## Phase 8: Frontend compatibility checks
- [ ] Verify frontend JS payloads match backend Pydantic schemas

