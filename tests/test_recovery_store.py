from __future__ import annotations

import json
from pathlib import Path

import pytest

import qic.core.recovery_store as recovery_store_module
from qic.core import (
    JournalConflictError,
    JournalCorruptionError,
    JournalPhase,
    JournalRecord,
    ReconciliationClass,
    RecoveryEvidenceBundle,
    RecoveryEvidenceStore,
    reconcile_evidence_bundle,
)


def journal_chain() -> tuple[JournalRecord, ...]:
    p0 = JournalRecord(
        transaction_id="tx-bundle",
        sequence=0,
        phase=JournalPhase.PREPARED,
        proposal_digest="proposal",
        actor="operator",
        grant_digest="grant",
        before_state_digest="before",
    )
    p1 = p0.successor(JournalPhase.VALIDATED)
    p2 = p1.successor(
        JournalPhase.STATE_COMMITTED,
        after_state_digest="after",
        outcome_digest="outcome",
    )
    p3 = p2.successor(
        JournalPhase.CHRONO_COMMITTED,
        chrono_event_digest="chrono",
    )
    p4 = p3.successor(
        JournalPhase.WITNESS_COMMITTED,
        witness_digest="witness",
    )
    p5 = p4.successor(JournalPhase.COMPLETE)
    return p0, p1, p2, p3, p4, p5


def bundle_for(record: JournalRecord, *, state_digest: str | None = None) -> RecoveryEvidenceBundle:
    if record.phase in {JournalPhase.PREPARED, JournalPhase.VALIDATED}:
        state = record.before_state_digest
    else:
        state = record.after_state_digest or "missing"
    if state_digest is not None:
        state = state_digest
    return RecoveryEvidenceBundle(
        transaction_id=record.transaction_id,
        journal_sequence=record.sequence,
        journal_head_digest=record.digest,
        state_digest=state,
        outcome_digest=record.outcome_digest,
        chrono_event_digest=record.chrono_event_digest,
        witness_digest=record.witness_digest,
    )


def test_bundle_store_roundtrip_and_exact_retry_idempotence(tmp_path: Path) -> None:
    store = RecoveryEvidenceStore(tmp_path / "evidence")
    record = journal_chain()[2]
    bundle = bundle_for(record)
    first = store.put(bundle)
    second = store.put(bundle)
    assert first == second
    assert store.load(bundle.transaction_id, bundle.journal_sequence) == bundle


def test_conflicting_bundle_for_same_journal_sequence_is_rejected(tmp_path: Path) -> None:
    store = RecoveryEvidenceStore(tmp_path / "evidence")
    record = journal_chain()[2]
    bundle = bundle_for(record)
    store.put(bundle)
    conflict = bundle_for(record, state_digest="different-state")
    with pytest.raises(JournalConflictError):
        store.put(conflict)


def test_concurrent_conflicting_bundle_promotion_never_overwrites_winner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = journal_chain()[2]
    desired = bundle_for(record, state_digest="desired-state")
    competing = bundle_for(record, state_digest="competing-state")

    staging = RecoveryEvidenceStore(tmp_path / "staging")
    competing_bytes = staging.put(competing).read_bytes()
    original_promote = recovery_store_module._promote_no_replace

    def inject_winner(temporary: Path, target: Path) -> None:
        target.write_bytes(competing_bytes)
        original_promote(temporary, target)

    monkeypatch.setattr(recovery_store_module, "_promote_no_replace", inject_winner)
    root = tmp_path / "evidence"
    store = RecoveryEvidenceStore(root)
    with pytest.raises(JournalConflictError, match="concurrent recovery evidence promotion"):
        store.put(desired)

    assert RecoveryEvidenceStore(root).load("tx-bundle", 2) == competing


def test_bundle_tamper_is_detected(tmp_path: Path) -> None:
    store = RecoveryEvidenceStore(tmp_path / "evidence")
    bundle = bundle_for(journal_chain()[3])
    path = store.put(bundle)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["chrono_event_digest"] = "forged"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(JournalCorruptionError, match="digest mismatch"):
        store.load(bundle.transaction_id, bundle.journal_sequence)


def test_bundle_must_bind_exact_journal_head_before_reconciliation() -> None:
    records = journal_chain()
    p2 = records[2]
    good = bundle_for(p2)
    assert reconcile_evidence_bundle(
        records[:3], good
    ).classification is ReconciliationClass.RESUME_CHRONO_COMMIT

    wrong_head = RecoveryEvidenceBundle(
        transaction_id=good.transaction_id,
        journal_sequence=good.journal_sequence,
        journal_head_digest="wrong-head",
        state_digest=good.state_digest,
        outcome_digest=good.outcome_digest,
    )
    with pytest.raises(JournalCorruptionError, match="head digest"):
        reconcile_evidence_bundle(records[:3], wrong_head)

    wrong_sequence = RecoveryEvidenceBundle(
        transaction_id=good.transaction_id,
        journal_sequence=1,
        journal_head_digest=records[1].digest,
        state_digest="before",
    )
    with pytest.raises(JournalCorruptionError, match="sequence"):
        reconcile_evidence_bundle(records[:3], wrong_sequence)


def test_restart_reconciliation_is_pure_and_idempotent(tmp_path: Path) -> None:
    records = journal_chain()
    p3 = records[3]
    store = RecoveryEvidenceStore(tmp_path / "evidence")
    store.put(bundle_for(p3))

    reloaded_a = RecoveryEvidenceStore(tmp_path / "evidence").load("tx-bundle", 3)
    reloaded_b = RecoveryEvidenceStore(tmp_path / "evidence").load("tx-bundle", 3)
    first = reconcile_evidence_bundle(records[:4], reloaded_a)
    second = reconcile_evidence_bundle(records[:4], reloaded_b)
    assert first == second
    assert first.classification is ReconciliationClass.RESUME_WITNESS_COMMIT
    assert store.bundles("tx-bundle") == (bundle_for(p3),)


def test_bundle_store_rejects_path_traversal(tmp_path: Path) -> None:
    store = RecoveryEvidenceStore(tmp_path / "evidence")
    bundle = RecoveryEvidenceBundle(
        transaction_id="../escape",
        journal_sequence=0,
        journal_head_digest="head",
        state_digest="before",
    )
    with pytest.raises(ValueError):
        store.put(bundle)
