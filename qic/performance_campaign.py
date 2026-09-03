"""Executable and persistent measurement campaigns for QIC G10.

Only raw integer/string measurement evidence participates in canonical identity.
Floating statistical summaries are regenerated derived views and never define a
campaign digest. Persistence is append-only by campaign ID and fails closed on
conflicting reuse or tampering.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Generic, TypeVar

from .core.digest import digest_hex
from .observatory import (
    BenchmarkRun,
    MeasurementClass,
    PerformanceEnvironment,
    PerformanceObservatory,
    PerformanceSample,
    PerformanceSummary,
    WorkloadDescriptor,
    summarize_wall_time,
)

T = TypeVar("T")


def _text(value: object, *, name: str) -> str:
    if type(value) is not str or not value or "\x00" in value:
        raise ValueError(f"{name} must be a non-empty NUL-free string")
    return value


@dataclass(frozen=True, slots=True)
class CampaignSpec:
    campaign_id: str
    workload: WorkloadDescriptor
    environment: PerformanceEnvironment
    warmups: int = 1
    repetitions: int = 5
    trace_memory: bool = False

    def __post_init__(self) -> None:
        _text(self.campaign_id, name="campaign_id")
        if not isinstance(self.workload, WorkloadDescriptor):
            raise TypeError("workload must be WorkloadDescriptor")
        if not isinstance(self.environment, PerformanceEnvironment):
            raise TypeError("environment must be PerformanceEnvironment")
        if type(self.warmups) is not int or self.warmups < 0:
            raise ValueError("warmups must be a non-negative int")
        if type(self.repetitions) is not int or self.repetitions <= 0:
            raise ValueError("repetitions must be a positive int")
        if type(self.trace_memory) is not bool:
            raise TypeError("trace_memory must be bool")

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="performance.campaign_spec")


@dataclass(frozen=True, slots=True)
class CampaignRecord:
    spec: CampaignSpec
    samples: tuple[PerformanceSample, ...]
    result_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.spec, CampaignSpec):
            raise TypeError("spec must be CampaignSpec")
        _text(self.result_digest, name="result_digest")
        if len(self.samples) != self.spec.repetitions:
            raise ValueError("sample count must equal campaign repetitions")
        if tuple(sample.repetition for sample in self.samples) != tuple(range(len(self.samples))):
            raise ValueError("sample repetitions must be contiguous from zero")
        if any(sample.workload_digest != self.spec.workload.digest for sample in self.samples):
            raise ValueError("all samples must bind the campaign workload")
        if any(sample.environment_digest != self.spec.environment.digest for sample in self.samples):
            raise ValueError("all samples must bind the campaign environment")
        if any(sample.result_digest != self.result_digest for sample in self.samples):
            raise ValueError("all samples must bind the campaign semantic result")

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="performance.campaign_record")

    @property
    def summary(self) -> PerformanceSummary:
        """Derived floating view; intentionally excluded from canonical identity."""
        return summarize_wall_time(self.samples)


@dataclass(frozen=True, slots=True)
class CampaignExecution(Generic[T]):
    result: T
    record: CampaignRecord


def execute_campaign(
    spec: CampaignSpec,
    operation: Callable[[], T],
    *,
    result_identity: Callable[[T], object] = lambda value: value,
) -> CampaignExecution[T]:
    """Measure an unchanged callable and return a canonical raw evidence record."""

    run: BenchmarkRun[T] = PerformanceObservatory(spec.environment).run(
        spec.workload,
        operation,
        result_identity=result_identity,
        warmups=spec.warmups,
        repetitions=spec.repetitions,
        trace_memory=spec.trace_memory,
        require_stable_result=True,
    )
    result_digest = run.samples[0].result_digest
    return CampaignExecution(
        result=run.result,
        record=CampaignRecord(spec=spec, samples=run.samples, result_digest=result_digest),
    )


class CampaignStoreError(RuntimeError):
    pass


class CampaignConflictError(CampaignStoreError):
    pass


class CampaignCorruptionError(CampaignStoreError):
    pass


class PerformanceCampaignStore:
    """Local immutable reference store for raw campaign evidence.

    This is evidence persistence, not authority/state persistence. Files are
    created with O_EXCL so conflicting campaign IDs never overwrite a winner.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, campaign_id: str) -> Path:
        _text(campaign_id, name="campaign_id")
        safe = campaign_id.replace("/", "_").replace("\\", "_")
        return self.root / f"{safe}.json"

    @staticmethod
    def _payload(record: CampaignRecord) -> dict[str, object]:
        return {
            "format": "QIC-PERFORMANCE-CAMPAIGN/1.0",
            "record_digest": record.digest,
            "spec": {
                "campaign_id": record.spec.campaign_id,
                "workload": {
                    "workload_id": record.spec.workload.workload_id,
                    "title": record.spec.workload.title,
                    "measurement_class": record.spec.workload.measurement_class.value,
                    "size": record.spec.workload.size,
                    "operations_per_run": record.spec.workload.operations_per_run,
                    "assurance_profile": record.spec.workload.assurance_profile,
                },
                "environment": asdict(record.spec.environment),
                "warmups": record.spec.warmups,
                "repetitions": record.spec.repetitions,
                "trace_memory": record.spec.trace_memory,
            },
            "samples": [asdict(sample) for sample in record.samples],
            "result_digest": record.result_digest,
        }

    @staticmethod
    def _encode(record: CampaignRecord) -> bytes:
        return (json.dumps(PerformanceCampaignStore._payload(record), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

    def persist(self, record: CampaignRecord) -> Path:
        if not isinstance(record, CampaignRecord):
            raise TypeError("record must be CampaignRecord")
        path = self._path(record.spec.campaign_id)
        encoded = self._encode(record)
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            try:
                existing = path.read_bytes()
            except OSError as exc:
                raise CampaignStoreError(f"cannot read existing campaign evidence: {exc}") from exc
            if existing == encoded:
                return path
            raise CampaignConflictError("campaign ID already exists with different evidence")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            try:
                path.unlink(missing_ok=True)
            finally:
                raise
        return path

    def load(self, campaign_id: str) -> CampaignRecord:
        path = self._path(campaign_id)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CampaignCorruptionError(f"cannot decode campaign evidence: {exc}") from exc
        try:
            if payload["format"] != "QIC-PERFORMANCE-CAMPAIGN/1.0":
                raise ValueError("unknown campaign evidence format")
            spec_data = payload["spec"]
            workload_data = spec_data["workload"]
            environment_data = spec_data["environment"]
            workload = WorkloadDescriptor(
                workload_id=workload_data["workload_id"],
                title=workload_data["title"],
                measurement_class=MeasurementClass(workload_data["measurement_class"]),
                size=workload_data["size"],
                operations_per_run=workload_data["operations_per_run"],
                assurance_profile=workload_data["assurance_profile"],
            )
            environment = PerformanceEnvironment(**environment_data)
            spec = CampaignSpec(
                campaign_id=spec_data["campaign_id"],
                workload=workload,
                environment=environment,
                warmups=spec_data["warmups"],
                repetitions=spec_data["repetitions"],
                trace_memory=spec_data["trace_memory"],
            )
            samples = tuple(PerformanceSample(**sample) for sample in payload["samples"])
            record = CampaignRecord(spec=spec, samples=samples, result_digest=payload["result_digest"])
        except (KeyError, TypeError, ValueError) as exc:
            raise CampaignCorruptionError(f"invalid campaign evidence structure: {exc}") from exc
        if record.digest != payload.get("record_digest"):
            raise CampaignCorruptionError("campaign evidence digest mismatch")
        return record
