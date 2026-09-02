"""Append-only local Chrono and witness kernel for QIC G5.

Chrono records deterministic local causal history over G4 transition outcomes.
Witness records bind to event and outcome/state digests. These structures prove
only declared structural composition and hash linkage; they do not create
authority, semantic truth, signatures, distributed consensus, or durable
crash-recovery guarantees.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .digest import digest_hex
from .transition import StateSnapshot, TransitionFailure, TransitionOutcome


class ChronoEventType(str, Enum):
    GENESIS = "GENESIS"
    TRANSITION = "TRANSITION"


class WitnessSubject(str, Enum):
    GENESIS_STATE = "GENESIS_STATE"
    TRANSITION_OUTCOME = "TRANSITION_OUTCOME"


@dataclass(frozen=True, slots=True)
class ChronoEvent:
    """One immutable event in a local hash-linked causal sequence."""

    sequence: int
    previous_event_digest: str | None
    event_type: ChronoEventType
    proposal_digest: str | None
    outcome_digest: str | None
    before_state_digest: str
    after_state_digest: str
    accepted: bool | None
    failure: TransitionFailure | None

    def __post_init__(self) -> None:
        if type(self.sequence) is not int or self.sequence < 0:
            raise ValueError("sequence must be a non-negative int")
        if self.previous_event_digest is not None and (
            type(self.previous_event_digest) is not str or not self.previous_event_digest
        ):
            raise ValueError("previous_event_digest must be a non-empty string or None")
        if type(self.event_type) is not ChronoEventType:
            raise TypeError("event_type must be ChronoEventType")
        for name, value in (
            ("before_state_digest", self.before_state_digest),
            ("after_state_digest", self.after_state_digest),
        ):
            if type(value) is not str or not value:
                raise ValueError(f"{name} must be a non-empty string")

        if self.event_type is ChronoEventType.GENESIS:
            if self.sequence != 0:
                raise ValueError("genesis event must have sequence 0")
            if self.previous_event_digest is not None:
                raise ValueError("genesis event cannot have a previous event")
            if self.proposal_digest is not None or self.outcome_digest is not None:
                raise ValueError("genesis event cannot bind a transition proposal/outcome")
            if self.accepted is not None or self.failure is not None:
                raise ValueError("genesis event cannot carry transition acceptance/failure")
            if self.before_state_digest != self.after_state_digest:
                raise ValueError("genesis event must preserve one genesis state digest")
            return

        if self.sequence == 0:
            raise ValueError("transition event cannot have sequence 0")
        if type(self.previous_event_digest) is not str or not self.previous_event_digest:
            raise ValueError("transition event requires previous_event_digest")
        if type(self.proposal_digest) is not str or not self.proposal_digest:
            raise ValueError("transition event requires proposal_digest")
        if type(self.outcome_digest) is not str or not self.outcome_digest:
            raise ValueError("transition event requires outcome_digest")
        if type(self.accepted) is not bool:
            raise TypeError("transition event accepted must be bool")
        if self.failure is not None and type(self.failure) is not TransitionFailure:
            raise TypeError("failure must be TransitionFailure or None")
        if self.accepted:
            if self.failure is not None:
                raise ValueError("accepted transition event cannot carry failure")
        else:
            if self.failure is None:
                raise ValueError("rejected transition event must carry failure")
            if self.before_state_digest != self.after_state_digest:
                raise ValueError("rejected transition event cannot change state digest")

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="chrono.event")


@dataclass(frozen=True, slots=True)
class WitnessRecord:
    """Unsigned local structural witness bound to one Chrono event."""

    sequence: int
    previous_witness_digest: str | None
    event_digest: str
    subject: WitnessSubject
    subject_digest: str

    def __post_init__(self) -> None:
        if type(self.sequence) is not int or self.sequence < 0:
            raise ValueError("sequence must be a non-negative int")
        if self.previous_witness_digest is not None and (
            type(self.previous_witness_digest) is not str or not self.previous_witness_digest
        ):
            raise ValueError("previous_witness_digest must be non-empty or None")
        if type(self.event_digest) is not str or not self.event_digest:
            raise ValueError("event_digest must be a non-empty string")
        if type(self.subject) is not WitnessSubject:
            raise TypeError("subject must be WitnessSubject")
        if type(self.subject_digest) is not str or not self.subject_digest:
            raise ValueError("subject_digest must be a non-empty string")
        if self.sequence == 0 and self.previous_witness_digest is not None:
            raise ValueError("genesis witness cannot have a previous witness")
        if self.sequence > 0 and (
            type(self.previous_witness_digest) is not str or not self.previous_witness_digest
        ):
            raise ValueError("non-genesis witness requires previous_witness_digest")

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="chrono.witness")


@dataclass(frozen=True, slots=True)
class ChronoChain:
    """Immutable append-only reference chain.

    Appending returns a new chain. Existing events/witnesses are never rewritten.
    This is an in-memory reference structure, not yet a durable crash-safe journal.
    A valid prefix is itself a valid chain; suffix truncation is detectable only
    when verification is supplied an independently retained expected head/length.
    """

    events: tuple[ChronoEvent, ...]
    witnesses: tuple[WitnessRecord, ...]

    def __post_init__(self) -> None:
        if type(self.events) is not tuple or type(self.witnesses) is not tuple:
            raise TypeError("events and witnesses must be tuples")
        if not self.events or not self.witnesses:
            raise ValueError("ChronoChain requires genesis event and witness")
        if not all(type(event) is ChronoEvent for event in self.events):
            raise TypeError("events must contain ChronoEvent values exactly")
        if not all(type(witness) is WitnessRecord for witness in self.witnesses):
            raise TypeError("witnesses must contain WitnessRecord values exactly")

    @classmethod
    def genesis(cls, state: StateSnapshot) -> "ChronoChain":
        if type(state) is not StateSnapshot:
            raise TypeError("state must be StateSnapshot exactly")
        event = ChronoEvent(
            sequence=0,
            previous_event_digest=None,
            event_type=ChronoEventType.GENESIS,
            proposal_digest=None,
            outcome_digest=None,
            before_state_digest=state.digest,
            after_state_digest=state.digest,
            accepted=None,
            failure=None,
        )
        witness = WitnessRecord(
            sequence=0,
            previous_witness_digest=None,
            event_digest=event.digest,
            subject=WitnessSubject.GENESIS_STATE,
            subject_digest=state.digest,
        )
        return cls(events=(event,), witnesses=(witness,))

    @property
    def head_event(self) -> ChronoEvent:
        return self.events[-1]

    @property
    def head_witness(self) -> WitnessRecord:
        return self.witnesses[-1]

    @property
    def current_state_digest(self) -> str:
        return self.head_event.after_state_digest

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="chrono.chain")

    def append_outcome(self, outcome: TransitionOutcome) -> "ChronoChain":
        """Append one exact G4 outcome or fail closed on causal mismatch."""

        if type(outcome) is not TransitionOutcome:
            raise TypeError("outcome must be TransitionOutcome exactly")
        valid, reason = self.verify()
        if not valid:
            raise ValueError(f"cannot append to invalid Chrono chain: {reason}")
        if outcome.before_digest != self.current_state_digest:
            raise ValueError("transition outcome does not begin at current Chrono state")
        sequence = len(self.events)
        event = ChronoEvent(
            sequence=sequence,
            previous_event_digest=self.head_event.digest,
            event_type=ChronoEventType.TRANSITION,
            proposal_digest=outcome.proposal_digest,
            outcome_digest=outcome.digest,
            before_state_digest=outcome.before_digest,
            after_state_digest=outcome.after_digest,
            accepted=outcome.accepted,
            failure=outcome.failure,
        )
        witness = WitnessRecord(
            sequence=sequence,
            previous_witness_digest=self.head_witness.digest,
            event_digest=event.digest,
            subject=WitnessSubject.TRANSITION_OUTCOME,
            subject_digest=outcome.digest,
        )
        candidate = ChronoChain(
            events=(*self.events, event),
            witnesses=(*self.witnesses, witness),
        )
        valid, reason = candidate.verify()
        if not valid:
            raise ValueError(f"candidate Chrono chain failed verification: {reason}")
        return candidate

    def verify(
        self,
        *,
        expected_length: int | None = None,
        expected_head_event_digest: str | None = None,
        expected_head_witness_digest: str | None = None,
    ) -> tuple[bool, str | None]:
        """Verify internal linkage and, optionally, an independently retained head.

        Internal hash linkage cannot distinguish a complete chain from a valid
        truncated prefix. `expected_length` and/or expected head digests provide
        the external anchor needed to detect suffix truncation.
        """

        if expected_length is not None:
            if type(expected_length) is not int or expected_length < 1:
                raise ValueError("expected_length must be a positive int or None")
            if len(self.events) != expected_length or len(self.witnesses) != expected_length:
                return False, "CHAIN_LENGTH_MISMATCH"
        for name, value in (
            ("expected_head_event_digest", expected_head_event_digest),
            ("expected_head_witness_digest", expected_head_witness_digest),
        ):
            if value is not None and (type(value) is not str or not value):
                raise ValueError(f"{name} must be a non-empty string or None")

        if len(self.events) != len(self.witnesses):
            return False, "EVENT_WITNESS_LENGTH_MISMATCH"
        if expected_head_event_digest is not None and self.head_event.digest != expected_head_event_digest:
            return False, "HEAD_EVENT_DIGEST_MISMATCH"
        if expected_head_witness_digest is not None and self.head_witness.digest != expected_head_witness_digest:
            return False, "HEAD_WITNESS_DIGEST_MISMATCH"

        for index, (event, witness) in enumerate(zip(self.events, self.witnesses)):
            if event.sequence != index or witness.sequence != index:
                return False, "SEQUENCE_MISMATCH"
            if index == 0:
                if event.event_type is not ChronoEventType.GENESIS:
                    return False, "GENESIS_EVENT_REQUIRED"
                if witness.subject is not WitnessSubject.GENESIS_STATE:
                    return False, "GENESIS_WITNESS_REQUIRED"
                if event.previous_event_digest is not None:
                    return False, "GENESIS_EVENT_PREVIOUS_DIGEST"
                if witness.previous_witness_digest is not None:
                    return False, "GENESIS_WITNESS_PREVIOUS_DIGEST"
                if witness.event_digest != event.digest:
                    return False, "WITNESS_EVENT_MISMATCH"
                if witness.subject_digest != event.after_state_digest:
                    return False, "GENESIS_WITNESS_STATE_MISMATCH"
                continue

            previous_event = self.events[index - 1]
            previous_witness = self.witnesses[index - 1]
            if event.event_type is not ChronoEventType.TRANSITION:
                return False, "NON_GENESIS_EVENT_TYPE"
            if event.previous_event_digest != previous_event.digest:
                return False, "PREVIOUS_EVENT_DIGEST_MISMATCH"
            if witness.previous_witness_digest != previous_witness.digest:
                return False, "PREVIOUS_WITNESS_DIGEST_MISMATCH"
            if event.before_state_digest != previous_event.after_state_digest:
                return False, "CAUSAL_STATE_MISMATCH"
            if witness.event_digest != event.digest:
                return False, "WITNESS_EVENT_MISMATCH"
            if witness.subject is not WitnessSubject.TRANSITION_OUTCOME:
                return False, "TRANSITION_WITNESS_SUBJECT_MISMATCH"
            if witness.subject_digest != event.outcome_digest:
                return False, "WITNESS_OUTCOME_MISMATCH"
            if event.accepted is False and event.before_state_digest != event.after_state_digest:
                return False, "REJECTED_EVENT_STATE_CHANGE"

        return True, None

    def verifies_outcome(self, sequence: int, outcome: TransitionOutcome) -> bool:
        """Check an external G4 outcome against its stored event/witness binding."""

        if type(sequence) is not int or sequence <= 0 or sequence >= len(self.events):
            return False
        if type(outcome) is not TransitionOutcome:
            return False
        event = self.events[sequence]
        witness = self.witnesses[sequence]
        return (
            event.event_type is ChronoEventType.TRANSITION
            and event.proposal_digest == outcome.proposal_digest
            and event.outcome_digest == outcome.digest
            and event.before_state_digest == outcome.before_digest
            and event.after_state_digest == outcome.after_digest
            and event.accepted is outcome.accepted
            and event.failure is outcome.failure
            and witness.event_digest == event.digest
            and witness.subject is WitnessSubject.TRANSITION_OUTCOME
            and witness.subject_digest == outcome.digest
        )
