from __future__ import annotations

import pytest

from qic.observatory import (
    BottleneckClass,
    MeasurementClass,
    PerformanceSummary,
    WorkloadDescriptor,
)
from qic.performance_evidence import (
    AcceleratorCandidate,
    AcceleratorTarget,
    BottleneckFinding,
    CostAttribution,
    CostComponent,
    FindingStatus,
    RegressionClass,
    RegressionEvidence,
    ScalePoint,
    ScalingCampaign,
    WorkloadAtlasEntry,
)


def workload() -> WorkloadDescriptor:
    return WorkloadDescriptor(
        workload_id="canonical.digest",
        title="Canonical digest",
        measurement_class=MeasurementClass.MICROKERNEL,
        size=100,
        operations_per_run=100,
        assurance_profile="FULL_DECLARED_PATH",
    )


def summary(value: int) -> PerformanceSummary:
    return PerformanceSummary(
        count=5,
        minimum_ns=value - 10,
        median_ns=float(value),
        mean_ns=float(value),
        p90_ns=value + 10,
        p95_ns=value + 10,
        maximum_ns=value + 10,
        stddev_ns=5.0,
    )


def point(size: int, environment: str, value: int) -> ScalePoint:
    return ScalePoint(
        size=size,
        workload_digest="w",
        environment_digest=environment,
        sample_evidence_digest=f"samples-{size}-{environment}",
        result_digest=f"result-{size}",
        summary=summary(value),
    )


def test_atlas_entry_requires_strictly_increasing_scale_sizes() -> None:
    item = WorkloadAtlasEntry(
        workload=workload(),
        kernel="qic.core.digest.digest_hex",
        scale_sizes=(10, 100, 1000),
        claim_boundary="measurement only",
    )
    assert item.scale_sizes == (10, 100, 1000)
    assert len(item.digest) == 64

    with pytest.raises(ValueError):
        WorkloadAtlasEntry(
            workload=workload(),
            kernel="qic.core.digest.digest_hex",
            scale_sizes=(10, 10, 100),
            claim_boundary="measurement only",
        )


def test_scaling_campaign_binds_sample_evidence_not_float_summary() -> None:
    p10 = point(10, "env", 100)
    p100 = point(100, "env", 200)
    campaign = ScalingCampaign("c1", "atlas", "env", (p10, p100))
    assert len(p10.digest) == 64
    assert len(campaign.digest) == 64

    with pytest.raises(ValueError):
        ScalingCampaign("c2", "atlas", "env", (p100, p10))

    other = point(1000, "other-env", 300)
    with pytest.raises(ValueError):
        ScalingCampaign("c3", "atlas", "env", (p10, other))


def test_cost_attribution_preserves_assurance_cost_and_residual() -> None:
    attribution = CostAttribution(
        workload_digest="w",
        total_ns=1000,
        components=(
            (CostComponent.SEMANTIC, 400),
            (CostComponent.INVARIANT, 200),
            (CostComponent.WITNESS, 100),
        ),
        method="paired microbenchmarks with equal semantic work",
    )
    assert attribution.unattributed_ns == 300
    assert len(attribution.digest) == 64

    with pytest.raises(ValueError):
        CostAttribution(
            workload_digest="w",
            total_ns=100,
            components=((CostComponent.SEMANTIC, 80), (CostComponent.AUTHORITY, 30)),
            method="invalid",
        )


def test_regression_classification_uses_integer_fixed_point_threshold() -> None:
    stable = RegressionEvidence.compare(
        workload_digest="w",
        baseline_environment_digest="a",
        candidate_environment_digest="b",
        baseline_median_twice_ns=200,
        candidate_median_twice_ns=208,
        threshold_ppm=50_000,
    )
    assert stable.classification is RegressionClass.STABLE
    assert len(stable.digest) == 64

    regression = RegressionEvidence.compare(
        workload_digest="w",
        baseline_environment_digest="a",
        candidate_environment_digest="b",
        baseline_median_twice_ns=200,
        candidate_median_twice_ns=212,
        threshold_ppm=50_000,
    )
    assert regression.classification is RegressionClass.REGRESSION

    improvement = RegressionEvidence.compare(
        workload_digest="w",
        baseline_environment_digest="a",
        candidate_environment_digest="b",
        baseline_median_twice_ns=200,
        candidate_median_twice_ns=188,
        threshold_ppm=50_000,
    )
    assert improvement.classification is RegressionClass.IMPROVEMENT


def test_observed_bottleneck_requires_nonzero_measured_share_and_evidence() -> None:
    finding = BottleneckFinding(
        finding_id="bf-1",
        workload_digest="w",
        bottleneck_class=BottleneckClass.SERIALIZATION_BOUND,
        measured_runtime_share_ppm=400_000,
        evidence_digests=("campaign-digest", "cost-digest"),
        rationale="serialization dominates paired decomposition",
    )
    assert finding.status is FindingStatus.OBSERVED
    assert len(finding.digest) == 64

    with pytest.raises(ValueError):
        BottleneckFinding(
            finding_id="bf-2",
            workload_digest="w",
            bottleneck_class=BottleneckClass.UNKNOWN,
            measured_runtime_share_ppm=0,
            evidence_digests=("evidence",),
            rationale="not enough evidence",
        )


def test_accelerator_candidate_is_hypothesis_and_has_amdahl_bound() -> None:
    finding = BottleneckFinding(
        finding_id="bf-1",
        workload_digest="w",
        bottleneck_class=BottleneckClass.COMPUTE_BOUND,
        measured_runtime_share_ppm=500_000,
        evidence_digests=("e1",),
        rationale="measured compute share",
    )
    candidate = AcceleratorCandidate(
        candidate_id="ac-1",
        finding_digest=finding.digest,
        target=AcceleratorTarget.MULTICORE,
        measured_runtime_share_ppm=finding.measured_runtime_share_ppm,
        assumed_component_speedup_milli=4_000,
        estimated_transfer_cost_ns=0,
        verification_strategy="bit-identical semantic result digest plus full invariant path",
    )
    assert candidate.status is FindingStatus.HYPOTHESIS
    assert candidate.amdahl_upper_bound == pytest.approx(1.6)
    assert len(candidate.digest) == 64

    with pytest.raises(ValueError):
        AcceleratorCandidate(
            candidate_id="ac-2",
            finding_digest=finding.digest,
            target=AcceleratorTarget.GPU,
            measured_runtime_share_ppm=500_000,
            assumed_component_speedup_milli=1_000,
            estimated_transfer_cost_ns=100,
            verification_strategy="invalid no-speedup assumption",
        )
