"""Pure transaction-journal model for QIC G9.

G9 begins with deterministic journal semantics before filesystem persistence.
A journal record describes durable intent/progress only; it does not grant
authority, execute a transition, or prove that an external storage device obeyed
flush/fsync semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .digest import digest_hex


class JournalPhase(str, Enum):
    PREPARED = "PREPARED"
    VALIDATED = "VALIDATED"
    STATE_COMMITTED = "STATE_COMMITTED"
    CHRONO_COMMITTED = "CHRONO_COMMITTED"
    WITNESS_COMMITTED = "WITNESS_COMMITTED"
    COMPLETE = "COMPLETE"
    ABORTED = "ABORTED"
    QUARANTINED = "QUARANTINED"


_ALLOWED_SUCCESSORS: dict[JournalPhase, frozenset[JournalPhase]] = {
    JournalPhase.PREPARED: frozenset(
        {JournalPhase.VALIDATED, JournalPhase.ABORTED, JournalPhase.QUARANTINED}
    ),
    JournalPhase.VALIDATED: frozenset(
        {JournalPhase.STATE_COMMITTED, JournalPhase.ABORTED, JournalPhase.QUARANTINED}
    ),
    JournalPhase.STATE_COMMITTED: frozenset(
        {JournalPhase.CHRONO_COMMITTED, JournalPhase.QUARANTINED}
    ),
    JournalPhase.CHRONO_COMMITTED: frozenset(
        {JournalPhase.WITNESS_COMMITTED, JournalPhase.QUARANTINED}
    ),
    JournalPhase.WITNESS_COMMITTED: frozenset(
        {JournalPhase.COMPLETE, JournalPhase.QUARANTINED}
    ),
    JournalPhase.COMPLETE: frozenset(),
    JournalPhase.ABORTED: frozenset(),
    JournalPhase.QUARANTINED: frozenset(),
}


def _required_text(value: object, *, name: str) -> str:
    if type(value) is not str or not value or "\x00" in value:
        raise ValueError(f"{name} must be a non-empty NUL-free string")
    return value


def _optional_text(value: object, *, name: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, name=name)


@dataclass(frozen=True, slots=True)
class JournalRecord:
    """One immutable transaction-journal phase record.

    `sequence` is local to one transaction and starts at zero. Successor records
    hash-link to the preceding record. Phase-specific references become required
    only after their corresponding persistence boundary has been crossed.
    """

    transaction_id: str
    sequence: int
    phase: JournalPhase
    proposal_digest: str
    actor: str
    grant_digest: str
    before_state_digest: str
    after_state_digest: str | None = None
    outcome_digest: str | None = None
    chrono_event_digest: str | None = None
    witness_digest: str | None = None
    previous_record_digest: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        _required_text(self.transaction_id, name="transaction_id")
        if type(self.sequence) is not int or self.sequence < 0:
            raise ValueError("sequence must be a non-negative int")
        if type(self.phase) is not JournalPhase:
            raise TypeError("phase must be JournalPhase")
        for name, value in (
            ("proposal_digest", self.proposal_digest),
            ("actor", self.actor),
            ("grant_digest", self.grant_digest),
            ("before_state_digest", self.before_state_digest),
        ):
            _required_text(value, name=name)
        for name, value in (
            ("after_state_digest", self.after_state_digest),
            ("outcome_digest", self.outcome_digest),
            ("chrono_event_digest", self.chrono_event_digest),
            ("witness_digest", self.witness_digest),
            ("previous_record_digest", self.previous_record_digest),
            ("reason", self.reason),
        ):
            _optional_text(value, name=name)

        if self.sequence == 0 and self.previous_record_digest is not None:
            raise ValueError("initial journal record cannot reference a predecessor")
        if self.sequence > 0 and self.previous_record_digest is None:
            raise ValueError("non-initial journal record requires previous_record_digest")
        if self.sequence == 0 and self.phase is not JournalPhase.PREPARED:
            raise ValueError("initial journal record must be PREPARED")

        reached_state = self.phase in {
            JournalPhase.STATE_COMMITTED,
            JournalPhase.CHRONO_COMMITTED,
            JournalPhase.WITNESS_COMMITTED,
            JournalPhase.COMPLETE,
        }
        reached_chrono = self.phase in {
            JournalPhase.CHRONO_COMMITTED,
            JournalPhase.WITNESS_COMMITTED,
            JournalPhase.COMPLETE,
        }
        reached_witness = self.phase in {
            JournalPhase.WITNESS_COMMITTED,
            JournalPhase.COMPLETE,
        }
        if reached_state and (
            self.after_state_digest is None or self.outcome_digest is None
        ):
            raise ValueError("state-committed phases require after_state_digest and outcome_digest")
        if reached_chrono and self.chrono_event_digest is None:
            raise ValueError("chrono-committed phases require chrono_event_digest")
        if reached_witness and self.witness_digest is None:
            raise ValueError("witness-committed phases require witness_digest")
        if self.phase in {JournalPhase.ABORTED, JournalPhase.QUARANTINED} and self.reason is None:
            raise ValueError("ABORTED/QUARANTINED records require a reason")

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="journal.record")

    @property
    def terminal(self) -> bool:
        return not _ALLOWED_SUCCESSORS[self.phase]

    def may_advance_to(self, phase: JournalPhase) -> bool:
        if type(phase) is not JournalPhase:
            raise TypeError("phase must be JournalPhase")
        return phase in _ALLOWED_SUCCESSORS[self.phase]

    def successor(self, phase: JournalPhase, **changes: object) -> "JournalRecord":
        """Return a hash-linked legal successor; never mutate the current record."""

        if not self.may_advance_to(phase):
            raise ValueError(f"illegal journal phase transition: {self.phase.value}->{phase.value}")
        protected = {"transaction_id", "sequence", "phase", "previous_record_digest"}
        if protected & changes.keys():
            raise ValueError("successor identity/link fields are managed by the journal model")
        return replace(
            self,
            sequence=self.sequence + 1,
            phase=phase,
            previous_record_digest=self.digest,
            **changes,
        )


def journal_phase_successors(phase: JournalPhase) -> frozenset[JournalPhase]:
    if type(phase) is not JournalPhase:
        raise TypeError("phase must be JournalPhase")
    return _ALLOWED_SUCCESSORS[phase]
