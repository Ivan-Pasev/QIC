"""Conservative durable-artifact reconciliation for QIC G9.

The journal is an intent/progress record. Authoritative state, transition
outcome, Chrono event, and witness artifacts are loaded separately and exposed
here only by their verified digests. Reconciliation never creates or rewrites
those artifacts. If durable evidence is ahead of the journal or disagrees with
it, the reference policy quarantines the transaction rather than guessing.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .journal import JournalPhase, JournalRecord
from .journal_store import JournalCorruptionError, RecoveryAssessment, RecoveryClass, assess_recovery


class ReconciliationClass(str, Enum):
    RESUME_VALIDATION = "RESUME_VALIDATION"
    RESUME_STATE_COMMIT = "RESUME_STATE_COMMIT"
    RESUME_CHRONO_COMMIT = "RESUME_CHRONO_COMMIT"
    RESUME_WITNESS_COMMIT = "RESUME_WITNESS_COMMIT"
    FINALIZE_COMPLETE = "FINALIZE_COMPLETE"
    COMPLETE = "COMPLETE"
    ABORTED = "ABORTED"
    QUARANTINE = "QUARANTINE"


@dataclass(frozen=True, slots=True)
class DurableArtifactView:
    """Verified digest view of separately loaded durable artifacts.

    `state_digest` represents the durable authoritative state root currently on
    disk. The other fields are optional because the corresponding durable
    artifacts may not yet exist at a crash boundary.
    """

    state_digest: str
    outcome_digest: str | None = None
    chrono_event_digest: str | None = None
    witness_digest: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("state_digest", self.state_digest),
            ("outcome_digest", self.outcome_digest),
            ("chrono_event_digest", self.chrono_event_digest),
            ("witness_digest", self.witness_digest),
        ):
            if value is None and name != "state_digest":
                continue
            if type(value) is not str or not value or "\x00" in value:
                raise ValueError(f"{name} must be a non-empty NUL-free string when present")


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    transaction_id: str
    classification: ReconciliationClass
    journal_phase: JournalPhase
    journal_head_digest: str
    reason: str | None = None

    @property
    def quarantined(self) -> bool:
        return self.classification is ReconciliationClass.QUARANTINE


def _quarantine(head: JournalRecord, reason: str) -> ReconciliationResult:
    return ReconciliationResult(
        transaction_id=head.transaction_id,
        classification=ReconciliationClass.QUARANTINE,
        journal_phase=head.phase,
        journal_head_digest=head.digest,
        reason=reason,
    )


def reconcile_recovery(
    records: tuple[JournalRecord, ...],
    artifacts: DurableArtifactView,
) -> ReconciliationResult:
    """Compare verified durable artifact digests with a verified journal chain.

    The reference policy accepts only artifact sets already justified by the
    journal phase. Evidence that appears to be ahead of the journal is not used
    to infer an unrecorded commit; it is quarantined for higher-level review.
    """

    if not isinstance(artifacts, DurableArtifactView):
        raise TypeError("artifacts must be DurableArtifactView")
    assessment: RecoveryAssessment = assess_recovery(records)
    head = records[-1]

    if head.phase is JournalPhase.QUARANTINED:
        return _quarantine(head, head.reason or "journal already quarantined")

    if head.phase in {JournalPhase.PREPARED, JournalPhase.VALIDATED, JournalPhase.ABORTED}:
        if artifacts.state_digest != head.before_state_digest:
            return _quarantine(head, "durable state advanced or diverged before journal state commit")
        if any(
            value is not None
            for value in (
                artifacts.outcome_digest,
                artifacts.chrono_event_digest,
                artifacts.witness_digest,
            )
        ):
            return _quarantine(head, "durable successor artifact exists ahead of journal phase")
        mapping = {
            JournalPhase.PREPARED: ReconciliationClass.RESUME_VALIDATION,
            JournalPhase.VALIDATED: ReconciliationClass.RESUME_STATE_COMMIT,
            JournalPhase.ABORTED: ReconciliationClass.ABORTED,
        }
        return ReconciliationResult(
            transaction_id=head.transaction_id,
            classification=mapping[head.phase],
            journal_phase=head.phase,
            journal_head_digest=head.digest,
        )

    if artifacts.state_digest != head.after_state_digest:
        return _quarantine(head, "durable state digest does not match journal after_state_digest")
    if artifacts.outcome_digest != head.outcome_digest:
        return _quarantine(head, "durable outcome digest does not match journal outcome_digest")

    if head.phase is JournalPhase.STATE_COMMITTED:
        if artifacts.chrono_event_digest is not None or artifacts.witness_digest is not None:
            return _quarantine(head, "Chrono/witness artifact exists ahead of journal phase")
        return ReconciliationResult(
            transaction_id=head.transaction_id,
            classification=ReconciliationClass.RESUME_CHRONO_COMMIT,
            journal_phase=head.phase,
            journal_head_digest=head.digest,
        )

    if artifacts.chrono_event_digest != head.chrono_event_digest:
        return _quarantine(head, "durable Chrono digest does not match journal chrono_event_digest")

    if head.phase is JournalPhase.CHRONO_COMMITTED:
        if artifacts.witness_digest is not None:
            return _quarantine(head, "witness artifact exists ahead of journal phase")
        return ReconciliationResult(
            transaction_id=head.transaction_id,
            classification=ReconciliationClass.RESUME_WITNESS_COMMIT,
            journal_phase=head.phase,
            journal_head_digest=head.digest,
        )

    if artifacts.witness_digest != head.witness_digest:
        return _quarantine(head, "durable witness digest does not match journal witness_digest")

    if head.phase is JournalPhase.WITNESS_COMMITTED:
        classification = ReconciliationClass.FINALIZE_COMPLETE
    elif head.phase is JournalPhase.COMPLETE:
        classification = ReconciliationClass.COMPLETE
    else:  # guarded by journal model; retained fail-closed for future enum expansion.
        raise JournalCorruptionError(f"unsupported journal phase during reconciliation: {head.phase}")

    return ReconciliationResult(
        transaction_id=head.transaction_id,
        classification=classification,
        journal_phase=head.phase,
        journal_head_digest=head.digest,
    )
