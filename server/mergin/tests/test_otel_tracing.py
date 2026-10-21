# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import os
import time
import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace.sampling import ALWAYS_OFF, ALWAYS_ON, ParentBased
from opentelemetry.trace import StatusCode

from ..celery import celery
from ..otel.instrument import UntracedCeleryTasksSampler
from ..otel.tracing import traced, set_span_attributes, mark_span_failed
from ..sync.models import GeodiffActionHistory
from ..sync.tasks import create_project_version_zip
from . import test_project_dir
from .test_project_controller import (
    create_transaction,
    upload_chunks,
    _get_changes_with_diff,
)


def get_span(spans, name):
    """Return the only finished span with given name"""
    found = [s for s in spans if s.name == name]
    assert len(found) == 1, f"expected exactly one {name} span, got {len(found)}"
    return found[0]


def children(spans, parent):
    """Names of direct child spans"""
    return [
        s.name for s in spans if s.parent and s.parent.span_id == parent.context.span_id
    ]


@pytest.mark.parametrize(
    "tracer",
    [
        # OTEL_ENABLED=0 - no SDK provider is set up and API falls back to no-op tracer
        trace.NoOpTracer(),
        # OTel enabled, but trace is not sampled
        TracerProvider(sampler=ALWAYS_OFF).get_tracer("mergin"),
    ],
    ids=["disabled", "not_sampled"],
)
def test_traced_not_recording(tracer, monkeypatch):
    """Spans are not recorded but duration is still measured (e.g. for GeodiffActionHistory)"""
    monkeypatch.setattr("mergin.otel.tracing.tracer", tracer)
    with traced("noop", {"mergin.attr": 1}) as step:
        assert not step.span.is_recording()
        set_span_attributes({"mergin.other": "a"})
        mark_span_failed("error")
        time.sleep(0.01)
    assert step.duration >= 0.01


def test_push_diff_spans(client, otel_spans):
    changes = _get_changes_with_diff(test_project_dir)
    upload, upload_dir = create_transaction("mergin", changes)
    upload_chunks(upload_dir, upload.changes)
    resp = client.post(f"/v1/project/push/finish/{upload.transaction_id}")
    assert resp.status_code == 200

    spans = otel_spans.get_finished_spans()
    process = get_span(spans, "upload.process_chunks")
    assert process.attributes["mergin.project.id"] == str(upload.project.id)
    assert process.attributes["mergin.version"] == "v2"
    assert "upload.merge_chunks" in children(spans, process)
    assert "upload.validate_gpkg" not in children(spans, process)  # only diff uploaded

    apply_diff = get_span(spans, "geodiff.apply_diff")
    assert apply_diff.parent.span_id == process.context.span_id
    assert apply_diff.status.status_code == StatusCode.UNSET
    assert apply_diff.attributes["mergin.file.path"] == "base.gpkg"
    assert apply_diff.attributes["mergin.version"] == "v2"
    assert children(spans, apply_diff) == [
        "storage.geodiff_copy",
        "storage.geodiff_copy",
        "geodiff.apply_changeset",
        "storage.copy_file",
        "storage.checksum",
    ]
    # timing for geodiff action history is taken from the same measurement
    gh = GeodiffActionHistory.query.filter_by(
        project_id=upload.project.id, target_version="v2"
    ).first()
    apply_changeset = get_span(spans, "geodiff.apply_changeset")
    assert (
        gh.geodiff_time <= (apply_changeset.end_time - apply_changeset.start_time) / 1e9
    )

    # conflicting diff (rebase was not done) marks span as failed with geodiff log
    otel_spans.clear()
    upload, upload_dir = create_transaction("mergin", changes, 2)
    upload_chunks(upload_dir, upload.changes)
    resp = client.post(f"/v1/project/push/finish/{upload.transaction_id}")
    assert resp.status_code == 422
    spans = otel_spans.get_finished_spans()
    apply_diff = get_span(spans, "geodiff.apply_diff")
    assert apply_diff.status.status_code == StatusCode.ERROR
    assert "GEODIFF ERROR" in apply_diff.status.description
    assert (
        get_span(spans, "geodiff.apply_changeset").status.status_code
        == StatusCode.ERROR
    )


def test_restore_spans(diff_project, otel_spans):
    # v7 is composed from multiple diffs which need to be concatenated
    test_file = os.path.join(diff_project.storage.project_dir, "v7", "base.gpkg")
    os.remove(test_file)
    diff_project.storage.restore_versioned_file("base.gpkg", 7)
    assert os.path.exists(test_file)

    spans = otel_spans.get_finished_spans()
    restore = get_span(spans, "storage.restore_versioned_file")
    assert restore.attributes["mergin.version"] == "v7"
    assert restore.attributes["mergin.diff.count"] > 1
    assert children(spans, restore) == [
        "storage.geodiff_copy",
        "geodiff.concat_changes",
        "geodiff.apply_changeset",
        "storage.copy_file",
    ]

    # nothing to restore -> no span
    otel_spans.clear()
    diff_project.storage.restore_versioned_file("base.gpkg", 7)
    assert not otel_spans.get_finished_spans()


def test_zip_spans(diff_project, otel_spans):
    latest_version = diff_project.get_latest_version()
    create_project_version_zip(latest_version.id)
    assert os.path.exists(latest_version.zip_path)

    spans = otel_spans.get_finished_spans()
    archive = get_span(spans, "zip.create_archive")
    assert archive.attributes["mergin.files.count"] == len(latest_version.files)


@celery.task(untraced=True)
def untraced_task():
    pass


@celery.task
def traced_task():
    pass


def test_untraced_celery_tasks_sampler():
    """Spans of celery tasks with untraced option and all their children are dropped,
    other spans follow wrapped sampler"""
    exporter = InMemorySpanExporter()
    provider = TracerProvider(
        sampler=UntracedCeleryTasksSampler(ParentBased(root=ALWAYS_ON))
    )
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("test")

    for prefix in ("run/", "apply_async/"):
        with tracer.start_as_current_span(prefix + untraced_task.name) as span:
            assert not span.is_recording()
            with tracer.start_as_current_span("SELECT") as child:
                assert not child.is_recording()

    # sampled parent propagated from other process (e.g. celery beat) is ignored
    parent = trace.set_span_in_context(
        trace.NonRecordingSpan(
            trace.SpanContext(
                trace_id=1,
                span_id=1,
                is_remote=True,
                trace_flags=trace.TraceFlags(trace.TraceFlags.SAMPLED),
            )
        )
    )
    with tracer.start_as_current_span(
        f"run/{untraced_task.name}", context=parent
    ) as span:
        assert not span.is_recording()

    with tracer.start_as_current_span(f"run/{traced_task.name}"):
        with tracer.start_as_current_span("SELECT"):
            pass
    # unknown task is traced
    with tracer.start_as_current_span("run/unknown.task"):
        pass
    assert [s.name for s in exporter.get_finished_spans()] == [
        "SELECT",
        f"run/{traced_task.name}",
        "run/unknown.task",
    ]
