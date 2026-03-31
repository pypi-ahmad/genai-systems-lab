"""Optional OpenTelemetry bootstrap for the platform.

Activate by calling :func:`setup_otel` at application startup **before**
any logger is created.  When the ``opentelemetry`` packages are not installed
every function degrades gracefully to a no-op.

Environment variables
---------------------
``OTEL_ENABLED``
    Set to ``"1"`` or ``"true"`` to enable the OTLP exporter at startup.
``OTEL_SERVICE_NAME``
    Service name reported to the collector.  Defaults to
    ``"genai-systems-lab"``.
``OTEL_EXPORTER_OTLP_ENDPOINT``
    gRPC endpoint for the OTLP exporter.  Defaults to
    ``"http://localhost:4317"``.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Lazy imports — avoid hard dependency on opentelemetry-*
# ---------------------------------------------------------------------------
_tracer_provider: Any | None = None
_NOOP = True  # flipped to False once OTel is configured


def _try_import():
    """Return the OTel modules or ``None`` if not installed."""
    try:
        from opentelemetry import trace  # type: ignore[import-untyped]
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore[import-untyped]
        from opentelemetry.sdk.trace.export import (  # type: ignore[import-untyped]
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )

        return trace, TracerProvider, BatchSpanProcessor, ConsoleSpanExporter
    except ImportError:
        return None


def _try_import_otlp():
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (  # type: ignore[import-untyped]
            OTLPSpanExporter,
        )

        return OTLPSpanExporter
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def setup_otel(
    *,
    service_name: str | None = None,
    otlp_endpoint: str | None = None,
    console_export: bool = False,
) -> bool:
    """Initialise OpenTelemetry tracing.

    Returns *True* when OTel was successfully configured, *False* otherwise
    (missing packages, etc.).
    """
    global _tracer_provider, _NOOP

    imports = _try_import()
    if imports is None:
        return False

    trace, TracerProvider, BatchSpanProcessor, ConsoleSpanExporter = imports

    svc = service_name or os.getenv("OTEL_SERVICE_NAME", "genai-systems-lab")
    _tracer_provider = TracerProvider()

    # OTLP exporter (gRPC)
    endpoint = otlp_endpoint or os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://localhost:4317",
    )
    OTLPSpanExporter = _try_import_otlp()
    if OTLPSpanExporter is not None:
        _tracer_provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
        )

    if console_export:
        _tracer_provider.add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )

    trace.set_tracer_provider(_tracer_provider)
    _NOOP = False
    return True


def get_tracer(name: str = "genai-systems-lab") -> Any:
    """Return an OTel ``Tracer`` (or a no-op stub)."""
    try:
        from opentelemetry import trace  # type: ignore[import-untyped]

        return trace.get_tracer(name)
    except ImportError:
        return _NoopTracer()


@contextmanager
def span(
    name: str,
    *,
    attributes: dict[str, str] | None = None,
) -> Generator[Any, None, None]:
    """Start a traced span.  Falls back to a no-op context when OTel is absent.

    Usage::

        with span("run_project", attributes={"project": name}):
            do_work()
    """
    tracer = get_tracer()
    if _NOOP:
        yield None
        return

    with tracer.start_as_current_span(name, attributes=attributes or {}) as s:
        yield s


def shutdown() -> None:
    """Flush pending spans and shut down the tracer provider."""
    if _tracer_provider is not None and hasattr(_tracer_provider, "shutdown"):
        _tracer_provider.shutdown()


# ---------------------------------------------------------------------------
# No-op fallbacks
# ---------------------------------------------------------------------------
class _NoopSpan:
    """Minimal stand-in when OTel is not installed."""

    def set_attribute(self, key: str, value: Any) -> None:  # noqa: ARG002
        pass

    def set_status(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        pass

    def record_exception(self, exc: BaseException) -> None:  # noqa: ARG002
        pass


class _NoopTracer:
    @contextmanager
    def start_as_current_span(self, name: str, **kwargs: Any) -> Generator[_NoopSpan, None, None]:  # noqa: ARG002
        yield _NoopSpan()
