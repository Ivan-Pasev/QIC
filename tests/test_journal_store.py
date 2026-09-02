from __future__ import annotations

import json
from pathlib import Path

import pytest

from qic.core import (
    JournalConflictError,
    JournalCorruptionError,
    JournalFailpoint,
    JournalFileStore,
    JournalPhase,
    JournalRecord,
    RecoveryClass,
    assess_recovery,
)


def prepared(transaction_id: str = "tx-1", *, proposal_digest: str = "proposal") -> JournalRecord:
    return JournalRecord(
        transaction_id=transaction_id,
        sequence=0,
        phase=JournalPhase.PREPARED,
        proposal_digest=proposal_digest,
        actor="operator",
        grant_digest="grant",
        before_state_digest="before",
    )


def full_chain(transaction_id: str = "tx-1") -> tuple[JournalRecord, ...]:
    p0 = prepared(transaction_id)
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
    return (p0, p1, p2, p3, p4, p5)


def test_durable_append_roundtrip_and_idempotent_same_record(tmp_path: Path) -> None:
    store = JournalFileStore(tmp_path / "journal")
    chain = full_chain()
    for record in chain:
        path = store.append(record)
        assert path.exists()
    assert store.load("tx-1") == chain
    assert store.append(chain[-1]) == tmp_path / "journal" / "tx-1" / "00000005.json"


def test_conflicting_duplicate_or_skipped_sequence_is_rejected(tmp_path: Path) -> None:
    store = JournalFileStore(tmp_path / "journal")
    p0, p1, *_ = full_chain()
    store.append(p0)
    with pytest.raises(JournalConflictError):
        store.append(prepared(proposal_digest="different"))
    skipped = JournalRecord(
        transaction_id="tx-1",
        sequence=2,
        phase=JournalPhase.VALIDATED,
        proposal_digest=p1.proposal_digest,
        actor=p1.actor,
        grant_digest=p1.grant_digest,
        before_state_digest=p1.before_state_digest,
        previous_record_digest=p0.digest,
    )
    with pytest.raises(JournalConflictError):
        store.append(skipped)


def test_path_traversal_transaction_id_is_rejected(tmp_path: Path) -> None:
    store = JournalFileStore(tmp_path / "journal")
    record = prepared("../escape")
    with pytest.raises(ValueError):
        store.append(record)


def test_persisted_record_tamper_is_detected(tmp_path: Path) -> None:
    store = JournalFileStore(tmp_path / "journal")
    record = prepared()
    path = store.append(record)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["actor"] = "attacker"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(JournalCorruptionError, match="digest mismatch"):
        store.load("tx-1")


def test_missing_middle_record_is_detected(tmp_path: Path) -> None:
    store = JournalFileStore(tmp_path / "journal")
    chain = full_chain()
    for record in chain[:3]:
        store.append(record)
    (tmp_path / "journal" / "tx-1" / "00000001.json").unlink()
    with pytest.raises(JournalCorruptionError, match="sequence gap"):
        store.load("tx-1")


def test_fail_before_promote_leaves_no_committed_record(tmp_path: Path) -> None:
    def fail(point: JournalFailpoint, path: Path) -> None:
        if point is JournalFailpoint.AFTER_FILE_FSYNC:
            raise RuntimeError("crash")

    store = JournalFileStore(tmp_path / "journal", failpoint=fail)
    with pytest.raises(RuntimeError, match="crash"):
        store.append(prepared())
    assert JournalFileStore(tmp_path / "journal").load("tx-1") == ()


def test_fail_after_promote_leaves_valid_record_for_recovery(tmp_path: Path) -> None:
    def fail(point: JournalFailpoint, path: Path) -> None:
        if point is JournalFailpoint.AFTER_PROMOTE:
            raise RuntimeError("crash")

    root = tmp_path / "journal"
    store = JournalFileStore(root, failpoint=fail)
    record = prepared()
    with pytest.raises(RuntimeError, match="crash"):
        store.append(record)
    assert JournalFileStore(root).load("tx-1") == (record,)


def test_concurrent_conflicting_promotion_never_overwrites_winner(tmp_path: Path) -> None:
    desired = prepared(proposal_digest="desired")
    competing = prepared(proposal_digest="competing")

    staging = JournalFileStore(tmp_path / "staging")
    competing_bytes = staging.append(competing).read_bytes()

    def inject_winner(point: JournalFailpoint, temporary: Path) -> None:
        if point is JournalFailpoint.AFTER_FILE_FSYNC:
            target = temporary.with_suffix("")
            target.write_bytes(competing_bytes)

    root = tmp_path / "journal"
    store = JournalFileStore(root, failpoint=inject_winner)
    with pytest.raises(JournalConflictError, match="concurrent journal promotion"):
        store.append(desired)

    assert JournalFileStore(root).load("tx-1") == (competing,)


def test_recovery_classifier_is_phase_specific_and_nonexecuting() -> None:
    chain = full_chain()
    expected = {
        JournalPhase.PREPARED: RecoveryClass.RESUME_VALIDATION,
        JournalPhase.VALIDATED: RecoveryClass.RESUME_STATE_COMMIT,
        JournalPhase.STATE_COMMITTED: RecoveryClass.REQUIRE_CHRONO_EVIDENCE,
        JournalPhase.CHRONO_COMMITTED: RecoveryClass.REQUIRE_WITNESS_EVIDENCE,
        JournalPhase.WITNESS_COMMITTED: RecoveryClass.FINALIZE_COMPLETE,
        JournalPhase.COMPLETE: RecoveryClass.COMPLETE,
    }
    for index, record in enumerate(chain):
        assessment = assess_recovery(chain[: index + 1])
        assert assessment.last_phase is record.phase
        assert assessment.classification is expected[record.phase]
        assert assessment.last_record_digest == record.digest


def test_abort_and_quarantine_are_terminal_recovery_classes() -> None:
    p0 = prepared()
    aborted = p0.successor(JournalPhase.ABORTED, reason="validation rejected")
    quarantined = p0.successor(JournalPhase.QUARANTINED, reason="corrupt dependency")
    assert assess_recovery((p0, aborted)).classification is RecoveryClass.ABORTED
    assert assess_recovery((p0, quarantined)).classification is RecoveryClass.QUARANTINED


def test_scan_contains_corrupt_transaction_without_hiding_valid_one(tmp_path: Path) -> None:
    store = JournalFileStore(tmp_path / "journal")
    store.append(prepared("good"))
    bad_path = store.append(prepared("bad"))
    payload = json.loads(bad_path.read_text(encoding="utf-8"))
    payload["record_digest"] = "forged"
    bad_path.write_text(json.dumps(payload), encoding="utf-8")

    scanned = store.scan()
    assert scanned["good"] == (prepared("good"),)
    assert isinstance(scanned["bad"], JournalCorruptionError)
