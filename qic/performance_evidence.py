"""Canonical evidence models for QIC G10 performance qualification.

Measured statistical views may contain floats, but QIC-CANONICAL/1.0 deliberately
forbids floats. Canonical performance evidence therefore binds raw/sample evidence
digests plus integer or fixed-point fields. Floating summaries remain derived views,
not identity-bearing canonical state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .core.digest import digest_hex
from .observatory import BottleneckClass, PerformanceSummary, WorkloadDescriptor

PPM = 1_000_000
SPEEDUP_MILLI = 1_000


class CostComponent(str, Enum):
    SEMANTIC = "SEMANTIC"
    AUTHORITY = "AUTHORITY"
    INVARIANT = "INVARIANT"
    SERIALIZATION = "SERIALIZATION"
    PERSISTENCE = "PERSISTENCE"
    CHRONO = "CHRONO"
    WITNESS = "WITNESS"
    SCHEDULER = "SCHEDULER"
    OTHER = "OTHER"


class RegressionClass(str, Enum):
    IMPROVEMENT = "IMPROVEMENT"
    STABLE = "STABLE"
    REGRESSION = "REGRESSION"


class FindingStatus(str, Enum):
    OBSERVED = "OBSERVED"
    HYPOTHESIS = "HYPOTHESIS"
    REJECTED = "REJECTED"


class AcceleratorTarget(str, Enum):
    CPU_OPTIMIZE = "CPU_OPTIMIZE"
    SIMD = "SIMD"
    MULTICORE = "MULTICORE"
    GPU = "GPU"
    FPGA = "FPGA"
    ASIC = "ASIC"
    PHOTONIC_RESEARCH = "PHOTONIC_RESEARCH"
    QPU_RESEARCH = "QPU_RESEARCH"
    NOT_ACCELERATOR_SUITABLE = "NOT_ACCELERATOR_SUITABLE"


def _text(value: object, *, name: str) -> str:
    if type(value) is not str or not value or "\x00" in value:
        raise ValueError(f"{name} must be a non-empty NUL-free string")
    return value


@dataclass(frozen=True, slots=True)
class WorkloadAtlasEntry:
    workload: WorkloadDescriptor
    kernel: str
    scale_sizes: tuple[int, ...]
    claim_boundary: str

    def __post_init__(self) -> None:
        if not isinstance(self.workload, WorkloadDescriptor):
            raise TypeError("workload must be WorkloadDescriptor")
        _text(self.kernel, name="kernel")
        _text(self.claim_boundary, name="claim_boundary")
        if not self.scale_sizes:
            raise ValueError("scale_sizes must not be empty")
        if any(type(size) is not int or size <= 0 for size in self.scale_sizes):
            raise ValueError("scale sizes must be positive ints")
        if tuple(sorted(set(self.scale_sizes))) != self.scale_sizes:
            raise ValueError("scale_sizes must be strictly increasing and unique")

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="performance.atlas_entry")


@dataclass(frozen=True, slots=True)
class ScalePoint:
    size: int
    workload_digest: str
    environment_digest: str
    sample_evidence_digest: str
    result_digest: str
    summary: PerformanceSummary

    def __post_init__(self) -> None:
        if type(self.size) is not int or self.size <= 0:
            raise ValueError("size must be a positive int")
        _text(self.workload_digest, name="workload_digest")
        _text(self.environment_digest, name="environment_digest")
        _text(self.sample_evidence_digest, name="sample_evidence_digest")
        _text(self.result_digest, name="result_digest")
        if not isinstance(self.summary, PerformanceSummary):
            raise TypeError("summary must be PerformanceSummary")

    @property
    def digest(self) -> str:
        # Summary is intentionally excluded: it is a derived statistical view that
        # contains floats. Canonical identity binds the immutable sample evidence.
        return digest_hex(
            {
                "size": self.size,
                "workload_digest": self.workload_digest,
                "environment_digest": self.environment_digest,
                "sample_evidence_digest": self.sample_evidence_digest,
                "result_digest": self.result_digest,
            },
            domain="performance.scale_point",
        )


@dataclass(frozen=True, slots=True)
class ScalingCampaign:
    campaign_id: str
    atlas_entry_digest: str
    environment_digest: str
    points: tuple[ScalePoint, ...]

    def __post_init__(self) -> None:
        _text(self.campaign_id, name="campaign_id")
        _text(self.atlas_entry_digest, name="atlas_entry_digest")
        _text(self.environment_digest, name="environment_digest")
        if len(self.points) < 2:
            raise ValueError("scaling campaign requires at least two points")
        sizes = tuple(point.size for point in self.points)
        if tuple(sorted(set(sizes))) != sizes:
            raise ValueError("campaign point sizes must be strictly increasing and unique")
        if any(point.environment_digest != self.environment_digest for point in self.points):
            raise ValueError("all scale points must use the campaign environment")

    @property
    def digest(self) -> str:
        return digest_hex(
            {
                "campaign_id": self.campaign_id,
                "atlas_entry_digest": self.atlas_entry_digest,
                "environment_digest": self.environment_digest,
                "point_digests": tuple(point.digest for point in self.points),
            },
            domain="performance.scaling_campaign",
        )


@dataclass(frozen=True, slots=True)
class CostAttribution:
    workload_digest: str
    total_ns: int
    components: tuple[tuple[CostComponent, int], ...]
    method: str

    def __post_init__(self) -> None:
        _text(self.workload_digest, name="workload_digest")
        _text(self.method, name="method")
        if type(self.total_ns) is not int or self.total_ns <= 0:
            raise ValueError("total_ns must be a positive int")
        if not self.components:
            raise ValueError("components must not be empty")
        names = tuple(component for component, _ in self.components)
        if len(set(names)) != len(names):
            raise ValueError("cost components must be unique")
        if any(not isinstance(component, CostComponent) for component in names):
            raise TypeError("component keys must be CostComponent")
        if any(type(value) is not int or value < 0 for _, value in self.components):
            raise ValueError("component costs must be non-negative ints")
        if sum(value for _, value in self.components) > self.total_ns:
            raise ValueError("attributed component cost cannot exceed total cost")

    @property
    def unattributed_ns(self) -> int:
        return self.total_ns - sum(value for _, value in self.components)

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="performance.cost_attribution")


@dataclass(frozen=True, slots=True)
class RegressionEvidence:
    workload_digest: str
    baseline_environment_digest: str
    candidate_environment_digest: str
    baseline_median_twice_ns: int
    candidate_median_twice_ns: int
    threshold_ppm: int
    classification: RegressionClass

    @classmethod
    def compare(
        cls,
        *,
        workload_digest: str,
        baseline_environment_digest: str,
        candidate_environment_digest: str,
        baseline_median_twice_ns: int,
        candidate_median_twice_ns: int,
        threshold_ppm: int,
    ) -> "RegressionEvidence":
        if type(baseline_median_twice_ns) is not int or baseline_median_twice_ns <= 0:
            raise ValueError("baseline_median_twice_ns must be positive int")
        if type(candidate_median_twice_ns) is not int or candidate_median_twice_ns <= 0:
            raise ValueError("candidate_median_twice_ns must be positive int")
        if type(threshold_ppm) is not int or not 0 <= threshold_ppm < PPM:
            raise ValueError("threshold_ppm must be integer in [0, 1_000_000)")

        upper = baseline_median_twice_ns * (PPM + threshold_ppm)
        lower = baseline_median_twice_ns * (PPM - threshold_ppm)
        candidate_scaled = candidate_median_twice_ns * PPM
        if candidate_scaled > upper:
            classification = RegressionClass.REGRESSION
        elif candidate_scaled < lower:
            classification = RegressionClass.IMPROVEMENT
        else:
            classification = RegressionClass.STABLE
        return cls(
            workload_digest=workload_digest,
            baseline_environment_digest=baseline_environment_digest,
            candidate_environment_digest=candidate_environment_digest,
            baseline_median_twice_ns=baseline_median_twice_ns,
            candidate_median_twice_ns=candidate_median_twice_ns,
            threshold_ppm=threshold_ppm,
            classification=classification,
        )

    def __post_init__(self) -> None:
        _text(self.workload_digest, name="workload_digest")
        _text(self.baseline_environment_digest, name="baseline_environment_digest")
        _text(self.candidate_environment_digest, name="candidate_environment_digest")
        if type(self.baseline_median_twice_ns) is not int or self.baseline_median_twice_ns <= 0:
            raise ValueError("baseline_median_twice_ns must be positive int")
        if type(self.candidate_median_twice_ns) is not int or self.candidate_median_twice_ns <= 0:
            raise ValueError("candidate_median_twice_ns must be positive int")
        if type(self.threshold_ppm) is not int or not 0 <= self.threshold_ppm < PPM:
            raise ValueError("threshold_ppm must be integer in [0, 1_000_000)")
        if not isinstance(self.classification, RegressionClass):
            raise TypeError("classification must be RegressionClass")

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="performance.regression")


@dataclass(frozen=True, slots=True)
class BottleneckFinding:
    finding_id: str
    workload_digest: str
    bottleneck_class: BottleneckClass
    measured_runtime_share_ppm: int
    evidence_digests: tuple[str, ...]
    rationale: str
    status: FindingStatus = FindingStatus.OBSERVED

    def __post_init__(self) -> None:
        _text(self.finding_id, name="finding_id")
        _text(self.workload_digest, name="workload_digest")
        _text(self.rationale, name="rationale")
        if not isinstance(self.bottleneck_class, BottleneckClass):
            raise TypeError("bottleneck_class must be BottleneckClass")
        if not isinstance(self.status, FindingStatus):
            raise TypeError("status must be FindingStatus")
        if type(self.measured_runtime_share_ppm) is not int or not 0 <= self.measured_runtime_share_ppm <= PPM:
            raise ValueError("measured_runtime_share_ppm must be integer in [0, 1_000_000]")
        if self.status is FindingStatus.OBSERVED and self.bottleneck_class is BottleneckClass.UNKNOWN:
            raise ValueError("an observed finding cannot classify the bottleneck as UNKNOWN")
        if self.status is FindingStatus.OBSERVED and self.measured_runtime_share_ppm <= 0:
            raise ValueError("an observed finding requires positive measured runtime share")
        if not self.evidence_digests or any(not digest for digest in self.evidence_digests):
            raise ValueError("evidence_digests must contain at least one digest")

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="performance.bottleneck_finding")


@dataclass(frozen=True, slots=True)
class AcceleratorCandidate:
    candidate_id: str
    finding_digest: str
    target: AcceleratorTarget
    measured_runtime_share_ppm: int
    assumed_component_speedup_milli: int
    estimated_transfer_cost_ns: int
    verification_strategy: str
    status: FindingStatus = FindingStatus.HYPOTHESIS

    def __post_init__(self) -> None:
        _text(self.candidate_id, name="candidate_id")
        _text(self.finding_digest, name="finding_digest")
        _text(self.verification_strategy, name="verification_strategy")
        if not isinstance(self.target, AcceleratorTarget):
            raise TypeError("target must be AcceleratorTarget")
        if not isinstance(self.status, FindingStatus):
            raise TypeError("status must be FindingStatus")
        if type(self.measured_runtime_share_ppm) is not int or not 0 < self.measured_runtime_share_ppm <= PPM:
            raise ValueError("candidate requires positive measured_runtime_share_ppm")
        if type(self.assumed_component_speedup_milli) is not int or self.assumed_component_speedup_milli <= SPEEDUP_MILLI:
            raise ValueError("assumed_component_speedup_milli must be integer > 1000")
        if type(self.estimated_transfer_cost_ns) is not int or self.estimated_transfer_cost_ns < 0:
            raise ValueError("estimated_transfer_cost_ns must be a non-negative int")
        if self.status is FindingStatus.OBSERVED:
            raise ValueError("accelerator candidate status cannot be OBSERVED before implementation evidence")

    @property
    def amdahl_upper_bound(self) -> float:
        p = self.measured_runtime_share_ppm / PPM
        s = self.assumed_component_speedup_milli / SPEEDUP_MILLI
        return 1.0 / ((1.0 - p) + (p / s))

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="performance.accelerator_candidate")
