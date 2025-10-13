import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor

# Setup OpenTelemetry Tracer
provider = TracerProvider()
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

def get_tracer(module_name: str):
    """Returns a new tracer for a given module name."""
    return trace.get_tracer(module_name)

def start_trace(name: str):
    """Starts a new span and returns it."""
    tracer = get_tracer(__name__)
    return tracer.start_as_current_span(name)

def end_trace(span):
    """Ends a span."""
    if span:
        span.end()
