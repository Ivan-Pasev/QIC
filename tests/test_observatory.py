from __future__ import annotations

from dataclasses import replace

import pytest

from qic.observatory import (
    MeasurementClass,
    PerformanceEnvironment,
    PerformanceObservatory,
    PerformanceSample,
    WorkloadDescriptor,
    summarize_wall_time,
)


def environment() -> PerformanceEnvironment:
    return PerformanceEnvironment(
        python_implementation="CPython",
        python_version="3.12.0",
        os_system="TestOS",
        os_release="1",
        machine="x86_64",
        processor="test-cpu",
        logical_cpu_count=4,
        configuration_digest="config-digest",
    )


def workload() -> WorkloadDescriptor:
    return WorkloadDescriptor(
        workload_id="G10.TEST.IDENTITY",
        title="Semantic identity test",
        measurement_class=MeasurementClass.MICROKERNEL,
        size=1,
        operations_per_run=1,
        assurance_profile="FULL_CONSTITUTIONAL_PATH",
    )


def test_environment_capture_binds_configuration_without_hostname() -> None:
    first = PerformanceEnvironment.capture(configuration={"mode": "full", "t4": False})
    second = PerformanceEnvironment.capture(configuration={"mode": "full", "t4": False})
    assert first == second
    assert first.digest == second.digest
    assert first.configuration_digest


def test_observatory_returns_underlying_result_unchanged_and_excludes_warmups() -> None:
    calls: list[int] = []

    def operation() -> dict[str, object]:
        calls.append(len(calls))
        return {"accepted": True, "state": "same"}

    observed = PerformanceObservatory(environment()).run(
        workload(),
        operation,
        warmups=2,
        repetitions=4,
    )

    assert observed.result == {"accepted": True, "state": "same"}
    assert len(calls) == 6
    assert len(observed.samples) == 4
    assert [sample.repetition for sample in observed.samples] == [0, 1, 2, 3]
    assert len({sample.result_digest for sample in observed.samples}) == 1
    assert observed.summary.count == 4


def test_none_is_a_valid_measured_result() -> None:
    observed = PerformanceObservatory(environment()).run(
        workload(),
        lambda: None,
        warmups=0,
        repetitions=2,
    )
    assert observed.result is None
    assert len(observed.samples) == 2


def test_unstable_semantic_result_is_rejected_by_default() -> None:
    counter = 0

    def operation() -> int:
        nonlocal counter
        counter += 1
        return counter

    with pytest.raises(ValueError, match="semantic result identity"):
        PerformanceObservatory(environment()).run(
            workload(),
            operation,
            warmups=0,
            repetitions=2,
        )


def test_custom_result_identity_can_ignore_nonsemantic_noise() -> None:
    counter = 0

    def operation() -> dict[str, int]:
        nonlocal counter
        counter += 1
        return {"semantic": 7, "nonce": counter}

    observed = PerformanceObservatory(environment()).run(
        workload(),
        operation,
        result_identity=lambda result: {"semantic": result["semantic"]},
        warmups=0,
        repetitions=3,
    )
    assert observed.result["semantic"] == 7
    assert len({sample.result_digest for sample in observed.samples}) == 1


def test_memory_tracing_is_explicit_and_sampled() -> None:
    observed = PerformanceObservatory(environment()).run(
        workload(),
        lambda: tuple(range(32)),
        result_identity=lambda result: len(result),
        warmups=0,
        repetitions=2,
        trace_memory=True,
    )
    assert all(sample.peak_traced_bytes is not None for sample in observed.samples)
    assert all(sample.peak_traced_bytes >= 0 for sample in observed.samples if sample.peak_traced_bytes is not None)


def test_summary_uses_measured_samples_only() -> None:
    base = PerformanceSample(
        workload_digest="workload",
        environment_digest="environment",
        repetition=0,
        wall_time_ns=10,
        cpu_time_ns=9,
        peak_traced_bytes=None,
        operations=1,
        result_digest="result",
    )
    samples = tuple(
        replace(base, repetition=index, wall_time_ns=value)
        for index, value in enumerate((10, 20, 30, 40, 50))
    )
    summary = summarize_wall_time(samples)
    assert summary.count == 5
    assert summary.minimum_ns == 10
    assert summary.median_ns == 30
    assert summary.mean_ns == 30
    assert summary.p90_ns == 50
    assert summary.p95_ns == 50
    assert summary.maximum_ns == 50


def test_workload_descriptor_rejects_zero_sized_work() -> None:
    with pytest.raises(ValueError, match="size"):
        WorkloadDescriptor(
            workload_id="bad",
            title="bad",
            measurement_class=MeasurementClass.MICROKERNEL,
            size=0,
            operations_per_run=1,
            assurance_profile="FULL",
        )
