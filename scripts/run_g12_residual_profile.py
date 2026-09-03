#!/usr/bin/env python3
"""Run bounded G12 residual canonicalization characterization.

Timing and allocation are measured in separate channels. `tracemalloc` is never
enabled for the timing channel, because observer overhead would materially
change the measured serializer path. Proxy microkernels remain explicitly
non-attributive: they indicate operation-scale behavior, not exact nested time
shares inside `canonical_bytes`.
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
    "Environment-specific G12 residual-cost characterization only. Timing and allocation "
    "are separate measurement channels; tracemalloc is excluded from timing. Exact production-path "
    "measurements and proxy microkernels are distinguished explicitly. Proxy timings are not exact "
    "nested attribution. No accelerator, native extension, hardware, federation, T4/T5, maturity, "
    "or universal performance inference."
)


def _descriptor(workload_id: str, title: str, size: int, channel: str) -> WorkloadDescriptor:
    return WorkloadDescriptor(
        workload_id=f"{workload_id}.{channel}",
        title=f"{title} [{channel}]",
        measurement_class=MeasurementClass.MICROKERNEL,
        size=size,
        operations_per_run=1,
        assurance_profile=f"G12_READ_ONLY_{channel.upper()}",
    )


def _timing_summary(run) -> dict[str, int | float]:
    return {
        "count": run.summary.count,
        "minimum_ns": run.summary.minimum_ns,
        "median_ns": run.summary.median_ns,
        "mean_ns": run.summary.mean_ns,
        "p90_ns": run.summary.p90_ns,
        "p95_ns": run.summary.p95_ns,
        "maximum_ns": run.summary.maximum_ns,
        "stddev_ns": run.summary.stddev_ns,
    }


def _memory_summary(run) -> dict[str, int | float]:
    peaks = [sample.peak_traced_bytes for sample in run.samples]
    if any(peak is None for peak in peaks):
        raise RuntimeError("memory channel produced a sample without traced peak bytes")
    concrete = [int(peak) for peak in peaks if peak is not None]
    return {
        "count": len(concrete),
        "minimum_peak_traced_bytes": min(concrete),
        "median_peak_traced_bytes": statistics.median(concrete),
        "maximum_peak_traced_bytes": max(concrete),
    }


def _measure(
    observatory: PerformanceObservatory,
    *,
    workload_id: str,
    title: str,
    classification: str,
    size: int,
    operation,
    warmups: int,
    repetitions: int,
) -> dict[str, object]:
    timing_descriptor = _descriptor(workload_id, title, size, "timing")
    timing_run = observatory.run(
        timing_descriptor,
        operation,
        result_identity=lambda value: value,
        warmups=warmups,
        repetitions=repetitions,
        trace_memory=False,
    )

    memory_descriptor = _descriptor(workload_id, title, size, "memory")
    memory_run = observatory.run(
        memory_descriptor,
        operation,
        result_identity=lambda value: value,
        warmups=warmups,
        repetitions=repetitions,
        trace_memory=True,
    )

    if timing_run.samples[0].result_digest != memory_run.samples[0].result_digest:
        raise RuntimeError(f"result identity differs between timing and memory channels for {workload_id}")

    return {
        "workload_id": workload_id,
        "classification": classification,
        "timing_workload_digest": timing_descriptor.digest,
        "memory_workload_digest": memory_descriptor.digest,
        "result_digest": timing_run.samples[0].result_digest,
        "timing": _timing_summary(timing_run),
        "allocation": _memory_summary(memory_run),
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
            "campaign": "QIC-G12-RESIDUAL-PROFILE/2.0",
            "sizes": SIZES,
            "warmups": args.warmups,
            "repetitions": args.repetitions,
            "timing_trace_memory": False,
            "allocation_trace_memory": True,
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

        exact = [
            _measure(
                observatory,
                workload_id="g12.exact.canonical_bytes",
                title="G12 exact production canonical_bytes",
                classification="EXACT_PRODUCTION_PATH",
                size=size,
                operation=lambda payload=payload: canonical_bytes(payload),
                warmups=args.warmups,
                repetitions=args.repetitions,
            ),
            _measure(
                observatory,
                workload_id="g12.exact.encode_value_tuple",
                title="G12 exact production tuple _encode_value",
                classification="EXACT_PRODUCTION_INTERNAL",
                size=size,
                operation=lambda payload=payload: _encode_value(payload),
                warmups=args.warmups,
                repetitions=args.repetitions,
            ),
            _measure(
                observatory,
                workload_id="g12.exact.digest_hex",
                title="G12 exact digest_hex end path",
                classification="EXACT_END_PATH",
                size=size,
                operation=lambda payload=payload: digest_hex(payload, domain="g12.residual"),
                warmups=args.warmups,
                repetitions=args.repetitions,
            ),
        ]

        proxies = [
            _measure(
                observatory,
                workload_id="g12.proxy.integer_leaf_batch",
                title="Proxy: encode integer leaves independently",
                classification="PROXY_NON_ATTRIBUTIVE",
                size=size,
                operation=lambda payload=payload: tuple(_encode_value(item) for item in payload),
                warmups=args.warmups,
                repetitions=args.repetitions,
            ),
            _measure(
                observatory,
                workload_id="g12.proxy.integer_text_batch",
                title="Proxy: decimal integer text emission",
                classification="PROXY_NON_ATTRIBUTIVE",
                size=size,
                operation=lambda payload=payload: tuple(str(item).encode("ascii") for item in payload),
                warmups=args.warmups,
                repetitions=args.repetitions,
            ),
            _measure(
                observatory,
                workload_id="g12.proxy.preencoded_join",
                title="Proxy: comma join of pre-encoded leaves",
                classification="PROXY_NON_ATTRIBUTIVE",
                size=size,
                operation=lambda encoded_leaves=encoded_leaves: b','.join(encoded_leaves),
                warmups=args.warmups,
                repetitions=args.repetitions,
            ),
            _measure(
                observatory,
                workload_id="g12.proxy.json_string_batch",
                title="Proxy: JSON string escaping/encoding batch",
                classification="PROXY_NON_ATTRIBUTIVE",
                size=size,
                operation=lambda text_payload=text_payload: tuple(_json_string(item) for item in text_payload),
                warmups=args.warmups,
                repetitions=args.repetitions,
            ),
            _measure(
                observatory,
                workload_id="g12.proxy.mapping_encode",
                title="Proxy family: production mapping encoding with reversed input order",
                classification="PAYLOAD_FAMILY_COMPARISON",
                size=size,
                operation=lambda mapping_payload=mapping_payload: _encode_value(mapping_payload),
                warmups=args.warmups,
                repetitions=args.repetitions,
            ),
            _measure(
                observatory,
                workload_id="g12.proxy.set_encode",
                title="Proxy family: production set encoding and ordering",
                classification="PAYLOAD_FAMILY_COMPARISON",
                size=size,
                operation=lambda set_payload=set_payload: _encode_value(set_payload),
                warmups=args.warmups,
                repetitions=args.repetitions,
            ),
        ]

        records.append(
            {
                "size": size,
                "exact_production_measurements": exact,
                "proxy_measurements": proxies,
                "interpretation_rule": (
                    "Timing excludes tracemalloc. Allocation uses a separate traced run. Exact measurements "
                    "may be compared within this environment. Proxy measurements indicate operation-scale "
                    "behavior only and are not exact nested time shares."
                ),
            }
        )

    manifest = {
        "format": "QIC-G12-RESIDUAL-PROFILE/2.0",
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
