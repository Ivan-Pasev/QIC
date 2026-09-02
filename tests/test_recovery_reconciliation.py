from __future__ import annotations

from qic.core import (
    DurableArtifactView,
    JournalPhase,
    JournalRecord,
    ReconciliationClass,
    reconcile_recovery,
)


def prepared() -> JournalRecord:
    return JournalRecord(
        transaction_id="tx-r",
        sequence=0,
        phase=JournalPhase.PREPARED,
        proposal_digest="proposal",
        actor="operator",
        grant_digest="grant",
        before_state_digest="before",
    )


def chain() -> tuple[JournalRecord, ...]:
    p0 = prepared()
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


def test_reconciliation_progression_requires_exact_durable_evidence() -> None:
    p0, p1, p2, p3, p4, p5 = chain()

    assert reconcile_recovery(
        (p0,), DurableArtifactView(state_digest="before")
    ).classification is ReconciliationClass.RESUME_VALIDATION

    assert reconcile_recovery(
        (p0, p1), DurableArtifactView(state_digest="before")
    ).classification is ReconciliationClass.RESUME_STATE_COMMIT

    assert reconcile_recovery(
        (p0, p1, p2),
        DurableArtifactView(state_digest="after", outcome_digest="outcome"),
    ).classification is ReconciliationClass.RESUME_CHRONO_COMMIT

    assert reconcile_recovery(
        (p0, p1, p2, p3),
        DurableArtifactView(
            state_digest="after",
            outcome_digest="outcome",
            chrono_event_digest="chrono",
        ),
    ).classification is ReconciliationClass.RESUME_WITNESS_COMMIT

    assert reconcile_recovery(
        (p0, p1, p2, p3, p4),
        DurableArtifactView(
            state_digest="after",
            outcome_digest="outcome",
            chrono_event_digest="chrono",
            witness_digest="witness",
        ),
    ).classification is ReconciliationClass.FINALIZE_COMPLETE

    assert reconcile_recovery(
        (p0, p1, p2, p3, p4, p5),
        DurableArtifactView(
            state_digest="after",
            outcome_digest="outcome",
            chrono_event_digest="chrono",
            witness_digest="witness",
        ),
    ).classification is ReconciliationClass.COMPLETE


def test_artifact_ahead_of_journal_is_quarantined_not_inferred_forward() -> None:
    p0, p1, p2, p3, *_ = chain()

    ahead_state = reconcile_recovery(
        (p0, p1),
        DurableArtifactView(state_digest="after", outcome_digest="outcome"),
    )
    assert ahead_state.quarantined
    assert "advanced or diverged" in (ahead_state.reason or "")

    ahead_chrono = reconcile_recovery(
        (p0, p1, p2),
        DurableArtifactView(
            state_digest="after",
            outcome_digest="outcome",
            chrono_event_digest="chrono",
        ),
    )
    assert ahead_chrono.quarantined
    assert "ahead" in (ahead_chrono.reason or "")

    ahead_witness = reconcile_recovery(
        (p0, p1, p2, p3),
        DurableArtifactView(
            state_digest="after",
            outcome_digest="outcome",
            chrono_event_digest="chrono",
            witness_digest="witness",
        ),
    )
    assert ahead_witness.quarantined
    assert "ahead" in (ahead_witness.reason or "")


def test_mismatched_committed_artifacts_are_quarantined() -> None:
    p0, p1, p2, p3, p4, _ = chain()

    assert reconcile_recovery(
        (p0, p1, p2),
        DurableArtifactView(state_digest="wrong", outcome_digest="outcome"),
    ).quarantined
    assert reconcile_recovery(
        (p0, p1, p2),
        DurableArtifactView(state_digest="after", outcome_digest="wrong"),
    ).quarantined
    assert reconcile_recovery(
        (p0, p1, p2, p3),
        DurableArtifactView(
            state_digest="after",
            outcome_digest="outcome",
            chrono_event_digest="wrong",
        ),
    ).quarantined
    assert reconcile_recovery(
        (p0, p1, p2, p3, p4),
        DurableArtifactView(
            state_digest="after",
            outcome_digest="outcome",
            chrono_event_digest="chrono",
            witness_digest="wrong",
        ),
    ).quarantined


def test_abort_requires_original_state_and_no_successor_artifacts() -> None:
    p0 = prepared()
    aborted = p0.successor(JournalPhase.ABORTED, reason="rejected")
    ok = reconcile_recovery((p0, aborted), DurableArtifactView(state_digest="before"))
    assert ok.classification is ReconciliationClass.ABORTED

    changed = reconcile_recovery((p0, aborted), DurableArtifactView(state_digest="after"))
    assert changed.quarantined


def test_quarantined_journal_never_becomes_resumable() -> None:
    p0 = prepared()
    quarantined = p0.successor(JournalPhase.QUARANTINED, reason="ambiguous")
    result = reconcile_recovery(
        (p0, quarantined), DurableArtifactView(state_digest="before")
    )
    assert result.classification is ReconciliationClass.QUARANTINE
    assert result.quarantined


def test_durable_artifact_view_rejects_empty_or_nul_digests() -> None:
    for value in ("", "bad\x00digest"):
        try:
            DurableArtifactView(state_digest=value)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid state digest was accepted")
