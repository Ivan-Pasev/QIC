from __future__ import annotations

from pathlib import Path

from qic.core import (
    JournalFileStore,
    JournalPhase,
    JournalRecord,
    ReconciliationClass,
    RecoveryEvidenceBundle,
    RecoveryEvidenceStore,
    reconcile_evidence_bundle,
)


def records() -> tuple[JournalRecord, ...]:
    p0 = JournalRecord(
        transaction_id="tx-crash",
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


def evidence_for(record: JournalRecord) -> RecoveryEvidenceBundle:
    if record.phase in {JournalPhase.PREPARED, JournalPhase.VALIDATED}:
        state = record.before_state_digest
    else:
        state = record.after_state_digest or "missing"
    return RecoveryEvidenceBundle(
        transaction_id=record.transaction_id,
        journal_sequence=record.sequence,
        journal_head_digest=record.digest,
        state_digest=state,
        outcome_digest=record.outcome_digest,
        chrono_event_digest=record.chrono_event_digest,
        witness_digest=record.witness_digest,
    )


def persist_prefix(root: Path, count: int) -> tuple[JournalRecord, ...]:
    journal = JournalFileStore(root / "journal")
    chain = records()[:count]
    for record in chain:
        journal.append(record)
    return JournalFileStore(root / "journal").load("tx-crash")


def test_restart_campaign_resumes_only_next_missing_boundary(tmp_path: Path) -> None:
    expected = {
        1: ReconciliationClass.RESUME_VALIDATION,
        2: ReconciliationClass.RESUME_STATE_COMMIT,
        3: ReconciliationClass.RESUME_CHRONO_COMMIT,
        4: ReconciliationClass.RESUME_WITNESS_COMMIT,
        5: ReconciliationClass.FINALIZE_COMPLETE,
        6: ReconciliationClass.COMPLETE,
    }
    for count, classification in expected.items():
        root = tmp_path / f"phase-{count}"
        durable_records = persist_prefix(root, count)
        head = durable_records[-1]
        evidence_store = RecoveryEvidenceStore(root / "evidence")
        evidence_store.put(evidence_for(head))

        # Simulate a fresh process: reopen both stores and classify from bytes.
        restarted_records = JournalFileStore(root / "journal").load("tx-crash")
        restarted_bundle = RecoveryEvidenceStore(root / "evidence").load(
            "tx-crash", head.sequence
        )
        result = reconcile_evidence_bundle(restarted_records, restarted_bundle)
        assert result.classification is classification

        # Repeating restart/reconciliation must not advance or duplicate durable data.
        result_again = reconcile_evidence_bundle(
            JournalFileStore(root / "journal").load("tx-crash"),
            RecoveryEvidenceStore(root / "evidence").load("tx-crash", head.sequence),
        )
        assert result_again == result
        assert JournalFileStore(root / "journal").load("tx-crash") == durable_records


def test_crash_after_state_artifact_before_state_journal_is_quarantined(tmp_path: Path) -> None:
    p0, p1, p2, *_ = records()
    root = tmp_path / "state-ahead"
    journal = JournalFileStore(root / "journal")
    journal.append(p0)
    journal.append(p1)

    # Model durable state/outcome evidence surviving while the STATE_COMMITTED
    # journal record did not. It is intentionally rebound to current journal head
    # so the reconciler can evaluate the artifact relationship; it must still
    # quarantine because state/outcome are ahead of VALIDATED.
    bundle = RecoveryEvidenceBundle(
        transaction_id=p1.transaction_id,
        journal_sequence=p1.sequence,
        journal_head_digest=p1.digest,
        state_digest=p2.after_state_digest or "missing",
        outcome_digest=p2.outcome_digest,
    )
    RecoveryEvidenceStore(root / "evidence").put(bundle)
    result = reconcile_evidence_bundle(
        JournalFileStore(root / "journal").load("tx-crash"),
        RecoveryEvidenceStore(root / "evidence").load("tx-crash", p1.sequence),
    )
    assert result.classification is ReconciliationClass.QUARANTINE
    assert "advanced or diverged" in (result.reason or "")


def test_crash_after_chrono_artifact_before_chrono_journal_is_quarantined(tmp_path: Path) -> None:
    p0, p1, p2, p3, *_ = records()
    root = tmp_path / "chrono-ahead"
    journal = JournalFileStore(root / "journal")
    for record in (p0, p1, p2):
        journal.append(record)
    bundle = RecoveryEvidenceBundle(
        transaction_id=p2.transaction_id,
        journal_sequence=p2.sequence,
        journal_head_digest=p2.digest,
        state_digest=p2.after_state_digest or "missing",
        outcome_digest=p2.outcome_digest,
        chrono_event_digest=p3.chrono_event_digest,
    )
    RecoveryEvidenceStore(root / "evidence").put(bundle)
    result = reconcile_evidence_bundle(
        JournalFileStore(root / "journal").load("tx-crash"),
        RecoveryEvidenceStore(root / "evidence").load("tx-crash", p2.sequence),
    )
    assert result.classification is ReconciliationClass.QUARANTINE
    assert "ahead" in (result.reason or "")


def test_crash_after_witness_artifact_before_witness_journal_is_quarantined(tmp_path: Path) -> None:
    p0, p1, p2, p3, p4, *_ = records()
    root = tmp_path / "witness-ahead"
    journal = JournalFileStore(root / "journal")
    for record in (p0, p1, p2, p3):
        journal.append(record)
    bundle = RecoveryEvidenceBundle(
        transaction_id=p3.transaction_id,
        journal_sequence=p3.sequence,
        journal_head_digest=p3.digest,
        state_digest=p3.after_state_digest or "missing",
        outcome_digest=p3.outcome_digest,
        chrono_event_digest=p3.chrono_event_digest,
        witness_digest=p4.witness_digest,
    )
    RecoveryEvidenceStore(root / "evidence").put(bundle)
    result = reconcile_evidence_bundle(
        JournalFileStore(root / "journal").load("tx-crash"),
        RecoveryEvidenceStore(root / "evidence").load("tx-crash", p3.sequence),
    )
    assert result.classification is ReconciliationClass.QUARANTINE
    assert "ahead" in (result.reason or "")


def test_no_double_state_commit_after_state_committed_restart(tmp_path: Path) -> None:
    p0, p1, p2, *_ = records()
    root = tmp_path / "no-double-state"
    journal = JournalFileStore(root / "journal")
    for record in (p0, p1, p2):
        journal.append(record)
    RecoveryEvidenceStore(root / "evidence").put(evidence_for(p2))

    for _ in range(3):
        result = reconcile_evidence_bundle(
            JournalFileStore(root / "journal").load("tx-crash"),
            RecoveryEvidenceStore(root / "evidence").load("tx-crash", p2.sequence),
        )
        assert result.classification is ReconciliationClass.RESUME_CHRONO_COMMIT
        assert result.classification is not ReconciliationClass.RESUME_STATE_COMMIT


def test_no_synthesis_when_required_evidence_is_missing(tmp_path: Path) -> None:
    p0, p1, p2, p3, *_ = records()
    root = tmp_path / "missing-chrono"
    journal = JournalFileStore(root / "journal")
    for record in (p0, p1, p2, p3):
        journal.append(record)

    # A CHRONO_COMMITTED journal requires exact Chrono evidence. Missing evidence
    # must quarantine; reconciliation must not manufacture the expected digest.
    incomplete = RecoveryEvidenceBundle(
        transaction_id=p3.transaction_id,
        journal_sequence=p3.sequence,
        journal_head_digest=p3.digest,
        state_digest=p3.after_state_digest or "missing",
        outcome_digest=p3.outcome_digest,
        chrono_event_digest=None,
    )
    RecoveryEvidenceStore(root / "evidence").put(incomplete)
    result = reconcile_evidence_bundle(
        JournalFileStore(root / "journal").load("tx-crash"),
        RecoveryEvidenceStore(root / "evidence").load("tx-crash", p3.sequence),
    )
    assert result.classification is ReconciliationClass.QUARANTINE
    assert "Chrono digest" in (result.reason or "")
