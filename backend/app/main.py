from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import structlog
from structlog.stdlib import ProcessorFormatter
import logging
import sys

from app.api.routes import (
    auth,
    course,
    gradebook,
    health,
    message,
    notification,
    telegram,
    users,
    courses,
    chat,
    course_role,
)
from app.core.config import settings
from app.db.session import async_session
from app.services.telegram import TelegramBot
from app.core.logging import get_logger, log_request, log_response, log_error
from app.core.metrics import metrics_middleware, metrics_endpoint
from app.core.tracing import setup_tracing

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Configure standard library logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=settings.LOG_LEVEL,
    force=True,
)

logger = structlog.get_logger()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up metrics middleware
app.middleware("http")(metrics_middleware)

# Set up tracing
setup_tracing(app)

# Add metrics endpoint
app.add_route("/metrics", metrics_endpoint)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", "")
    start_time = time.time()
    
    try:
        log_request(logger, request_id, request.method, str(request.url))
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000
        log_response(logger, request_id, request.method, str(request.url), response.status_code, duration)
        return response
    except Exception as e:
        log_error(logger, request_id, request.method, str(request.url), e)
        raise

# Include routers
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(courses.router, prefix=settings.API_V1_STR)
app.include_router(gradebook.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(notification.router, prefix=settings.API_V1_STR)
app.include_router(course_role.router, prefix=settings.API_V1_STR)
app.include_router(telegram.router, prefix=settings.API_V1_STR)

# Telegram bot
telegram_bot = None


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    global telegram_bot
    async with async_session() as session:
        telegram_bot = TelegramBot(session)
        await telegram_bot.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    if telegram_bot:
        await telegram_bot.stop()


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "0.0.1",
        "time": datetime.now(timezone.utc).isoformat(),
    } 