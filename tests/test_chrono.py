from __future__ import annotations

import json
from pathlib import Path

from qic.core.authority import AuthorityDomain, AuthorityGrant, AuthorityRequirement
from qic.core.chrono import ChronoChain, ChronoEvent, ChronoEventType, WitnessRecord, WitnessSubject
from qic.core.transition import (
    FAMILY_AUTHORITY,
    StateSnapshot,
    TransitionEngine,
    TransitionFailure,
    TransitionFamily,
    TransitionOutcome,
    TransitionProposal,
    TransitionSpec,
)


ROOT = Path(__file__).parents[1]


def state(value: str = "0", *, revision: int = 0) -> StateSnapshot:
    return StateSnapshot(revision=revision, entries=(("counter", value),))


def grant() -> AuthorityGrant:
    return AuthorityGrant(
        grant_id="grant-worker",
        subject="worker",
        issuer="qic.root",
        domains=frozenset({AuthorityDomain.COMPUTATIONAL}),
        capabilities=frozenset({"state.increment"}),
        resources=frozenset({"state.counter"}),
    )


def proposal(current: StateSnapshot, *, key: str = "counter") -> TransitionProposal:
    return TransitionProposal(
        proposal_id="proposal-001",
        actor="worker",
        operation="state.increment",
        expected_state_digest=current.digest,
        payload=(("key", key),),
    )


def increment_rule(current: StateSnapshot, requested: TransitionProposal) -> StateSnapshot | None:
    if requested.get("key") != "counter":
        return None
    value = current.get("counter")
    if value is None or not value.isdigit():
        return None
    return StateSnapshot(
        revision=current.revision + 1,
        entries=(("counter", str(int(value) + 1)),),
    )


def engine() -> TransitionEngine:
    family = TransitionFamily.COMPUTATIONAL
    domain = FAMILY_AUTHORITY[family]
    assert domain is not None
    spec = TransitionSpec(
        operation="state.increment",
        family=family,
        authority=AuthorityRequirement(
            domains=frozenset({domain}),
            capabilities=frozenset({"state.increment"}),
            resources=frozenset({"state.counter"}),
        ),
    )
    return TransitionEngine(specs=(spec,), rules={"state.increment": increment_rule})


def accepted_outcome(current: StateSnapshot) -> TransitionOutcome:
    return engine().execute(state=current, proposal=proposal(current), grant=grant())


def rejected_outcome(current: StateSnapshot) -> TransitionOutcome:
    return engine().execute(state=current, proposal=proposal(current, key="missing"), grant=grant())


def test_genesis_chain_is_valid_and_bound_to_state() -> None:
    current = state()
    chain = ChronoChain.genesis(current)
    assert chain.verify() == (True, None)
    assert chain.current_state_digest == current.digest
    assert chain.events[0].event_type is ChronoEventType.GENESIS
    assert chain.witnesses[0].subject is WitnessSubject.GENESIS_STATE
    assert chain.witnesses[0].subject_digest == current.digest


def test_accepted_transition_appends_causal_event_and_witness() -> None:
    current = state()
    outcome = accepted_outcome(current)
    assert outcome.accepted
    chain = ChronoChain.genesis(current).append_outcome(outcome)
    assert chain.verify() == (True, None)
    assert chain.current_state_digest == outcome.after_digest
    assert chain.verifies_outcome(1, outcome)
    assert chain.events[1].previous_event_digest == chain.events[0].digest
    assert chain.witnesses[1].previous_witness_digest == chain.witnesses[0].digest


def test_rejected_transition_is_witnessable_without_state_commit() -> None:
    current = state()
    outcome = rejected_outcome(current)
    assert not outcome.accepted
    assert outcome.failure is TransitionFailure.RULE_REJECTED
    chain = ChronoChain.genesis(current).append_outcome(outcome)
    event = chain.events[1]
    assert chain.verify() == (True, None)
    assert event.accepted is False
    assert event.before_state_digest == event.after_state_digest == current.digest
    assert chain.current_state_digest == current.digest
    assert chain.verifies_outcome(1, outcome)


def test_chain_rejects_outcome_from_wrong_causal_state() -> None:
    chain = ChronoChain.genesis(state())
    wrong = accepted_outcome(state("9", revision=9))
    try:
        chain.append_outcome(wrong)
    except ValueError as exc:
        assert "current Chrono state" in str(exc)
    else:
        raise AssertionError("causally stale outcome must be rejected")


def test_event_deletion_is_detected() -> None:
    s0 = state()
    first = accepted_outcome(s0)
    chain = ChronoChain.genesis(s0).append_outcome(first)
    second = accepted_outcome(first.after_state)
    chain = chain.append_outcome(second)
    tampered = ChronoChain(
        events=(chain.events[0], chain.events[2]),
        witnesses=(chain.witnesses[0], chain.witnesses[2]),
    )
    assert tampered.verify()[0] is False


def test_event_reordering_is_detected() -> None:
    s0 = state()
    first = accepted_outcome(s0)
    chain = ChronoChain.genesis(s0).append_outcome(first)
    second = accepted_outcome(first.after_state)
    chain = chain.append_outcome(second)
    tampered = ChronoChain(
        events=(chain.events[0], chain.events[2], chain.events[1]),
        witnesses=(chain.witnesses[0], chain.witnesses[2], chain.witnesses[1]),
    )
    assert tampered.verify()[0] is False


def test_forged_previous_event_link_is_detected() -> None:
    s0 = state()
    outcome = accepted_outcome(s0)
    chain = ChronoChain.genesis(s0).append_outcome(outcome)
    original = chain.events[1]
    forged = ChronoEvent(
        sequence=original.sequence,
        previous_event_digest="forged",
        event_type=original.event_type,
        proposal_digest=original.proposal_digest,
        outcome_digest=original.outcome_digest,
        before_state_digest=original.before_state_digest,
        after_state_digest=original.after_state_digest,
        accepted=original.accepted,
        failure=original.failure,
    )
    tampered = ChronoChain(events=(chain.events[0], forged), witnesses=chain.witnesses)
    assert tampered.verify() == (False, "PREVIOUS_EVENT_DIGEST_MISMATCH")


def test_event_mutation_breaks_witness_binding() -> None:
    s0 = state()
    outcome = accepted_outcome(s0)
    chain = ChronoChain.genesis(s0).append_outcome(outcome)
    original = chain.events[1]
    mutated = ChronoEvent(
        sequence=original.sequence,
        previous_event_digest=original.previous_event_digest,
        event_type=original.event_type,
        proposal_digest="different-proposal",
        outcome_digest=original.outcome_digest,
        before_state_digest=original.before_state_digest,
        after_state_digest=original.after_state_digest,
        accepted=original.accepted,
        failure=original.failure,
    )
    tampered = ChronoChain(events=(chain.events[0], mutated), witnesses=chain.witnesses)
    assert tampered.verify() == (False, "WITNESS_EVENT_MISMATCH")


def test_witness_mutation_is_detected() -> None:
    s0 = state()
    outcome = accepted_outcome(s0)
    chain = ChronoChain.genesis(s0).append_outcome(outcome)
    original = chain.witnesses[1]
    forged = WitnessRecord(
        sequence=original.sequence,
        previous_witness_digest=original.previous_witness_digest,
        event_digest=original.event_digest,
        subject=original.subject,
        subject_digest="wrong-outcome",
    )
    tampered = ChronoChain(events=chain.events, witnesses=(chain.witnesses[0], forged))
    assert tampered.verify() == (False, "WITNESS_OUTCOME_MISMATCH")


def test_external_outcome_mismatch_is_detected() -> None:
    s0 = state()
    outcome = accepted_outcome(s0)
    chain = ChronoChain.genesis(s0).append_outcome(outcome)
    different = TransitionOutcome(
        accepted=False,
        failure=TransitionFailure.RULE_REJECTED,
        proposal_digest=outcome.proposal_digest,
        before_state=s0,
        after_state=s0,
    )
    assert not chain.verifies_outcome(1, different)


def test_chrono_schema_enum_parity() -> None:
    payload = json.loads((ROOT / "schemas" / "chrono.schema.json").read_text(encoding="utf-8"))
    assert payload["$defs"]["event_type"]["enum"] == [item.value for item in ChronoEventType]
    assert payload["$defs"]["witness_subject"]["enum"] == [item.value for item in WitnessSubject]
    assert payload["$defs"]["failure"]["enum"] == [item.value for item in TransitionFailure]


def test_chrono_golden_vectors() -> None:
    payload = json.loads((Path(__file__).parent / "vectors" / "chrono_v1.json").read_text(encoding="utf-8"))
    s0 = state()
    outcome = accepted_outcome(s0)
    chain = ChronoChain.genesis(s0).append_outcome(outcome)
    assert s0.digest == payload["genesis_state_digest"]
    assert outcome.proposal_digest == payload["accepted_proposal_digest"]
    assert outcome.digest == payload["accepted_outcome_digest"]
    assert outcome.after_digest == payload["accepted_after_state_digest"]
    assert chain.events[0].digest == payload["genesis_event_digest"]
    assert chain.witnesses[0].digest == payload["genesis_witness_digest"]
    assert chain.events[1].digest == payload["transition_event_digest"]
    assert chain.witnesses[1].digest == payload["transition_witness_digest"]
