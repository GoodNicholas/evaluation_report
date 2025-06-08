import logging
import sys
from datetime import datetime
from typing import Any, Dict

import structlog
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
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

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)

def add_trace_context(logger: structlog.BoundLogger, **kwargs: Any) -> structlog.BoundLogger:
    """Add OpenTelemetry trace context to the logger."""
    current_span = trace.get_current_span()
    if current_span.is_recording():
        context = {
            "trace_id": format(current_span.get_span_context().trace_id, "032x"),
            "span_id": format(current_span.get_span_context().span_id, "016x"),
        }
        return logger.bind(**context, **kwargs)
    return logger.bind(**kwargs)

def log_request(logger: structlog.BoundLogger, request_id: str, method: str, url: str) -> None:
    """Log an incoming request."""
    add_trace_context(logger).info(
        "request_started",
        request_id=request_id,
        method=method,
        url=url,
    )

def log_response(
    logger: structlog.BoundLogger,
    request_id: str,
    method: str,
    url: str,
    status_code: int,
    duration_ms: float,
) -> None:
    """Log a response."""
    add_trace_context(logger).info(
        "request_finished",
        request_id=request_id,
        method=method,
        url=url,
        status_code=status_code,
        duration_ms=duration_ms,
    )

def log_error(
    logger: structlog.BoundLogger,
    request_id: str,
    method: str,
    url: str,
    error: Exception,
) -> None:
    """Log an error."""
    add_trace_context(logger).error(
        "request_failed",
        request_id=request_id,
        method=method,
        url=url,
        error_type=type(error).__name__,
        error_message=str(error),
        exc_info=True,
    ) 