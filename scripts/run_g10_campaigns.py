#!/usr/bin/env python3
"""Run a bounded G10 measurement campaign over safe existing microkernels.

The output contains raw environment-bound measurements. Timing values are not
reproducibility targets and are not interpreted as bottleneck or hardware claims.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from qic.core.canonical import canonical_bytes
from qic.core.digest import digest_hex
from qic.observatory import PerformanceEnvironment
from qic.performance_campaign import CampaignSpec, PerformanceCampaignStore, execute_campaign
from qic.workload_atlas import atlas_by_id


CAMPAIGN_WORKLOADS = ("canonical.bytes", "canonical.digest")
CAMPAIGN_SIZES = (10, 100, 1_000)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=7)
    parser.add_argument("--warmups", type=int, default=2)
    args = parser.parse_args()
    if args.repetitions <= 1:
        raise SystemExit("repetitions must be > 1 for baseline evidence")
    if args.warmups < 0:
        raise SystemExit("warmups must be >= 0")

    args.output.mkdir(parents=True, exist_ok=True)
    evidence_dir = args.output / "campaigns"
    store = PerformanceCampaignStore(evidence_dir)
    atlas = atlas_by_id()
    environment = PerformanceEnvironment.capture(
        configuration={
            "campaign": "G10-BASELINE/1.0",
            "assurance_profile": "FULL_DECLARED_PATH",
            "warmups": args.warmups,
            "repetitions": args.repetitions,
            "workloads": CAMPAIGN_WORKLOADS,
            "sizes": CAMPAIGN_SIZES,
        }
    )

    records: list[dict[str, object]] = []
    for workload_id in CAMPAIGN_WORKLOADS:
        entry = atlas[workload_id]
        for size in CAMPAIGN_SIZES:
            descriptor = replace(
                entry.workload,
                size=size,
                operations_per_run=1,
            )
            payload = tuple(range(size))
            campaign_id = f"g10-baseline-{workload_id}-s{size}"
            spec = CampaignSpec(
                campaign_id=campaign_id,
                workload=descriptor,
                environment=environment,
                warmups=args.warmups,
                repetitions=args.repetitions,
            )
            if workload_id == "canonical.bytes":
                execution = execute_campaign(
                    spec,
                    lambda payload=payload: canonical_bytes(payload),
                    result_identity=lambda value: value.hex(),
                )
            else:
                execution = execute_campaign(
                    spec,
                    lambda payload=payload: digest_hex(payload, domain="g10.baseline"),
                )
            path = store.persist(execution.record)
            summary = execution.record.summary
            records.append(
                {
                    "campaign_id": campaign_id,
                    "record_digest": execution.record.digest,
                    "relative_path": str(path.relative_to(args.output)),
                    "workload_id": workload_id,
                    "size": size,
                    "sample_count": len(execution.record.samples),
                    "result_digest": execution.record.result_digest,
                    "derived_summary": {
                        "minimum_ns": summary.minimum_ns,
                        "median_ns": summary.median_ns,
                        "mean_ns": summary.mean_ns,
                        "p90_ns": summary.p90_ns,
                        "p95_ns": summary.p95_ns,
                        "maximum_ns": summary.maximum_ns,
                        "stddev_ns": summary.stddev_ns,
                    },
                }
            )

    manifest = {
        "format": "QIC-G10-BASELINE-MANIFEST/1.0",
        "claim_boundary": (
            "Environment-specific raw performance evidence only; no bottleneck, accelerator, "
            "hardware, federation, T4/T5, maturity, or semantic-truth inference."
        ),
        "environment": {
            "digest": environment.digest,
            "python_implementation": environment.python_implementation,
            "python_version": environment.python_version,
            "os_system": environment.os_system,
            "os_release": environment.os_release,
            "machine": environment.machine,
            "processor": environment.processor,
            "logical_cpu_count": environment.logical_cpu_count,
            "configuration_digest": environment.configuration_digest,
        },
        "records": records,
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"pass": True, "environment_digest": environment.digest, "campaigns": len(records)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
