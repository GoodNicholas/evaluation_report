from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response
from starlette.requests import Request
import time

# Request metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"]
)

# Business metrics
USER_REGISTRATIONS = Counter(
    "user_registrations_total",
    "Total number of user registrations"
)

COURSE_CREATIONS = Counter(
    "course_creations_total",
    "Total number of courses created"
)

ENROLLMENTS = Counter(
    "course_enrollments_total",
    "Total number of course enrollments"
)

ASSIGNMENT_SUBMISSIONS = Counter(
    "assignment_submissions_total",
    "Total number of assignment submissions"
)

async def metrics_middleware(request: Request, call_next):
    """Middleware to collect request metrics."""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

async def metrics_endpoint(request: Request) -> Response:
    """Endpoint to expose Prometheus metrics."""
    return Response(
        generate_latest(),
        media_type="text/plain"
    ) 