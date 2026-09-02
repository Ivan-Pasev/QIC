from __future__ import annotations

import json
from pathlib import Path

import pytest

from qic.core import canonical_text, digest_hex
from qic.core.authority import AuthorityDomain, AuthorityGrant, AuthorityRequirement, GrantState
from qic.core.transition import (
    ENABLED_FAMILIES,
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


def grant(
    *,
    subject: str = "worker",
    domains: frozenset[AuthorityDomain] = frozenset({AuthorityDomain.COMPUTATIONAL}),
    capabilities: frozenset[str] = frozenset({"state.increment"}),
    resources: frozenset[str] = frozenset({"state.counter"}),
    state_value: GrantState = GrantState.ACTIVE,
) -> AuthorityGrant:
    return AuthorityGrant(
        grant_id="grant-worker",
        subject=subject,
        issuer="qic.root",
        domains=domains,
        capabilities=capabilities,
        resources=resources,
        state=state_value,
    )


def proposal(current: StateSnapshot, *, operation: str = "state.increment", actor: str = "worker") -> TransitionProposal:
    return TransitionProposal(
        proposal_id="proposal-001",
        actor=actor,
        operation=operation,
        expected_state_digest=current.digest,
        payload=(("key", "counter"),),
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


def rejecting_rule(current: StateSnapshot, requested: TransitionProposal) -> StateSnapshot | None:
    return None


def counter_below_two(candidate: StateSnapshot) -> bool:
    value = candidate.get("counter")
    return value is not None and int(value) < 2


def build_engine(
    *,
    family: TransitionFamily = TransitionFamily.COMPUTATIONAL,
    rule=increment_rule,
    invariant_ids: tuple[str, ...] = (),
    global_invariant_ids: tuple[str, ...] = (),
) -> TransitionEngine:
    authority = AuthorityRequirement(
        domains=frozenset({FAMILY_AUTHORITY[family]}) if FAMILY_AUTHORITY[family] is not None else frozenset(),
        capabilities=frozenset({"state.increment"}),
        resources=frozenset({"state.counter"}),
    )
    spec = TransitionSpec(
        operation="state.increment",
        family=family,
        authority=authority,
        invariant_ids=invariant_ids,
    )
    return TransitionEngine(
        specs=(spec,),
        rules={"state.increment": rule},
        invariants={"counter.below-two": counter_below_two},
        global_invariant_ids=global_invariant_ids,
    )


def assert_rejected_unchanged(
    outcome: TransitionOutcome,
    current: StateSnapshot,
    failure: TransitionFailure,
) -> None:
    assert not outcome.accepted
    assert outcome.failure is failure
    assert outcome.before_state is current
    assert outcome.after_state is current
    assert outcome.before_digest == outcome.after_digest == current.digest
    assert canonical_text(outcome.before_state) == canonical_text(outcome.after_state)


def test_successful_transition_commits_candidate_after_all_gates() -> None:
    current = state()
    result = build_engine().execute(state=current, proposal=proposal(current), grant=grant())
    assert result.accepted
    assert result.failure is None
    assert result.before_state is current
    assert result.after_state is not current
    assert result.after_state.revision == 1
    assert result.after_state.get("counter") == "1"
    assert result.before_digest != result.after_digest


def test_unknown_operation_cannot_commit() -> None:
    current = state()
    result = build_engine().execute(
        state=current,
        proposal=proposal(current, operation="unknown.operation"),
        grant=grant(),
    )
    assert_rejected_unchanged(result, current, TransitionFailure.UNKNOWN_OPERATION)


@pytest.mark.parametrize("family", [TransitionFamily.PHYSICAL, TransitionFamily.EVOLUTIONARY])
def test_t4_t5_are_not_enabled(family: TransitionFamily) -> None:
    current = state()
    required_domain = FAMILY_AUTHORITY[family]
    assert required_domain is not None
    engine = build_engine(family=family)
    result = engine.execute(
        state=current,
        proposal=proposal(current),
        grant=grant(domains=frozenset({required_domain})),
    )
    assert_rejected_unchanged(result, current, TransitionFailure.FAMILY_NOT_ENABLED)


def test_stale_state_cannot_commit() -> None:
    current = state()
    stale = TransitionProposal(
        proposal_id="stale",
        actor="worker",
        operation="state.increment",
        expected_state_digest=state("9", revision=9).digest,
        payload=(("key", "counter"),),
    )
    result = build_engine().execute(state=current, proposal=stale, grant=grant())
    assert_rejected_unchanged(result, current, TransitionFailure.STALE_STATE)


def test_actor_must_match_current_grant_subject() -> None:
    current = state()
    result = build_engine().execute(
        state=current,
        proposal=proposal(current, actor="other"),
        grant=grant(subject="worker"),
    )
    assert_rejected_unchanged(result, current, TransitionFailure.SUBJECT_MISMATCH)


def test_missing_domain_capability_resource_and_revocation_all_deny() -> None:
    current = state()
    requested = proposal(current)
    denied = (
        grant(domains=frozenset({AuthorityDomain.EPISTEMIC})),
        grant(capabilities=frozenset()),
        grant(resources=frozenset()),
        grant(state_value=GrantState.REVOKED),
    )
    for current_grant in denied:
        result = build_engine().execute(state=current, proposal=requested, grant=current_grant)
        assert_rejected_unchanged(result, current, TransitionFailure.AUTHORITY_DENIED)


def test_rule_rejection_cannot_commit() -> None:
    current = state()
    result = build_engine(rule=rejecting_rule).execute(
        state=current,
        proposal=proposal(current),
        grant=grant(),
    )
    assert_rejected_unchanged(result, current, TransitionFailure.RULE_REJECTED)


def test_scoped_invariant_failure_cannot_commit() -> None:
    current = state("1", revision=1)
    result = build_engine(invariant_ids=("counter.below-two",)).execute(
        state=current,
        proposal=proposal(current),
        grant=grant(),
    )
    assert_rejected_unchanged(result, current, TransitionFailure.INVARIANT_FAILED)
    assert result.failed_invariant == "counter.below-two"


def test_global_invariant_failure_cannot_commit() -> None:
    current = state("1", revision=1)
    result = build_engine(global_invariant_ids=("counter.below-two",)).execute(
        state=current,
        proposal=proposal(current),
        grant=grant(),
    )
    assert_rejected_unchanged(result, current, TransitionFailure.INVARIANT_FAILED)
    assert result.failed_invariant == "counter.below-two"


def test_family_registry_matches_runtime_contract() -> None:
    payload = json.loads((ROOT / "registry" / "transitions.json").read_text(encoding="utf-8"))
    rows = {row["id"]: row for row in payload["transitions"]}
    assert set(rows) == {family.value for family in TransitionFamily}
    for family in TransitionFamily:
        row = rows[family.value]
        runtime_domain = FAMILY_AUTHORITY[family]
        assert row["authority_domain"] == (runtime_domain.value if runtime_domain else None)
        if family in ENABLED_FAMILIES:
            assert row.get("status", "ENABLED") != "NOT_ENABLED"
        else:
            assert row.get("status") == "NOT_ENABLED"


def test_transition_schema_enum_parity() -> None:
    payload = json.loads((ROOT / "schemas" / "transition.schema.json").read_text(encoding="utf-8"))
    assert payload["$defs"]["family"]["enum"] == [family.value for family in TransitionFamily]
    assert payload["$defs"]["failure"]["enum"] == [failure.value for failure in TransitionFailure]


def test_state_and_payload_require_sorted_unique_immutable_entries() -> None:
    with pytest.raises(TypeError):
        StateSnapshot(entries=[("counter", "0")])  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        StateSnapshot(entries=(("z", "0"), ("a", "1")))
    with pytest.raises(ValueError):
        TransitionProposal(
            proposal_id="p",
            actor="worker",
            operation="state.increment",
            expected_state_digest="x",
            payload=(("key", "a"), ("key", "b")),
        )


def test_engine_rejects_incomplete_rule_or_invariant_registry() -> None:
    spec = TransitionSpec(
        operation="state.increment",
        family=TransitionFamily.COMPUTATIONAL,
        authority=AuthorityRequirement(domains=frozenset({AuthorityDomain.COMPUTATIONAL})),
    )
    with pytest.raises(ValueError):
        TransitionEngine(specs=(spec,), rules={})
    with pytest.raises(ValueError):
        TransitionEngine(
            specs=(TransitionSpec(
                operation="state.increment",
                family=TransitionFamily.COMPUTATIONAL,
                authority=AuthorityRequirement(domains=frozenset({AuthorityDomain.COMPUTATIONAL})),
                invariant_ids=("missing",),
            ),),
            rules={"state.increment": increment_rule},
        )


def test_transition_golden_vector() -> None:
    payload = json.loads((Path(__file__).parent / "vectors" / "transition_v1.json").read_text(encoding="utf-8"))
    spec = payload["state"]
    current = StateSnapshot(
        revision=spec["revision"],
        entries=tuple((key, value) for key, value in spec["entries"]),
    )
    assert current.digest == spec["sha256"]

    p = payload["proposal"]
    requested = TransitionProposal(
        proposal_id=p["proposal_id"],
        actor=p["actor"],
        operation=p["operation"],
        expected_state_digest=p["expected_state_digest"],
        payload=tuple((key, value) for key, value in p["payload"]),
    )
    assert canonical_text(requested) == payload["proposal_canonical"]
    assert requested.digest == payload["proposal_sha256"]

    result = build_engine().execute(state=current, proposal=requested, grant=grant())
    assert result.accepted
    assert result.after_state.revision == payload["outcome"]["after_revision"]
    assert result.after_state.entries == tuple(tuple(item) for item in payload["outcome"]["after_entries"])
    assert result.digest == payload["outcome"]["sha256"]
