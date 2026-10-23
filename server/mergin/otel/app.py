# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import time
from celery.signals import (
    task_postrun,
    worker_process_init,
    task_prerun,
    task_retry,
    beat_init,
)
from opentelemetry import trace, propagate, context, metrics

from ..app import db
from ..config import Configuration as AppConfiguration
from .config import Configuration
from .instrument import (
    instrument_celery_otel,
    instrument_sqlalchemy,
)


def register(app):
    """Register opentelemetry module in Flask app"""

    if not AppConfiguration.OTEL_ENABLED:
        return

    # shared sqlalchemy instrumentation for both, flask and celery, can be done during import and needs an app context
    with app.app_context():
        instrument_sqlalchemy(db)

    @app.after_request
    def inject_trace_header(response):
        """Injects the current trace ID into the response headers to appear in Gunicorn access logs"""
        span = trace.get_current_span()
        ctx = span.get_span_context()

        if ctx.is_valid:
            trace_id = format(ctx.trace_id, "032x")
            response.headers["X-Trace-Id"] = trace_id

        return response


if AppConfiguration.OTEL_ENABLED:
    meter = metrics.get_meter("mergin.celery.instrumentation")

    task_duration = meter.create_histogram(
        name="mergin_celery_task_duration",
        unit="s",
        description="Actual execution time of the task",
    )

    task_calls = meter.create_counter(
        name="mergin_celery_task_count",
        description="Total count of task executions by state",
    )

    task_retries = meter.create_counter(
        name="mergin_celery_task_retry_total",
        description="Total number of times tasks have been retried",
    )

    active_tasks = meter.create_up_down_counter(
        name="mergin_celery_task_active_count",
        description="Number of tasks currently executing in this worker",
    )

    @task_prerun.connect
    def on_task_prerun(task=None, **kwargs):
        # store start time in the Celery request context
        task.request.otel_start_time = time.time()
        active_tasks.add(1, {"mergin.celery.task": task.name})
        meter_provider = metrics.get_meter_provider()
        if hasattr(meter_provider, "force_flush"):
            meter_provider.force_flush()

    @task_retry.connect
    def on_task_retry(task=None, reason=None, **kwargs):
        task_retries.add(
            1, {"mergin.celery.task": task.name, "reason": str(reason)[:50]}
        )

    @task_postrun.connect
    def on_task_postrun(task=None, state=None, **kwargs):
        active_tasks.add(-1, {"mergin.celery.task": task.name})

        start_time = getattr(task.request, "otel_start_time", None)
        if start_time:
            duration = time.time() - start_time

            common_attrs = {
                "mergin.celery.task": task.name,
                "state": state,
                "worker": task.request.hostname,
                "retries": task.request.retries,
            }

            task_duration.record(duration, common_attrs)
            task_calls.add(1, common_attrs)

        # Ensure data leaves the process (this is where autoinstrumentation fails)
        meter_provider = metrics.get_meter_provider()
        if hasattr(meter_provider, "force_flush"):
            meter_provider.force_flush()

    # global flag to prevent double-init within a single process
    _otel_initialized = False

    def init_celery_tracing(**kwargs):
        """Initialize tracing for Celery and make sure it is only done once"""
        global _otel_initialized
        if _otel_initialized:
            return

        instrument_celery_otel()
        _otel_initialized = True

    @worker_process_init.connect
    def on_worker_process_init(sender=None, **kwargs):
        """
        Fires only in Child Processes (prefork mode).
        """
        init_celery_tracing(sender=sender)

        from opentelemetry.instrumentation.celery import CeleryInstrumentor

        CeleryInstrumentor().instrument()

    @beat_init.connect
    def init_beat_otel(sender=None, **kwargs):
        init_celery_tracing(sender=sender)

        from opentelemetry.instrumentation.celery import CeleryInstrumentor

        CeleryInstrumentor().instrument()

    # this is a hack to get celery tracing to work for threaded /gevent workers as worker_init is not working
    if Configuration.OTEL_MANUAL_CELERY_TRACING:

        @task_prerun.connect
        def on_task_prerun(sender=None, task=None, **kwargs):
            """For each task start a span manually and attach to the context"""
            init_celery_tracing(sender=sender)

            # extract Trace ID from task headers
            headers = getattr(task.request, "headers", {}) or {}
            parent_context = propagate.extract(headers)

            # start the span (linked to the parent from Flask)
            # name follows opentelemetry-instrumentation-celery convention (run/<task>), see CELERY_SPAN_PREFIXES
            tracer = trace.get_tracer(__name__)
            span = tracer.start_span(
                name=f"run/{sender.name}",
                context=parent_context,
                kind=trace.SpanKind.CONSUMER,
            )

            current_context = trace.set_span_in_context(span, parent_context)
            token = context.attach(current_context)

            # store for cleanup
            task.request.current_otel_span = span
            task.request.otel_context_token = token

        @task_postrun.connect
        def on_task_postrun(task=None, **kwargs):
            """For each task end the span and detach from the context"""
            span = getattr(task.request, "current_otel_span", None)
            if span:
                span.end()

            token = getattr(task.request, "otel_context_token", None)
            if token:
                context.detach(token)
