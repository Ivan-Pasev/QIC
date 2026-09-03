from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from qic.core.canonical import _canonical_bytes_reference, canonical_bytes
from qic.observatory import MeasurementClass, PerformanceEnvironment, WorkloadDescriptor
from qic.performance_campaign import CampaignSpec, PerformanceCampaignStore, execute_campaign

CLAIM_BOUNDARY = (
    "Same-environment reference-versus-candidate algorithmic evidence only; "
    "exact QIC-CANONICAL/1.0 byte identity is mandatory. No accelerator, hardware, "
    "federation, T4/T5, maturity, or universal performance inference."
)


def _summary(record):
    summary = record.summary
    return {
        "count": summary.count,
        "minimum_ns": summary.minimum_ns,
        "median_ns": summary.median_ns,
        "mean_ns": summary.mean_ns,
        "p90_ns": summary.p90_ns,
        "p95_ns": summary.p95_ns,
        "maximum_ns": summary.maximum_ns,
        "stddev_ns": summary.stddev_ns,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--repetitions", type=int, default=15)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    store = PerformanceCampaignStore(args.output / "campaigns")
    environment = PerformanceEnvironment.capture(
        configuration={
            "campaign": "QIC-G11-CANONICAL-COMPARISON/1.0",
            "assurance_profile": "BYTE_IDENTITY_REQUIRED",
        }
    )

    records = []
    for size in (10, 100, 1000):
        payload = tuple(range(size))
        reference_bytes = _canonical_bytes_reference(payload)
        candidate_bytes = canonical_bytes(payload)
        if candidate_bytes != reference_bytes:
            raise SystemExit(f"canonical byte identity failed before measurement at size={size}")

        paired = []
        for implementation, operation in (
            ("reference", lambda payload=payload: _canonical_bytes_reference(payload)),
            ("candidate", lambda payload=payload: canonical_bytes(payload)),
        ):
            workload = WorkloadDescriptor(
                workload_id=f"g11.canonical.{implementation}",
                title=f"G11 canonicalizer {implementation}",
                measurement_class=MeasurementClass.MICROKERNEL,
                size=size,
                operations_per_run=1,
                assurance_profile="BYTE_IDENTITY_REQUIRED",
            )
            spec = CampaignSpec(
                campaign_id=f"g11-{implementation}-s{size}",
                workload=workload,
                environment=environment,
                warmups=args.warmups,
                repetitions=args.repetitions,
                trace_memory=False,
            )
            execution = execute_campaign(spec, operation, result_identity=lambda value: value)
            path = store.persist(execution.record)
            paired.append(
                {
                    "implementation": implementation,
                    "relative_path": str(path.relative_to(args.output)),
                    "record_digest": execution.record.digest,
                    "result_digest": execution.record.result_digest,
                    "sample_count": len(execution.record.samples),
                    "derived_summary": _summary(execution.record),
                }
            )

        if paired[0]["result_digest"] != paired[1]["result_digest"]:
            raise SystemExit(f"semantic result digest diverged at size={size}")

        reference_median = paired[0]["derived_summary"]["median_ns"]
        candidate_median = paired[1]["derived_summary"]["median_ns"]
        records.append(
            {
                "size": size,
                "byte_identity": True,
                "reference": paired[0],
                "candidate": paired[1],
                "derived_candidate_over_reference": candidate_median / reference_median,
                "derived_improvement_fraction": (reference_median - candidate_median) / reference_median,
            }
        )

    manifest = {
        "format": "QIC-G11-CANONICAL-COMPARISON-MANIFEST/1.0",
        "claim_boundary": CLAIM_BOUNDARY,
        "environment": {**asdict(environment), "digest": environment.digest},
        "warmups": args.warmups,
        "repetitions": args.repetitions,
        "records": records,
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
