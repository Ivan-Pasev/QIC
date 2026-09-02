from __future__ import annotations

from pathlib import Path

from qic.core import (
    AuthorityDomain,
    AuthorityGrant,
    AuthorityRequirement,
    DurableArtifactView,
    JournalFileStore,
    JournalPhase,
    JournalRecord,
    ReconciliationClass,
    StateSnapshot,
    TransitionEngine,
    TransitionFailure,
    TransitionFamily,
    TransitionProposal,
    TransitionSpec,
    digest_hex,
    reconcile_recovery,
)


def rejected_transition():
    state = StateSnapshot(revision=0, entries=(("counter", "0"),))
    proposal = TransitionProposal(
        proposal_id="rejected-recovery",
        actor="worker",
        operation="state.increment",
        expected_state_digest=state.digest,
        payload=(("key", "counter"),),
    )
    spec = TransitionSpec(
        operation="state.increment",
        family=TransitionFamily.COMPUTATIONAL,
        authority=AuthorityRequirement(
            domains=frozenset({AuthorityDomain.COMPUTATIONAL}),
            capabilities=frozenset({"state.increment"}),
            resources=frozenset({"state.counter"}),
        ),
    )
    wrong_grant = AuthorityGrant(
        grant_id="wrong-grant",
        subject="worker",
        issuer="qic.root",
        domains=frozenset({AuthorityDomain.EPISTEMIC}),
        capabilities=frozenset({"state.increment"}),
        resources=frozenset({"state.counter"}),
    )

    def increment(current: StateSnapshot, requested: TransitionProposal) -> StateSnapshot:
        return StateSnapshot(revision=1, entries=(("counter", "1"),))

    outcome = TransitionEngine(specs=(spec,), rules={"state.increment": increment}).execute(
        state=state,
        proposal=proposal,
        grant=wrong_grant,
    )
    return state, proposal, wrong_grant, outcome


def test_rejected_g4_outcome_remains_noncommit_after_restart(tmp_path: Path) -> None:
    state, proposal, grant, outcome = rejected_transition()
    assert not outcome.accepted
    assert outcome.failure is TransitionFailure.AUTHORITY_DENIED
    assert outcome.after_state is state

    prepared = JournalRecord(
        transaction_id="tx-rejected",
        sequence=0,
        phase=JournalPhase.PREPARED,
        proposal_digest=digest_hex(proposal, domain="recovery.test.proposal"),
        actor=proposal.actor,
        grant_digest=digest_hex(grant, domain="recovery.test.grant"),
        before_state_digest=state.digest,
    )
    aborted = prepared.successor(
        JournalPhase.ABORTED,
        reason=f"G4:{outcome.failure.value}",
    )

    store = JournalFileStore(tmp_path / "journal")
    store.append(prepared)
    store.append(aborted)

    restarted = JournalFileStore(tmp_path / "journal").load("tx-rejected")
    result = reconcile_recovery(
        restarted,
        DurableArtifactView(state_digest=state.digest),
    )
    assert result.classification is ReconciliationClass.ABORTED
    assert restarted[-1].after_state_digest is None
    assert restarted[-1].outcome_digest is None
    assert state.get("counter") == "0"


def test_rejected_terminal_journal_cannot_be_advanced_into_commit(tmp_path: Path) -> None:
    state, proposal, grant, outcome = rejected_transition()
    prepared = JournalRecord(
        transaction_id="tx-rejected",
        sequence=0,
        phase=JournalPhase.PREPARED,
        proposal_digest=digest_hex(proposal, domain="recovery.test.proposal"),
        actor=proposal.actor,
        grant_digest=digest_hex(grant, domain="recovery.test.grant"),
        before_state_digest=state.digest,
    )
    aborted = prepared.successor(JournalPhase.ABORTED, reason=outcome.failure.value)
    assert aborted.terminal
    assert not aborted.may_advance_to(JournalPhase.STATE_COMMITTED)
