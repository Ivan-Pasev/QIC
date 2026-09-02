"""Read-only performance observatory for QIC G10.

The observatory measures work; it does not change the authority, invariant,
serialization, Chrono, witness, KBI, journal, or recovery path of the measured
callable. Timing values are evidence about one declared environment, not
canonical truth and not an accelerator/hardware maturity claim.
"""

from __future__ import annotations

import math
import os
import platform
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Generic, TypeVar

from .core.digest import digest_hex


T = TypeVar("T")


class MeasurementClass(str, Enum):
    MICROKERNEL = "MICROKERNEL"
    END_TO_END = "END_TO_END"


class BottleneckClass(str, Enum):
    COMPUTE_BOUND = "COMPUTE_BOUND"
    MEMORY_BOUND = "MEMORY_BOUND"
    SERIALIZATION_BOUND = "SERIALIZATION_BOUND"
    IO_BOUND = "IO_BOUND"
    GRAPH_TRAVERSAL = "GRAPH_TRAVERSAL"
    SCHEDULER_BOUND = "SCHEDULER_BOUND"
    ASSURANCE_BOUND = "ASSURANCE_BOUND"
    ALGORITHM_BOUND = "ALGORITHM_BOUND"
    UNKNOWN = "UNKNOWN"


def _required_text(value: object, *, name: str) -> str:
    if type(value) is not str or not value or "\x00" in value:
        raise ValueError(f"{name} must be a non-empty NUL-free string")
    return value


@dataclass(frozen=True, slots=True)
class PerformanceEnvironment:
    python_implementation: str
    python_version: str
    os_system: str
    os_release: str
    machine: str
    processor: str
    logical_cpu_count: int | None
    configuration_digest: str

    def __post_init__(self) -> None:
        for name in (
            "python_implementation",
            "python_version",
            "os_system",
            "os_release",
            "machine",
            "configuration_digest",
        ):
            _required_text(getattr(self, name), name=name)
        if type(self.processor) is not str or "\x00" in self.processor:
            raise ValueError("processor must be a NUL-free string")
        if self.logical_cpu_count is not None and (
            type(self.logical_cpu_count) is not int or self.logical_cpu_count <= 0
        ):
            raise ValueError("logical_cpu_count must be a positive int or None")

    @classmethod
    def capture(cls, *, configuration: object) -> "PerformanceEnvironment":
        return cls(
            python_implementation=platform.python_implementation(),
            python_version=platform.python_version(),
            os_system=platform.system() or "UNKNOWN",
            os_release=platform.release() or "UNKNOWN",
            machine=platform.machine() or "UNKNOWN",
            processor=platform.processor(),
            logical_cpu_count=os.cpu_count(),
            configuration_digest=digest_hex(configuration, domain="performance.configuration"),
        )

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="performance.environment")


@dataclass(frozen=True, slots=True)
class WorkloadDescriptor:
    workload_id: str
    title: str
    measurement_class: MeasurementClass
    size: int
    operations_per_run: int
    assurance_profile: str

    def __post_init__(self) -> None:
        _required_text(self.workload_id, name="workload_id")
        _required_text(self.title, name="title")
        _required_text(self.assurance_profile, name="assurance_profile")
        if type(self.measurement_class) is not MeasurementClass:
            raise TypeError("measurement_class must be MeasurementClass")
        if type(self.size) is not int or self.size <= 0:
            raise ValueError("size must be a positive int")
        if type(self.operations_per_run) is not int or self.operations_per_run <= 0:
            raise ValueError("operations_per_run must be a positive int")

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="performance.workload")


@dataclass(frozen=True, slots=True)
class PerformanceSample:
    workload_digest: str
    environment_digest: str
    repetition: int
    wall_time_ns: int
    cpu_time_ns: int
    peak_traced_bytes: int | None
    operations: int
    result_digest: str

    def __post_init__(self) -> None:
        _required_text(self.workload_digest, name="workload_digest")
        _required_text(self.environment_digest, name="environment_digest")
        _required_text(self.result_digest, name="result_digest")
        for name in ("repetition", "wall_time_ns", "cpu_time_ns", "operations"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a non-negative int")
        if self.operations <= 0:
            raise ValueError("operations must be positive")
        if self.peak_traced_bytes is not None and (
            type(self.peak_traced_bytes) is not int or self.peak_traced_bytes < 0
        ):
            raise ValueError("peak_traced_bytes must be a non-negative int or None")


@dataclass(frozen=True, slots=True)
class PerformanceSummary:
    count: int
    minimum_ns: int
    median_ns: float
    mean_ns: float
    p90_ns: int
    p95_ns: int
    maximum_ns: int
    stddev_ns: float


def _nearest_rank(values: tuple[int, ...], percentile: float) -> int:
    if not values:
        raise ValueError("percentile requires at least one value")
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


def summarize_wall_time(samples: tuple[PerformanceSample, ...]) -> PerformanceSummary:
    if not samples:
        raise ValueError("summary requires at least one sample")
    values = tuple(sample.wall_time_ns for sample in samples)
    return PerformanceSummary(
        count=len(values),
        minimum_ns=min(values),
        median_ns=statistics.median(values),
        mean_ns=statistics.fmean(values),
        p90_ns=_nearest_rank(values, 0.90),
        p95_ns=_nearest_rank(values, 0.95),
        maximum_ns=max(values),
        stddev_ns=statistics.pstdev(values),
    )


@dataclass(frozen=True, slots=True)
class BenchmarkRun(Generic[T]):
    result: T
    samples: tuple[PerformanceSample, ...]
    summary: PerformanceSummary


class PerformanceObservatory:
    """Measure an unchanged callable under an explicit workload/environment."""

    def __init__(self, environment: PerformanceEnvironment) -> None:
        if not isinstance(environment, PerformanceEnvironment):
            raise TypeError("environment must be PerformanceEnvironment")
        self.environment = environment

    def run(
        self,
        workload: WorkloadDescriptor,
        operation: Callable[[], T],
        *,
        result_identity: Callable[[T], object] = lambda value: value,
        warmups: int = 1,
        repetitions: int = 5,
        trace_memory: bool = False,
        require_stable_result: bool = True,
    ) -> BenchmarkRun[T]:
        if not isinstance(workload, WorkloadDescriptor):
            raise TypeError("workload must be WorkloadDescriptor")
        if not callable(operation) or not callable(result_identity):
            raise TypeError("operation and result_identity must be callable")
        if type(warmups) is not int or warmups < 0:
            raise ValueError("warmups must be a non-negative int")
        if type(repetitions) is not int or repetitions <= 0:
            raise ValueError("repetitions must be a positive int")

        for _ in range(warmups):
            operation()

        samples: list[PerformanceSample] = []
        final_result: T | None = None
        expected_result_digest: str | None = None

        for repetition in range(repetitions):
            if trace_memory:
                tracemalloc.start()
            cpu_start = time.process_time_ns()
            wall_start = time.perf_counter_ns()
            try:
                result = operation()
            finally:
                wall_end = time.perf_counter_ns()
                cpu_end = time.process_time_ns()
                if trace_memory:
                    _, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()
                else:
                    peak = None

            identity = result_identity(result)
            result_digest = digest_hex(identity, domain="performance.result")
            if expected_result_digest is None:
                expected_result_digest = result_digest
            elif require_stable_result and result_digest != expected_result_digest:
                raise ValueError("measured workload changed semantic result identity across repetitions")

            samples.append(
                PerformanceSample(
                    workload_digest=workload.digest,
                    environment_digest=self.environment.digest,
                    repetition=repetition,
                    wall_time_ns=wall_end - wall_start,
                    cpu_time_ns=cpu_end - cpu_start,
                    peak_traced_bytes=peak,
                    operations=workload.operations_per_run,
                    result_digest=result_digest,
                )
            )
            final_result = result

        assert final_result is not None
        frozen_samples = tuple(samples)
        return BenchmarkRun(
            result=final_result,
            samples=frozen_samples,
            summary=summarize_wall_time(frozen_samples),
        )
