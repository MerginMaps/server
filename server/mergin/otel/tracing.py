# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

"""Helpers for custom spans. Safe to use when OTel is disabled - the API then falls back to no-op tracer."""

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional
from celery import current_app
from opentelemetry import trace
from opentelemetry.trace import Span, SpanKind, Status, StatusCode

tracer = trace.get_tracer("mergin")

# avoid exporting huge geodiff logs as span status
MAX_STATUS_LENGTH = 2048

# span names of celery tasks as created by opentelemetry-instrumentation-celery: run/<task> (worker)
# and apply_async/<task> (sender), manual celery tracing (OTEL_MANUAL_CELERY_TRACING) follows the same convention
CELERY_SPAN_PREFIXES = ("run/", "apply_async/")


@dataclass
class TracedStep:
    span: Span
    duration: float = 0.0  # in seconds, set when block exits


@contextmanager
def traced(
    name: str, attributes: Optional[dict] = None, kind: SpanKind = SpanKind.INTERNAL
):
    """Run block in a child span of current span.
    Yields TracedStep with measured duration for consumers outside OTel (e.g. GeodiffActionHistory).
    Exceptions propagating through the block are recorded on the span automatically.
    Use kind=SpanKind.CLIENT for calls to other services.
    """
    with tracer.start_as_current_span(name, kind=kind, attributes=attributes) as span:
        step = TracedStep(span)
        start = time.perf_counter()
        try:
            yield step
        finally:
            step.duration = time.perf_counter() - start


def set_span_attributes(attributes: dict) -> None:
    """Add attributes to current span"""
    trace.get_current_span().set_attributes(attributes)


def mark_span_failed(message: str) -> None:
    """Mark current span as failed, e.g. for handled errors which do not propagate"""
    trace.get_current_span().set_status(
        Status(StatusCode.ERROR, message[:MAX_STATUS_LENGTH])
    )


def is_untraced_celery_task_span(span_name: str) -> bool:
    """Check if span belongs to celery task excluded from tracing with task option, e.g.
    @celery.task(untraced=True) for frequent periodic tasks without any value in traces.
    """
    for prefix in CELERY_SPAN_PREFIXES:
        if span_name.startswith(prefix):
            task = current_app.tasks.get(span_name[len(prefix) :])
            return getattr(task, "untraced", False)
    return False
