from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import settings

def setup_tracing(app):
    """Set up OpenTelemetry tracing."""
    # Create a resource with service information
    resource = Resource.create({
        "service.name": "lms-backend",
        "service.version": "1.0.0",
        "deployment.environment": settings.ENVIRONMENT,
    })

    # Create a tracer provider
    tracer_provider = TracerProvider(resource=resource)

    # Create an OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.OTLP_ENDPOINT,
        insecure=settings.OTLP_INSECURE,
    )

    # Add the exporter to the tracer provider
    tracer_provider.add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )

    # Set the tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=tracer_provider,
        excluded_urls="health,metrics",
    )

def get_tracer(name: str):
    """Get a tracer instance."""
    return trace.get_tracer(name) 