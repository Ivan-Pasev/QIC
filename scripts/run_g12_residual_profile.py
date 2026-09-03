#!/usr/bin/env python3
"""Run bounded G12 residual canonicalization characterization.

This campaign measures the optimized G11 production path plus deliberately
labeled proxy microkernels. Proxy timing is evidence about one operation in one
environment; it is not exact nested attribution and must not be subtracted as
if it were a causal stage measurement.
"""

from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import asdict
from pathlib import Path

from qic.core.canonical import _encode_value, _json_string, canonical_bytes
from qic.core.digest import digest_hex
from qic.observatory import MeasurementClass, PerformanceEnvironment, PerformanceObservatory, WorkloadDescriptor

SIZES = (10, 100, 1_000)
CLAIM_BOUNDARY = (
    "Environment-specific G12 residual-cost characterization only. Exact production-path "
    "measurements and proxy microkernels are distinguished explicitly. Proxy timings are not "
    "exact nested attribution. No accelerator, native extension, hardware, federation, T4/T5, "
    "maturity, or universal performance inference."
)


def _summary(run) -> dict[str, int | float | None]:
    peaks = [sample.peak_traced_bytes for sample in run.samples if sample.peak_traced_bytes is not None]
    return {
        "count": run.summary.count,
        "minimum_ns": run.summary.minimum_ns,
        "median_ns": run.summary.median_ns,
        "mean_ns": run.summary.mean_ns,
        "p90_ns": run.summary.p90_ns,
        "p95_ns": run.summary.p95_ns,
        "maximum_ns": run.summary.maximum_ns,
        "stddev_ns": run.summary.stddev_ns,
        "median_peak_traced_bytes": statistics.median(peaks) if peaks else None,
        "maximum_peak_traced_bytes": max(peaks) if peaks else None,
    }


def _run(observatory, *, workload_id, title, size, operation, warmups, repetitions, trace_memory):
    descriptor = WorkloadDescriptor(
        workload_id=workload_id,
        title=title,
        measurement_class=MeasurementClass.MICROKERNEL,
        size=size,
        operations_per_run=1,
        assurance_profile="G12_READ_ONLY_CHARACTERIZATION",
    )
    run = observatory.run(
        descriptor,
        operation,
        result_identity=lambda value: value,
        warmups=warmups,
        repetitions=repetitions,
        trace_memory=trace_memory,
    )
    return {
        "workload_id": workload_id,
        "workload_digest": descriptor.digest,
        "summary": _summary(run),
        "result_digest": run.samples[0].result_digest,
    }


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
            "campaign": "QIC-G12-RESIDUAL-PROFILE/1.0",
            "sizes": SIZES,
            "warmups": args.warmups,
            "repetitions": args.repetitions,
            "memory_tracing": True,
        }
    )
    observatory = PerformanceObservatory(environment)
    records: list[dict[str, object]] = []

    for size in SIZES:
        payload = tuple(range(size))
        encoded_leaves = tuple(_encode_value(item) for item in payload)
        text_payload = tuple(str(item) for item in payload)
        mapping_payload = {f"k{item:06d}": item for item in reversed(range(size))}
        set_payload = set(range(size))

        production_bytes = canonical_bytes(payload)
        production_inner = _encode_value(payload)
        if production_bytes != b'{"$canonical":"QIC-CANONICAL/1.0","value":' + production_inner + b'}':
            raise SystemExit(f"production envelope identity failed at size={size}")

        exact = []
        exact.append(
            _run(
                observatory,
                workload_id="g12.exact.canonical_bytes",
                title="G12 exact production canonical_bytes",
                size=size,
                operation=lambda payload=payload: canonical_bytes(payload),
                warmups=args.warmups,
                repetitions=args.repetitions,
                trace_memory=True,
            )
        )
        exact.append(
            _run(
                observatory,
                workload_id="g12.exact.encode_value_tuple",
                title="G12 exact production tuple _encode_value",
                size=size,
                operation=lambda payload=payload: _encode_value(payload),
                warmups=args.warmups,
                repetitions=args.repetitions,
                trace_memory=True,
            )
        )
        exact.append(
            _run(
                observatory,
                workload_id="g12.exact.digest_hex",
                title="G12 exact digest_hex end path",
                size=size,
                operation=lambda payload=payload: digest_hex(payload, domain="g12.residual"),
                warmups=args.warmups,
                repetitions=args.repetitions,
                trace_memory=True,
            )
        )

        proxies = []
        proxies.append(
            _run(
                observatory,
                workload_id="g12.proxy.integer_leaf_batch",
                title="Proxy: encode integer leaves independently",
                size=size,
                operation=lambda payload=payload: tuple(_encode_value(item) for item in payload),
                warmups=args.warmups,
                repetitions=args.repetitions,
                trace_memory=True,
            )
        )
        proxies.append(
            _run(
                observatory,
                workload_id="g12.proxy.integer_text_batch",
                title="Proxy: decimal integer text emission",
                size=size,
                operation=lambda payload=payload: tuple(str(item).encode("ascii") for item in payload),
                warmups=args.warmups,
                repetitions=args.repetitions,
                trace_memory=True,
            )
        )
        proxies.append(
            _run(
                observatory,
                workload_id="g12.proxy.preencoded_join",
                title="Proxy: comma join of pre-encoded leaves",
                size=size,
                operation=lambda encoded_leaves=encoded_leaves: b','.join(encoded_leaves),
                warmups=args.warmups,
                repetitions=args.repetitions,
                trace_memory=True,
            )
        )
        proxies.append(
            _run(
                observatory,
                workload_id="g12.proxy.json_string_batch",
                title="Proxy: JSON string escaping/encoding batch",
                size=size,
                operation=lambda text_payload=text_payload: tuple(_json_string(item) for item in text_payload),
                warmups=args.warmups,
                repetitions=args.repetitions,
                trace_memory=True,
            )
        )
        proxies.append(
            _run(
                observatory,
                workload_id="g12.proxy.mapping_encode",
                title="Proxy family: production mapping encoding with reversed input order",
                size=size,
                operation=lambda mapping_payload=mapping_payload: _encode_value(mapping_payload),
                warmups=args.warmups,
                repetitions=args.repetitions,
                trace_memory=True,
            )
        )
        proxies.append(
            _run(
                observatory,
                workload_id="g12.proxy.set_encode",
                title="Proxy family: production set encoding and ordering",
                size=size,
                operation=lambda set_payload=set_payload: _encode_value(set_payload),
                warmups=args.warmups,
                repetitions=args.repetitions,
                trace_memory=True,
            )
        )

        records.append(
            {
                "size": size,
                "exact_production_measurements": exact,
                "proxy_measurements": proxies,
                "interpretation_rule": (
                    "Exact measurements may be compared within this environment. Proxy measurements "
                    "indicate operation-scale behavior only and are not exact nested time shares."
                ),
            }
        )

    manifest = {
        "format": "QIC-G12-RESIDUAL-PROFILE/1.0",
        "claim_boundary": CLAIM_BOUNDARY,
        "environment": {**asdict(environment), "digest": environment.digest},
        "warmups": args.warmups,
        "repetitions": args.repetitions,
        "records": records,
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"pass": True, "environment": environment.digest, "sizes": len(records)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
