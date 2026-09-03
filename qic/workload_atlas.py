"""Declared G10 workload atlas over kernels that exist in the G0-G9 stack."""

from __future__ import annotations

import importlib
from typing import Callable

from .observatory import MeasurementClass, WorkloadDescriptor
from .performance_evidence import WorkloadAtlasEntry


CLAIM_BOUNDARY = (
    "Performance measurement only; no semantic, authority, maturity, accelerator, "
    "federation, hardware, T4, or T5 promotion."
)


def resolve_kernel(path: str) -> object:
    """Resolve a dotted module/symbol path, failing closed on atlas drift."""

    parts = path.split(".")
    if any(not part for part in parts):
        raise ValueError("kernel path must be a non-empty dotted path")

    module = None
    split_at = 0
    for index in range(len(parts), 0, -1):
        try:
            module = importlib.import_module(".".join(parts[:index]))
        except ModuleNotFoundError:
            continue
        split_at = index
        break
    if module is None:
        raise ImportError(f"cannot resolve module prefix for {path!r}")

    value: object = module
    for name in parts[split_at:]:
        value = getattr(value, name)
    return value


def _entry(
    workload_id: str,
    title: str,
    kernel: str,
    measurement_class: MeasurementClass,
    scale_sizes: tuple[int, ...],
) -> WorkloadAtlasEntry:
    return WorkloadAtlasEntry(
        workload=WorkloadDescriptor(
            workload_id=workload_id,
            title=title,
            measurement_class=measurement_class,
            size=scale_sizes[0],
            operations_per_run=1,
            assurance_profile="FULL_DECLARED_PATH",
        ),
        kernel=kernel,
        scale_sizes=scale_sizes,
        claim_boundary=CLAIM_BOUNDARY,
    )


WORKLOAD_ATLAS: tuple[WorkloadAtlasEntry, ...] = (
    _entry(
        "canonical.bytes",
        "Canonical serialization",
        "qic.core.canonical.canonical_bytes",
        MeasurementClass.MICROKERNEL,
        (1, 10, 100, 1_000, 10_000),
    ),
    _entry(
        "canonical.digest",
        "Domain-separated canonical digest",
        "qic.core.digest.digest_hex",
        MeasurementClass.MICROKERNEL,
        (1, 10, 100, 1_000, 10_000),
    ),
    _entry(
        "transition.execute",
        "Constitutional transition execution",
        "qic.core.transition.TransitionEngine.execute",
        MeasurementClass.END_TO_END,
        (1, 10, 100, 1_000),
    ),
    _entry(
        "chrono.verify",
        "Chrono chain verification",
        "qic.core.chrono.ChronoChain.verify",
        MeasurementClass.END_TO_END,
        (1, 10, 100, 1_000),
    ),
    _entry(
        "kbi.supporting_evidence",
        "KBI supporting-evidence query",
        "qic.core.kbi.KBIState.supporting_evidence",
        MeasurementClass.MICROKERNEL,
        (1, 10, 100, 1_000, 10_000),
    ),
    _entry(
        "journal.scan",
        "Durable journal startup scan",
        "qic.core.journal_store.JournalFileStore.scan",
        MeasurementClass.END_TO_END,
        (1, 10, 100, 1_000),
    ),
    _entry(
        "recovery.reconcile",
        "Conservative recovery reconciliation",
        "qic.core.recovery.reconcile_recovery",
        MeasurementClass.END_TO_END,
        (1, 10, 100, 1_000),
    ),
    _entry(
        "qualification.verify",
        "G8 adversarial qualification",
        "qic.qualification.qualification_verify",
        MeasurementClass.END_TO_END,
        (1,),
    ),
    _entry(
        "aggregate.verify",
        "Aggregate structural verification",
        "qic.cli.aggregate_verify",
        MeasurementClass.END_TO_END,
        (1,),
    ),
)


def atlas_by_id() -> dict[str, WorkloadAtlasEntry]:
    return {entry.workload.workload_id: entry for entry in WORKLOAD_ATLAS}


def verify_atlas() -> dict[str, object]:
    resolved: list[str] = []
    failures: list[str] = []
    ids: set[str] = set()
    for entry in WORKLOAD_ATLAS:
        workload_id = entry.workload.workload_id
        if workload_id in ids:
            failures.append(f"duplicate:{workload_id}")
            continue
        ids.add(workload_id)
        try:
            target = resolve_kernel(entry.kernel)
        except (AttributeError, ImportError, ModuleNotFoundError, ValueError) as exc:
            failures.append(f"{workload_id}:{type(exc).__name__}")
            continue
        if not callable(target):
            failures.append(f"{workload_id}:not-callable")
            continue
        resolved.append(workload_id)
    return {
        "pass": not failures,
        "resolved": tuple(resolved),
        "failures": tuple(failures),
        "claim_boundary": CLAIM_BOUNDARY,
    }
