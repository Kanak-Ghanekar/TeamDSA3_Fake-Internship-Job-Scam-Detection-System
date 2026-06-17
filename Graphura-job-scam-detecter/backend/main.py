import logging
import os
import time
from typing import Callable
from uuid import uuid4

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from postgrest.exceptions import APIError as PostgrestAPIError
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from api.router import api_router
from backend.core.config import get_settings
from backend.core.logging import setup_logging

settings = get_settings()

setup_logging()



logger = logging.getLogger(__name__)



class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id

        start = time.perf_counter()
        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            status_code = getattr(response, "status_code", "-")
            logger.info(
                "request completed",
                extra={
                    "request_id": request_id,
                    "path": str(request.url.path),
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

app.add_middleware(RequestLoggingMiddleware)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(api_router, prefix="/api")


@app.get("/")
def read_root():
    return {
        "app": "Fake Internship & Job Scam Detection System Backend",
        "status": "online",
        "documentation": "/docs"
    }


@app.on_event("startup")
async def startup_event() -> None:
    # Fail fast on missing Supabase configuration.
    from backend.core.startup import validate_supabase_startup

    validate_supabase_startup(fail_fast=not settings.debug)


# Exception handlers

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = request.headers.get("X-Request-ID") or getattr(
        getattr(request, "state", None), "request_id", "-"
    )
    details = exc.errors()
    msg = "Validation failed for request parameters or body."
    return JSONResponse(
        status_code=422,
        content={
            "detail": msg,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": msg,
                "details": details,
                "request_id": request_id,
            }
        }
    )

@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    request_id = request.headers.get("X-Request-ID") or getattr(
        getattr(request, "state", None), "request_id", "-"
    )
    details = exc.errors()
    msg = "Data validation failed."
    return JSONResponse(
        status_code=422,
        content={
            "detail": msg,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": msg,
                "details": details,
                "request_id": request_id,
            }
        }
    )

@app.exception_handler(PostgrestAPIError)
async def postgrest_exception_handler(request: Request, exc: PostgrestAPIError):
    request_id = request.headers.get("X-Request-ID") or getattr(
        getattr(request, "state", None), "request_id", "-"
    )
    logger.exception("Supabase database error", extra={"request_id": request_id})
    db_message = exc.message or str(exc)
    status_code = getattr(exc, "status", 500)
    
    if status_code in (502, 503, 504) or "connection" in db_message.lower():
        error_code = "SUPABASE_CONNECTION_ERROR"
        msg = "Could not connect to Supabase database."
    else:
        error_code = "SUPABASE_DB_ERROR"
        msg = f"Database operation failed: {db_message}"
        
    return JSONResponse(
        status_code=500,
        content={
            "detail": msg,
            "error": {
                "code": error_code,
                "message": msg,
                "details": {
                    "hint": getattr(exc, "hint", None),
                    "code": getattr(exc, "code", None),
                    "details": getattr(exc, "details", None),
                },
                "request_id": request_id,
            }
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = request.headers.get("X-Request-ID") or getattr(
        getattr(request, "state", None), "request_id", "-"
    )
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        error_info = detail["error"]
        code = error_info.get("code", "INTERNAL_ERROR")
        msg = error_info.get("message", "HTTP exception occurred.")
        details = error_info.get("details", None)
    else:
        code = "INTERNAL_ERROR"
        msg = str(detail)
        details = None
        
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": msg,
            "error": {
                "code": code,
                "message": msg,
                "details": details,
                "request_id": request_id,
            }
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = request.headers.get("X-Request-ID") or getattr(
        getattr(request, "state", None), "request_id", "-"
    )

    logger.exception("unhandled exception", extra={"request_id": request_id})
    message = str(exc) if settings.debug else "Internal Server Error"
    return JSONResponse(
        status_code=500,
        content={
            "detail": message,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": message,
                "request_id": request_id,
            }
        },
    )





@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
