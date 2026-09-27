"""AI Career Copilot API entrypoint."""
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import AppError, RateLimitExceededError
from app.core.logging import (
    configure_logging,
    get_logger,
    log_event,
    new_request_id,
    request_id_var,
)
from app.core.rate_limit import SlidingWindowRateLimiter

configure_logging()
logger = get_logger(__name__)
settings = get_settings()

app = FastAPI(
    title="AI Career Copilot API",
    description="AI-powered resume analysis, job matching, skill-gap analysis"
                " and interview preparation.",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

rate_limiter = SlidingWindowRateLimiter(settings.rate_limit_per_minute)


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    """Request id + structured access log + security headers + rate limit."""
    request_id = new_request_id()
    request_id_var.set(request_id)
    started = time.perf_counter()

    client_ip = request.client.host if request.client else "unknown"
    if request.url.path.startswith("/api"):
        try:
            rate_limiter.check(client_ip)
        except RateLimitExceededError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"code": exc.code, "message": exc.message,
                         "request_id": request_id},
            )

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    log_event(
        logger, "request",
        endpoint=f"{request.method} {request.url.path}",
        status=response.status_code,
        latency_ms=round((time.perf_counter() - started) * 1000),
    )
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message,
                 "request_id": request_id_var.get()},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(p) for p in first.get("loc", []) if p != "body")
    message = f"{location}: {first.get('msg', 'invalid input')}" if location else "Invalid input."
    return JSONResponse(
        status_code=422,
        content={"code": "validation_failed", "message": message,
                 "request_id": request_id_var.get()},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_error")
    return JSONResponse(
        status_code=500,
        content={"code": "internal_error",
                 "message": "Something went wrong. Please try again.",
                 "request_id": request_id_var.get()},
    )


@app.get("/health", tags=["health"])
def health() -> dict:
    from app.ai.embeddings.factory import get_embedding_provider

    return {
        "status": "ok",
        "environment": settings.environment,
        "llm_provider": settings.llm_provider,
        "embedding_provider": get_embedding_provider().name,
    }


app.include_router(api_router)
