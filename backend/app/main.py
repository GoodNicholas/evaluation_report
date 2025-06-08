from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from structlog import get_logger

logger = get_logger()

app = FastAPI(
    title="Evaluation Report API",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "0.0.1",
        "time": datetime.now(timezone.utc).isoformat(),
    } 