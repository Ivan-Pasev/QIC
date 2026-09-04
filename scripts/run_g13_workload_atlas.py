#!/usr/bin/env python3
"""Run the G13 canonical payload-family generalization matrix.

This script is read-only with respect to production state. Timing and traced
allocation are measured in separate channels. Exact production bytes are checked
against the frozen G1 reference for every payload before evidence is emitted.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from qic.core.canonical import _canonical_bytes_reference, canonical_bytes
from qic.core.digest import digest_hex
from qic.observatory import PerformanceEnvironment


FORMAT = "QIC-G13-WORKLOAD-ATLAS/1.0"
DEFAULT_SIZES = (10, 100, 1_000)


class AtlasEnum(Enum):
    A = "alpha"
    B = 2


@dataclass(frozen=True)
class AtlasRecord:
    index: int
    label: str
    active: bool


def payload_plain_int_tuple(size: int) -> object:
    return tuple(range(size))


def payload_plain_int_list(size: int) -> object:
    return list(range(size))


def payload_mixed_scalar_tuple(size: int) -> object:
    pattern: tuple[object, ...] = (1, True, "qic", b"bytes")
    return tuple(pattern[index % len(pattern)] for index in range(size))


def payload_string_tuple(size: int) -> object:
    samples = ("plain", 'quote\"', "slash\\", "line\nfeed", "unicode-Ω")
    return tuple(f"{samples[index % len(samples)]}-{index}" for index in range(size))


def payload_mapping(size: int) -> object:
    return {f"k{index:06d}": index for index in reversed(range(size))}


def payload_set(size: int) -> object:
    return {f"item-{index:06d}" for index in range(size)}


def payload_frozenset(size: int) -> object:
    return frozenset(range(size))


def payload_nested(size: int) -> object:
    width = max(1, size // 10)
    return {
        "tuples": tuple(range(width)),
        "lists": [list(range(width)) for _ in range(3)],
        "mapping": {f"n{index}": (index, str(index)) for index in range(width)},
    }


def payload_dataclass_tuple(size: int) -> object:
    return tuple(AtlasRecord(index=index, label=f"r-{index}", active=index % 2 == 0) for index in range(size))


def payload_enum_tuple(size: int) -> object:
    values = (AtlasEnum.A, AtlasEnum.B)
    return tuple(values[index % 2] for index in range(size))


FAMILIES: tuple[tuple[str, Callable[[int], object]], ...] = (
    ("plain_int_tuple", payload_plain_int_tuple),
    ("plain_int_list", payload_plain_int_list),
    ("mixed_scalar_tuple", payload_mixed_scalar_tuple),
    ("string_tuple", payload_string_tuple),
    ("string_key_mapping", payload_mapping),
    ("string_set", payload_set),
    ("int_frozenset", payload_frozenset),
    ("nested_structure", payload_nested),
    ("dataclass_tuple", payload_dataclass_tuple),
    ("enum_tuple", payload_enum_tuple),
)


def summarize(values: list[int]) -> dict[str, float | int]:
    ordered = sorted(values)
    return {
        "count": len(values),
        "minimum": ordered[0],
        "median": statistics.median(ordered),
        "mean": statistics.fmean(ordered),
        "maximum": ordered[-1],
    }


def timed(call: Callable[[], Any], warmups: int, repetitions: int) -> tuple[dict[str, float | int], str]:
    for _ in range(warmups):
        call()
    samples: list[int] = []
    identity: str | None = None
    for _ in range(repetitions):
        started = time.perf_counter_ns()
        result = call()
        samples.append(time.perf_counter_ns() - started)
        current = result.hex() if isinstance(result, bytes) else str(result)
        if identity is None:
            identity = current
        elif identity != current:
            raise RuntimeError("nondeterministic result identity during timing")
    assert identity is not None
    return summarize(samples), identity


def allocated(call: Callable[[], Any], repetitions: int) -> tuple[dict[str, float | int], str]:
    peaks: list[int] = []
    identity: str | None = None
    for _ in range(repetitions):
        tracemalloc.start()
        try:
            result = call()
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        peaks.append(peak)
        current = result.hex() if isinstance(result, bytes) else str(result)
        if identity is None:
            identity = current
        elif identity != current:
            raise RuntimeError("nondeterministic result identity during allocation measurement")
    assert identity is not None
    return summarize(peaks), identity


def measure_channel(call: Callable[[], Any], warmups: int, repetitions: int) -> dict[str, object]:
    timing, timing_identity = timed(call, warmups, repetitions)
    allocation, allocation_identity = allocated(call, repetitions)
    if timing_identity != allocation_identity:
        raise RuntimeError("timing/allocation semantic identity mismatch")
    return {"timing_ns": timing, "traced_peak_bytes": allocation, "result_identity": timing_identity}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--repetitions", type=int, default=9)
    parser.add_argument("--sizes", type=int, nargs="+", default=list(DEFAULT_SIZES))
    args = parser.parse_args()
    if args.repetitions <= 1:
        raise SystemExit("repetitions must be > 1")
    if args.warmups < 0 or any(size <= 0 for size in args.sizes):
        raise SystemExit("warmups must be >= 0 and sizes must be positive")

    args.output.mkdir(parents=True, exist_ok=True)
    environment = PerformanceEnvironment.capture(
        configuration={
            "campaign": FORMAT,
            "warmups": args.warmups,
            "repetitions": args.repetitions,
            "sizes": tuple(args.sizes),
            "families": tuple(name for name, _ in FAMILIES),
            "timing_trace_memory": False,
            "allocation_channel": "tracemalloc-separate",
        }
    )

    records: list[dict[str, object]] = []
    for family, factory in FAMILIES:
        for size in args.sizes:
            payload = factory(size)
            production = canonical_bytes(payload)
            reference = _canonical_bytes_reference(payload)
            if production != reference:
                raise RuntimeError(f"canonical byte mismatch: {family} size={size}")
            bytes_measurement = measure_channel(lambda payload=payload: canonical_bytes(payload), args.warmups, args.repetitions)
            digest_measurement = measure_channel(
                lambda payload=payload, family=family: digest_hex(payload, domain=f"g13.{family}"),
                args.warmups,
                args.repetitions,
            )
            records.append(
                {
                    "family": family,
                    "size": size,
                    "canonical_byte_length": len(production),
                    "byte_identity": True,
                    "canonical_bytes": bytes_measurement,
                    "digest_hex": digest_measurement,
                }
            )

    manifest = {
        "format": FORMAT,
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
        "measurement_policy": {
            "timing": "perf_counter_ns with tracemalloc disabled",
            "allocation": "separate tracemalloc peak channel",
            "byte_oracle": "frozen G1 _canonical_bytes_reference",
            "attribution": "no subtraction of independent timings as exact nested stage attribution",
        },
        "claim_boundary": (
            "Environment- and payload-family-specific characterization only. Production semantics are unchanged. "
            "No native extension, accelerator, hardware, federation, T4/T5, formal, security, deployment, "
            "maturity, or semantic-truth inference follows from this matrix."
        ),
        "records": records,
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": True, "families": len(FAMILIES), "records": len(records), "environment": environment.digest}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
