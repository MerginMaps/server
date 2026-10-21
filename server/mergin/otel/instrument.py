# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import logging
import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import (
    Decision,
    ParentBased,
    Sampler,
    SamplingResult,
    TraceIdRatioBased,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

from .config import Configuration
from .tracing import is_untraced_celery_task_span


def create_resource():
    return Resource.create(
        {
            "service.name": Configuration.OTEL_SERVICE_NAME,
            "process.pid": os.getpid(),
        }
    )


class UntracedCeleryTasksSampler(Sampler):
    """Drop spans of celery tasks with untraced=True option, otherwise delegate decision to wrapped sampler.
    Child spans (e.g. SQL queries) are dropped as well as parent based sampler follows the parent decision.
    """

    def __init__(self, delegate: Sampler):
        self._delegate = delegate

    def should_sample(
        self,
        parent_context,
        trace_id,
        name,
        kind=None,
        attributes=None,
        links=None,
        trace_state=None,
    ) -> SamplingResult:
        if is_untraced_celery_task_span(name):
            return SamplingResult(Decision.DROP)
        return self._delegate.should_sample(
            parent_context, trace_id, name, kind, attributes, links, trace_state
        )

    def get_description(self) -> str:
        return f"UntracedCeleryTasksSampler{{{self._delegate.get_description()}}}"


def setup_otel_provider():
    """
    Initializes the Tracer Engine. Call this Gunicorn in post_fork or in Celery worker_process_init.
    """
    resource = create_resource()

    sampler = UntracedCeleryTasksSampler(
        ParentBased(root=TraceIdRatioBased(Configuration.OTEL_TRACES_SAMPLER_ARG))
    )
    provider = TracerProvider(resource=resource, sampler=sampler)

    # each worker needs its own background thread (BatchSpanProcessor)
    exporter = OTLPSpanExporter(
        endpoint=Configuration.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True
    )
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)


def setup_otel_metrics():
    """Initializes the Metrics Engine. Call this in post_fork."""
    resource = create_resource()
    exporter = OTLPMetricExporter(
        endpoint=Configuration.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True
    )
    reader = PeriodicExportingMetricReader(exporter)

    provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)


def setup_otel_logging():
    LoggingInstrumentor().instrument(set_logging_format=True)

    # manually force the OTel format into the logging handler (e.g. for celery)
    for handler in logging.getLogger().handlers:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(otelTraceID)s] %(message)s")
        )


def instrument_flask_app(app):
    """Initializes the Flask app with OTel hooks. Call this in post_fork."""
    setup_otel_provider()
    setup_otel_metrics()
    # setup_otel_logging()

    # patch to prevent KeyErrors in logs
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        # manually fetch the current trace context for EVERY log record
        ctx = trace.get_current_span().get_span_context()
        record.otelTraceID = format(ctx.trace_id, "032x") if ctx.is_valid else "-"
        return record

    logging.setLogRecordFactory(record_factory)

    FlaskInstrumentor().instrument_app(
        app, excluded_urls=Configuration.OTEL_PYTHON_FLASK_EXCLUDED_URLS
    )
    # trace celery tasks sent from requests (apply_async/<task> span) and propagate trace context
    # in task headers, so the task in worker is linked to the request trace
    CeleryInstrumentor().instrument()


def instrument_sqlalchemy(db):
    """
    Instruments the SQLAlchemy engine managed by Flask-SQLAlchemy.
    """
    SQLAlchemyInstrumentor().instrument(
        engine=db.engine,
        enable_commenter=True,  # Adds TraceIDs to SQL comments
    )


def instrument_celery_otel():
    """Initializes metrics, tracing and logging. Call this in worker_process_init."""
    setup_otel_provider()
    setup_otel_metrics()
    setup_otel_logging()
