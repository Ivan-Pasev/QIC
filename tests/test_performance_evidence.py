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


def test_scaling_campaign_rejects_environment_mixing_and_unsorted_sizes() -> None:
    p10 = ScalePoint(10, "w", "env", summary(100), "r10")
    p100 = ScalePoint(100, "w", "env", summary(200), "r100")
    campaign = ScalingCampaign("c1", "atlas", "env", (p10, p100))
    assert len(campaign.digest) == 64

    with pytest.raises(ValueError):
        ScalingCampaign("c2", "atlas", "env", (p100, p10))

    other = ScalePoint(1000, "w", "other-env", summary(300), "r1000")
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

    with pytest.raises(ValueError):
        CostAttribution(
            workload_digest="w",
            total_ns=100,
            components=((CostComponent.SEMANTIC, 80), (CostComponent.AUTHORITY, 30)),
            method="invalid",
        )


def test_regression_classification_uses_explicit_threshold() -> None:
    stable = RegressionEvidence.compare(
        workload_digest="w",
        baseline_environment_digest="a",
        candidate_environment_digest="b",
        baseline_median_ns=100.0,
        candidate_median_ns=104.0,
        threshold_fraction=0.05,
    )
    assert stable.classification is RegressionClass.STABLE

    regression = RegressionEvidence.compare(
        workload_digest="w",
        baseline_environment_digest="a",
        candidate_environment_digest="b",
        baseline_median_ns=100.0,
        candidate_median_ns=106.0,
        threshold_fraction=0.05,
    )
    assert regression.classification is RegressionClass.REGRESSION

    improvement = RegressionEvidence.compare(
        workload_digest="w",
        baseline_environment_digest="a",
        candidate_environment_digest="b",
        baseline_median_ns=100.0,
        candidate_median_ns=94.0,
        threshold_fraction=0.05,
    )
    assert improvement.classification is RegressionClass.IMPROVEMENT


def test_observed_bottleneck_requires_nonzero_measured_share_and_evidence() -> None:
    finding = BottleneckFinding(
        finding_id="bf-1",
        workload_digest="w",
        bottleneck_class=BottleneckClass.SERIALIZATION_BOUND,
        measured_runtime_share=0.4,
        evidence_digests=("campaign-digest", "cost-digest"),
        rationale="serialization dominates paired decomposition",
    )
    assert finding.status is FindingStatus.OBSERVED

    with pytest.raises(ValueError):
        BottleneckFinding(
            finding_id="bf-2",
            workload_digest="w",
            bottleneck_class=BottleneckClass.UNKNOWN,
            measured_runtime_share=0.0,
            evidence_digests=("evidence",),
            rationale="not enough evidence",
        )


def test_accelerator_candidate_is_hypothesis_and_has_amdahl_bound() -> None:
    finding = BottleneckFinding(
        finding_id="bf-1",
        workload_digest="w",
        bottleneck_class=BottleneckClass.COMPUTE_BOUND,
        measured_runtime_share=0.5,
        evidence_digests=("e1",),
        rationale="measured compute share",
    )
    candidate = AcceleratorCandidate(
        candidate_id="ac-1",
        finding_digest=finding.digest,
        target=AcceleratorTarget.MULTICORE,
        measured_runtime_share=finding.measured_runtime_share,
        assumed_component_speedup=4.0,
        estimated_transfer_cost_ns=0,
        verification_strategy="bit-identical semantic result digest plus full invariant path",
    )
    assert candidate.status is FindingStatus.HYPOTHESIS
    assert candidate.amdahl_upper_bound == pytest.approx(1.6)

    with pytest.raises(ValueError):
        AcceleratorCandidate(
            candidate_id="ac-2",
            finding_digest=finding.digest,
            target=AcceleratorTarget.GPU,
            measured_runtime_share=0.5,
            assumed_component_speedup=1.0,
            estimated_transfer_cost_ns=100,
            verification_strategy="invalid no-speedup assumption",
        )
