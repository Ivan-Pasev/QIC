from __future__ import annotations

import pytest

from qic.workload_atlas import WORKLOAD_ATLAS, atlas_by_id, resolve_kernel, verify_atlas


def test_workload_atlas_ids_are_unique_and_live() -> None:
    verification = verify_atlas()
    assert verification["pass"] is True, verification["failures"]
    assert len(verification["resolved"]) == len(WORKLOAD_ATLAS)
    assert len(atlas_by_id()) == len(WORKLOAD_ATLAS)


def test_every_atlas_kernel_resolves_to_callable() -> None:
    for entry in WORKLOAD_ATLAS:
        assert callable(resolve_kernel(entry.kernel)), entry.kernel
        assert "Performance measurement only" in entry.claim_boundary
        assert entry.workload.assurance_profile == "FULL_DECLARED_PATH"


def test_resolver_fails_closed_on_missing_kernel() -> None:
    with pytest.raises((AttributeError, ImportError, ModuleNotFoundError)):
        resolve_kernel("qic.core.digest.not_a_real_kernel")


def test_atlas_contains_current_g0_g9_surfaces_only() -> None:
    ids = set(atlas_by_id())
    assert {
        "canonical.bytes",
        "canonical.digest",
        "transition.execute",
        "chrono.verify",
        "kbi.supporting_evidence",
        "journal.scan",
        "recovery.reconcile",
        "qualification.verify",
        "aggregate.verify",
    } == ids
    assert all("holo" not in item for item in ids)
    assert all("topo" not in item for item in ids)
    assert all("federation" not in item for item in ids)
