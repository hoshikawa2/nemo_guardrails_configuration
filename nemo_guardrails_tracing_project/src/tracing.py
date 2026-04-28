import os
from contextlib import contextmanager
_TRACING_ENABLED=os.getenv("ENABLE_TRACING","false").lower()=="true"
try:
    if _TRACING_ENABLED:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        provider=TracerProvider(); endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT","http://localhost:6006/v1/traces")
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        trace.set_tracer_provider(provider); tracer=trace.get_tracer("nemo_guardrails_governed_project")
    else: tracer=None
except Exception: tracer=None
@contextmanager
def span(name:str, **attrs):
    if tracer is None:
        yield None; return
    with tracer.start_as_current_span(name) as sp:
        for k,v in attrs.items(): sp.set_attribute(k,str(v))
        yield sp
