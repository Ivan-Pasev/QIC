#!/usr/bin/env python3
"""Measure the frozen G1 canonicalizer against the G11 direct encoder candidate.

Every size point is byte-gated before timing interpretation. Output is
environment-specific performance evidence, not a portable speed claim.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from qic.core.canonical import _canonical_bytes_reference, canonical_bytes
from qic.observatory import MeasurementClass, PerformanceEnvironment, PerformanceObservatory, WorkloadDescriptor


SIZES = (100, 1_000, 10_000)
THRESHOLD_PPM = 30_000  # 3%; below this is treated as stable/noise at this campaign scale.


def _samples_payload(run) -> list[dict[str, int | str | None]]:
    return [
        {
            "repetition": sample.repetition,
            "wall_time_ns": sample.wall_time_ns,
            "cpu_time_ns": sample.cpu_time_ns,
            "peak_traced_bytes": sample.peak_traced_bytes,
            "operations": sample.operations,
            "result_digest": sample.result_digest,
        }
        for sample in run.samples
    ]


def _classify(reference_ns: int, candidate_ns: int) -> tuple[str, int]:
    delta_ppm = ((candidate_ns - reference_ns) * 1_000_000) // reference_ns
    if delta_ppm > THRESHOLD_PPM:
        return "REGRESSION", delta_ppm
    if delta_ppm < -THRESHOLD_PPM:
        return "IMPROVEMENT", delta_ppm
    return "STABLE", delta_ppm


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--repetitions", type=int, default=15)
    args = parser.parse_args()
    if args.warmups < 0 or args.repetitions < 5:
        raise SystemExit("warmups must be >= 0 and repetitions must be >= 5")

    args.output.mkdir(parents=True, exist_ok=True)
    environment = PerformanceEnvironment.capture(
        configuration={
            "campaign": "G11-CANONICALIZER-COMPARE/1.0",
            "warmups": args.warmups,
            "repetitions": args.repetitions,
            "sizes": SIZES,
            "threshold_ppm": THRESHOLD_PPM,
        }
    )
    observatory = PerformanceObservatory(environment)
    records: list[dict[str, object]] = []

    for size in SIZES:
        payload = tuple(range(size))
        reference_bytes = _canonical_bytes_reference(payload)
        candidate_bytes = canonical_bytes(payload)
        if candidate_bytes != reference_bytes:
            raise SystemExit(f"byte identity failure at size {size}")

        base = WorkloadDescriptor(
            workload_id="g11.canonical.reference",
            title="Frozen G1 canonicalizer reference",
            measurement_class=MeasurementClass.MICROKERNEL,
            size=size,
            operations_per_run=1,
            assurance_profile="BYTE_IDENTITY_GATED",
        )
        candidate_descriptor = replace(
            base,
            workload_id="g11.canonical.candidate",
            title="G11 direct encoder candidate",
        )
        reference_run = observatory.run(
            base,
            lambda payload=payload: _canonical_bytes_reference(payload),
            result_identity=lambda value: value.hex(),
            warmups=args.warmups,
            repetitions=args.repetitions,
        )
        candidate_run = observatory.run(
            candidate_descriptor,
            lambda payload=payload: canonical_bytes(payload),
            result_identity=lambda value: value.hex(),
            warmups=args.warmups,
            repetitions=args.repetitions,
        )
        if reference_run.result != candidate_run.result:
            raise SystemExit(f"measured byte identity failure at size {size}")

        ref_median = int(reference_run.summary.median_ns)
        cand_median = int(candidate_run.summary.median_ns)
        classification, delta_ppm = _classify(ref_median, cand_median)
        records.append(
            {
                "size": size,
                "byte_identity": True,
                "reference": {
                    "median_ns": ref_median,
                    "samples": _samples_payload(reference_run),
                    "result_digest": reference_run.samples[0].result_digest,
                },
                "candidate": {
                    "median_ns": cand_median,
                    "samples": _samples_payload(candidate_run),
                    "result_digest": candidate_run.samples[0].result_digest,
                },
                "classification": classification,
                "candidate_delta_ppm": delta_ppm,
            }
        )

    manifest = {
        "format": "QIC-G11-CANONICALIZER-COMPARE/1.0",
        "claim_boundary": (
            "Environment-specific A/B software measurements only. Byte identity is mandatory; "
            "timing is not a cross-environment reproducibility target and implies no hardware claim."
        ),
        "threshold_ppm": THRESHOLD_PPM,
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
    target = args.output / "manifest.json"
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": True, "environment_digest": environment.digest, "records": len(records)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
