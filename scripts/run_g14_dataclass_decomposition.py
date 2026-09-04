#!/usr/bin/env python3
"""Run the G14 Phase-A dataclass canonicalization decomposition campaign.

The campaign is characterization-only. Independent proxy microkernels are
measured separately and MUST NOT be added, subtracted, or interpreted as exact
nested stage shares. Timing and traced allocation use separate channels.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import tracemalloc
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Callable

from qic.core.canonical import (
    _canonical_bytes_reference,
    _encode_value,
    _json_string,
    _type_name,
    canonical_bytes,
)
from qic.observatory import PerformanceEnvironment


FORMAT = "QIC-G14-DATACLASS-DECOMPOSITION/1.0"
DEFAULT_SIZES = (10, 100, 1_000)


@dataclass(frozen=True)
class SmallRecord:
    index: int
    label: str
    active: bool


@dataclass(frozen=True)
class WideRecord:
    a: int
    b: int
    c: int
    d: int
    e: int
    f: int
    g: int
    h: int


@dataclass(frozen=True, slots=True)
class SlottedRecord:
    index: int
    label: str
    left: int
    right: int


@dataclass(frozen=True)
class MixedRecord:
    index: int
    label: str
    active: bool
    payload: bytes
    values: tuple[int, ...]


def build_small(size: int) -> tuple[SmallRecord, ...]:
    return tuple(SmallRecord(i, f"r-{i}", i % 2 == 0) for i in range(size))


def build_wide(size: int) -> tuple[WideRecord, ...]:
    return tuple(WideRecord(i, i + 1, i + 2, i + 3, i + 4, i + 5, i + 6, i + 7) for i in range(size))


def build_slotted(size: int) -> tuple[SlottedRecord, ...]:
    return tuple(SlottedRecord(i, f"s-{i}", i * 2, i * 3) for i in range(size))


def build_mixed(size: int) -> tuple[MixedRecord, ...]:
    return tuple(
        MixedRecord(i, f"m-{i}", i % 2 == 0, f"b-{i}".encode("ascii"), (i, i + 1, i + 2))
        for i in range(size)
    )


SHAPES: tuple[tuple[str, Callable[[int], tuple[object, ...]]], ...] = (
    ("small_frozen_3", build_small),
    ("wide_frozen_8", build_wide),
    ("slotted_frozen_4", build_slotted),
    ("mixed_frozen_5", build_mixed),
)


def _prepare_metadata(cls: type[object]) -> tuple[bytes, tuple[tuple[str, bytes], ...]]:
    """Prepare reusable metadata in the form a later Phase-B candidate could consume."""

    ordered = sorted(fields(cls), key=lambda item: item.name)
    type_name_json = _json_string(f"{cls.__module__}.{cls.__qualname__}")
    field_metadata = tuple((field.name, _json_string(field.name) + b":") for field in ordered)
    return type_name_json, field_metadata


def _checksum_bytes(value: bytes) -> int:
    return len(value) + (value[0] if value else 0) + (value[-1] if value else 0)


def _fields_lookup_batch(items: tuple[object, ...]) -> int:
    return sum(len(fields(item)) for item in items)


def _sorted_fields_batch(items: tuple[object, ...]) -> int:
    total = 0
    for item in items:
        ordered = sorted(fields(item), key=lambda field: field.name)
        total += sum(len(field.name) for field in ordered)
    return total


def _type_name_json_batch(items: tuple[object, ...]) -> int:
    return sum(_checksum_bytes(_json_string(_type_name(item))) for item in items)


def _field_name_json_batch(items: tuple[object, ...]) -> int:
    total = 0
    for item in items:
        for field in sorted(fields(item), key=lambda field: field.name):
            total += _checksum_bytes(_json_string(field.name))
    return total


def _getattr_batch(items: tuple[object, ...]) -> int:
    count = 0
    for item in items:
        for field in sorted(fields(item), key=lambda field: field.name):
            getattr(item, field.name)
            count += 1
    return count


def _recursive_value_encode_batch(items: tuple[object, ...]) -> int:
    total = 0
    for item in items:
        for field in sorted(fields(item), key=lambda field: field.name):
            total += len(_encode_value(getattr(item, field.name)))
    return total


def _metadata_prepare_repeated(items: tuple[object, ...]) -> int:
    total = 0
    for item in items:
        type_json, field_metadata = _prepare_metadata(type(item))
        total += len(type_json) + sum(len(prefix) for _, prefix in field_metadata)
    return total


def _metadata_reuse_proxy(items: tuple[object, ...]) -> int:
    """Model reuse of one prepared descriptor without constructing candidate output."""

    if not items:
        return 0
    type_json, field_metadata = _prepare_metadata(type(items[0]))
    descriptor_size = len(type_json) + sum(len(prefix) for _, prefix in field_metadata)
    total = 0
    for item in items:
        if type(item) is not type(items[0]):
            raise RuntimeError("metadata reuse proxy requires one exact dataclass type")
        total += descriptor_size
    return total


def _full_item_encode_batch(items: tuple[object, ...]) -> int:
    return sum(len(_encode_value(item)) for item in items)


PROXIES: tuple[tuple[str, Callable[[tuple[object, ...]], int]], ...] = (
    ("fields_lookup", _fields_lookup_batch),
    ("sorted_fields", _sorted_fields_batch),
    ("type_name_json", _type_name_json_batch),
    ("field_name_json", _field_name_json_batch),
    ("getattr_reads", _getattr_batch),
    ("recursive_value_encode", _recursive_value_encode_batch),
    ("metadata_prepare_repeated", _metadata_prepare_repeated),
    ("metadata_reuse_proxy", _metadata_reuse_proxy),
    ("full_item_encode", _full_item_encode_batch),
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


def _identity(value: Any) -> str:
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, int):
        return str(value)
    raise TypeError(f"unsupported measurement identity type: {type(value)!r}")


def timed(call: Callable[[], Any], warmups: int, repetitions: int) -> tuple[dict[str, float | int], str]:
    for _ in range(warmups):
        call()
    samples: list[int] = []
    stable: str | None = None
    for _ in range(repetitions):
        started = time.perf_counter_ns()
        result = call()
        samples.append(time.perf_counter_ns() - started)
        current = _identity(result)
        if stable is None:
            stable = current
        elif stable != current:
            raise RuntimeError("nondeterministic result identity during timing")
    assert stable is not None
    return summarize(samples), stable


def allocated(call: Callable[[], Any], repetitions: int) -> tuple[dict[str, float | int], str]:
    peaks: list[int] = []
    stable: str | None = None
    for _ in range(repetitions):
        tracemalloc.start()
        try:
            result = call()
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        peaks.append(peak)
        current = _identity(result)
        if stable is None:
            stable = current
        elif stable != current:
            raise RuntimeError("nondeterministic result identity during allocation measurement")
    assert stable is not None
    return summarize(peaks), stable


def measure(call: Callable[[], Any], warmups: int, repetitions: int) -> dict[str, object]:
    timing, timing_identity = timed(call, warmups, repetitions)
    allocation, allocation_identity = allocated(call, repetitions)
    if timing_identity != allocation_identity:
        raise RuntimeError("timing/allocation result identity mismatch")
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
            "phase": "A-decomposition-only",
            "warmups": args.warmups,
            "repetitions": args.repetitions,
            "sizes": tuple(args.sizes),
            "shapes": tuple(name for name, _ in SHAPES),
            "proxies": tuple(name for name, _ in PROXIES),
            "timing_trace_memory": False,
            "allocation_channel": "tracemalloc-separate",
        }
    )

    records: list[dict[str, object]] = []
    for shape, factory in SHAPES:
        for size in args.sizes:
            items = factory(size)
            production = canonical_bytes(items)
            reference = _canonical_bytes_reference(items)
            if production != reference:
                raise RuntimeError(f"canonical byte mismatch for {shape} size={size}")

            proxy_results = {
                name: measure(lambda call=call, items=items: call(items), args.warmups, args.repetitions)
                for name, call in PROXIES
            }
            full_tuple = measure(lambda items=items: canonical_bytes(items), args.warmups, args.repetitions)
            if bytes.fromhex(str(full_tuple["result_identity"])) != reference:
                raise RuntimeError(f"full-tuple measured identity mismatch for {shape} size={size}")

            records.append(
                {
                    "shape": shape,
                    "size": size,
                    "field_count": len(fields(type(items[0]))),
                    "canonical_byte_length": len(production),
                    "byte_identity": True,
                    "proxies": proxy_results,
                    "full_tuple_canonical": full_tuple,
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
            "phase": "A decomposition only; no production candidate",
            "timing": "perf_counter_ns with tracemalloc disabled",
            "allocation": "separate tracemalloc peak channel",
            "byte_oracle": "frozen G1 _canonical_bytes_reference",
            "proxy_semantics": (
                "independent microkernels are non-additive and non-attributive; do not subtract or sum "
                "their timings to claim exact nested stage shares"
            ),
        },
        "claim_boundary": (
            "Environment-specific dataclass-path characterization only. No production canonicalizer change, "
            "native extension, accelerator, hardware, federation, T4/T5, formal, security, deployment, "
            "maturity, or semantic-truth inference follows from this campaign."
        ),
        "records": records,
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": True, "phase": "A", "shapes": len(SHAPES), "records": len(records), "environment": environment.digest}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
