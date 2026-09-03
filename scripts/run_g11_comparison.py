from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import asdict
from pathlib import Path

from qic.core.canonical import _canonical_bytes_reference, canonical_bytes
from qic.core.digest import digest_hex
from qic.observatory import MeasurementClass, PerformanceEnvironment, WorkloadDescriptor
from qic.performance_campaign import CampaignSpec, PerformanceCampaignStore, execute_campaign

CLAIM_BOUNDARY = (
    "Counterbalanced same-environment reference-versus-candidate algorithmic evidence only; "
    "exact QIC-CANONICAL/1.0 byte identity is mandatory. Residual digest-path decomposition "
    "is an estimate from independently timed same-job medians. No accelerator, hardware, "
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


def _run(store, environment, output, *, size, implementation, order, operation, warmups, repetitions):
    workload = WorkloadDescriptor(
        workload_id=f"g11.canonical.{implementation}",
        title=f"G11 canonicalizer {implementation}",
        measurement_class=MeasurementClass.MICROKERNEL,
        size=size,
        operations_per_run=1,
        assurance_profile="BYTE_IDENTITY_REQUIRED",
    )
    spec = CampaignSpec(
        campaign_id=f"g11-{order}-{implementation}-s{size}",
        workload=workload,
        environment=environment,
        warmups=warmups,
        repetitions=repetitions,
        trace_memory=False,
    )
    execution = execute_campaign(spec, operation, result_identity=lambda value: value)
    path = store.persist(execution.record)
    return {
        "implementation": implementation,
        "order": order,
        "relative_path": str(path.relative_to(output)),
        "record_digest": execution.record.digest,
        "result_digest": execution.record.result_digest,
        "sample_count": len(execution.record.samples),
        "derived_summary": _summary(execution.record),
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
            "campaign": "QIC-G11-CANONICAL-COMPARISON/2.0",
            "assurance_profile": "BYTE_IDENTITY_REQUIRED",
            "counterbalanced": True,
        }
    )

    records = []
    for size in (10, 100, 1000):
        payload = tuple(range(size))
        reference_bytes = _canonical_bytes_reference(payload)
        candidate_bytes = canonical_bytes(payload)
        if candidate_bytes != reference_bytes:
            raise SystemExit(f"canonical byte identity failed before measurement at size={size}")

        operations = {
            "reference": lambda payload=payload: _canonical_bytes_reference(payload),
            "candidate": lambda payload=payload: canonical_bytes(payload),
        }
        orders = (
            ("reference-first", ("reference", "candidate")),
            ("candidate-first", ("candidate", "reference")),
        )
        order_records = []
        reference_medians = []
        candidate_medians = []
        semantic_digest = None
        compatibility_reference = None
        compatibility_candidate = None
        for order_name, sequence in orders:
            pair = []
            for implementation in sequence:
                item = _run(
                    store,
                    environment,
                    args.output,
                    size=size,
                    implementation=implementation,
                    order=order_name,
                    operation=operations[implementation],
                    warmups=args.warmups,
                    repetitions=args.repetitions,
                )
                pair.append(item)
                if implementation == "reference":
                    reference_medians.append(item["derived_summary"]["median_ns"])
                    compatibility_reference = compatibility_reference or item
                else:
                    candidate_medians.append(item["derived_summary"]["median_ns"])
                    compatibility_candidate = compatibility_candidate or item
                semantic_digest = semantic_digest or item["result_digest"]
                if item["result_digest"] != semantic_digest:
                    raise SystemExit(f"semantic result digest diverged at size={size}")
            order_records.append({"order": order_name, "measurements": pair})

        digest_item = _run(
            store,
            environment,
            args.output,
            size=size,
            implementation="digest",
            order="residual",
            operation=lambda payload=payload: digest_hex(payload, domain="g11.residual"),
            warmups=args.warmups,
            repetitions=args.repetitions,
        )

        reference_median = statistics.median(reference_medians)
        candidate_median = statistics.median(candidate_medians)
        digest_median = digest_item["derived_summary"]["median_ns"]
        serialization_share_ppm = None
        if candidate_median <= digest_median:
            serialization_share_ppm = round(candidate_median * 1_000_000 / digest_median)

        records.append(
            {
                "size": size,
                "byte_identity": True,
                "reference": compatibility_reference,
                "candidate": compatibility_candidate,
                "orders": order_records,
                "digest": digest_item,
                "derived_reference_median_ns": reference_median,
                "derived_candidate_median_ns": candidate_median,
                "derived_candidate_over_reference": candidate_median / reference_median,
                "derived_improvement_fraction": (reference_median - candidate_median) / reference_median,
                "derived_digest_median_ns": digest_median,
                "derived_serialization_share_ppm": serialization_share_ppm,
            }
        )

    manifest = {
        "format": "QIC-G11-CANONICAL-COMPARISON-MANIFEST/1.0",
        "measurement_revision": "counterbalanced-v2",
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
