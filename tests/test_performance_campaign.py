from __future__ import annotations

import json

import pytest

from qic.observatory import MeasurementClass, PerformanceEnvironment, WorkloadDescriptor
from qic.performance_campaign import (
    CampaignConflictError,
    CampaignCorruptionError,
    CampaignSpec,
    PerformanceCampaignStore,
    execute_campaign,
)


def environment() -> PerformanceEnvironment:
    return PerformanceEnvironment(
        python_implementation="CPython",
        python_version="3.12.test",
        os_system="TestOS",
        os_release="1",
        machine="x86_64",
        processor="",
        logical_cpu_count=4,
        configuration_digest="cfg",
    )


def workload() -> WorkloadDescriptor:
    return WorkloadDescriptor(
        workload_id="campaign.test",
        title="Campaign test",
        measurement_class=MeasurementClass.MICROKERNEL,
        size=10,
        operations_per_run=10,
        assurance_profile="FULL_DECLARED_PATH",
    )


def test_execute_campaign_preserves_result_and_canonical_raw_evidence() -> None:
    spec = CampaignSpec("c1", workload(), environment(), warmups=2, repetitions=4)
    calls = 0

    def operation() -> tuple[int, ...]:
        nonlocal calls
        calls += 1
        return tuple(range(10))

    execution = execute_campaign(spec, operation)
    assert execution.result == tuple(range(10))
    assert calls == 6
    assert len(execution.record.samples) == 4
    assert len(execution.record.digest) == 64
    assert execution.record.summary.count == 4
    assert all(sample.result_digest == execution.record.result_digest for sample in execution.record.samples)


def test_store_roundtrip_is_idempotent_and_does_not_persist_float_summary(tmp_path) -> None:
    spec = CampaignSpec("c1", workload(), environment(), warmups=0, repetitions=3)
    record = execute_campaign(spec, lambda: ("stable", 1)).record
    store = PerformanceCampaignStore(tmp_path)
    path = store.persist(record)
    assert store.persist(record) == path
    loaded = store.load("c1")
    assert loaded == record
    assert loaded.digest == record.digest

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "summary" not in payload
    assert all(type(sample["wall_time_ns"]) is int for sample in payload["samples"])
    assert all(type(sample["cpu_time_ns"]) is int for sample in payload["samples"])


def test_store_rejects_conflicting_reuse(tmp_path) -> None:
    store = PerformanceCampaignStore(tmp_path)
    first = execute_campaign(
        CampaignSpec("same", workload(), environment(), warmups=0, repetitions=2),
        lambda: "a",
    ).record
    second = execute_campaign(
        CampaignSpec("same", workload(), environment(), warmups=0, repetitions=2),
        lambda: "b",
    ).record
    store.persist(first)
    with pytest.raises(CampaignConflictError):
        store.persist(second)


def test_store_detects_tampering(tmp_path) -> None:
    store = PerformanceCampaignStore(tmp_path)
    record = execute_campaign(
        CampaignSpec("tamper", workload(), environment(), warmups=0, repetitions=2),
        lambda: "stable",
    ).record
    path = store.persist(record)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["samples"][0]["wall_time_ns"] += 1
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    with pytest.raises(CampaignCorruptionError):
        store.load("tamper")


def test_campaign_rejects_unstable_semantic_result() -> None:
    spec = CampaignSpec("unstable", workload(), environment(), warmups=0, repetitions=3)
    count = 0

    def operation() -> int:
        nonlocal count
        count += 1
        return count

    with pytest.raises(ValueError, match="semantic result identity"):
        execute_campaign(spec, operation)
