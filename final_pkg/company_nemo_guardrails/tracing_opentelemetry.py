import os
from contextlib import contextmanager

_TRACING_ENABLED = os.getenv("ENABLE_TRACING", "false").lower() == "true"

tracer = None

if _TRACING_ENABLED:
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        endpoint = os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT",
            "http://localhost:6006/v1/traces"
        )

        # ✅ Define metadata do serviço (IMPORTANTE pro Phoenix)
        resource = Resource.create({
            "service.name": "nemo_guardrails_governed_project"
        })

        provider = TracerProvider(resource=resource)

        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            timeout=5  # evita travamentos
        )

        span_processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(span_processor)

        # ✅ Evita sobrescrever provider existente
        if not isinstance(trace.get_tracer_provider(), TracerProvider):
            trace.set_tracer_provider(provider)

        tracer = trace.get_tracer(__name__)

    except Exception as e:
        print(f"[Tracing Disabled] Error initializing tracing: {e}")
        tracer = None


@contextmanager
def span(name: str, **attrs):
    if tracer is None:
        yield None
        return

    try:
        with tracer.start_as_current_span(name) as sp:
            for k, v in attrs.items():
                # ✅ mantém tipo quando possível
                if isinstance(v, (str, int, float, bool)):
                    sp.set_attribute(k, v)
                else:
                    sp.set_attribute(k, str(v))
            yield sp
    except Exception as e:
        print(f"[Tracing Error] Span '{name}' failed: {e}")
        yield None