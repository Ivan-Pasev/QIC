from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from qic.core.authority import AuthorityDomain, AuthorityGrant
from qic.core.kbi import (
    ClaimRecord,
    ClaimStatus,
    ContradictionRecord,
    EvidenceBinding,
    EvidenceClass,
    EvidenceRecord,
    EvidenceRelation,
    KBIContext,
    KBIExecutor,
    KBIState,
)
from qic.core.transition import TransitionFailure


ROOT = Path(__file__).parents[1]
ALL_CAPABILITIES = frozenset(
    {
        "kbi.claim.assert",
        "kbi.evidence.add",
        "kbi.evidence.bind",
        "kbi.claim.promote",
        "kbi.claim.contradict",
    }
)


def epistemic_grant(*, capabilities: frozenset[str] = ALL_CAPABILITIES) -> AuthorityGrant:
    return AuthorityGrant(
        grant_id="grant-kbi",
        subject="curator",
        issuer="qic.root",
        domains=frozenset({AuthorityDomain.EPISTEMIC}),
        capabilities=capabilities,
        resources=frozenset({"state.kbi"}),
    )


def computational_grant() -> AuthorityGrant:
    return AuthorityGrant(
        grant_id="grant-compute",
        subject="curator",
        issuer="qic.root",
        domains=frozenset({AuthorityDomain.COMPUTATIONAL}),
        capabilities=frozenset({"kbi.claim.promote"}),
        resources=frozenset({"state.kbi"}),
    )


def claim(claim_id: str = "claim-a", *, origin: str = "source.origin") -> ClaimRecord:
    return ClaimRecord(
        claim_id=claim_id,
        statement=f"statement for {claim_id}",
        origin_source_id=origin,
    )


def evidence(evidence_id: str, source_id: str) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=evidence_id,
        evidence_class=EvidenceClass.OBSERVED,
        source_id=source_id,
        artifact_digest=f"artifact-{evidence_id}",
    )


def execute_assert(context: KBIContext, record: ClaimRecord, *, proposal_id: str) -> KBIContext:
    result = KBIExecutor().assert_claim(
        context,
        record,
        actor="curator",
        grant=epistemic_grant(),
        proposal_id=proposal_id,
    )
    assert result.outcome.accepted
    return result.context


def add_support(
    context: KBIContext,
    *,
    evidence_id: str,
    source_id: str,
    claim_id: str = "claim-a",
) -> KBIContext:
    executor = KBIExecutor()
    added = executor.add_evidence(
        context,
        evidence(evidence_id, source_id),
        actor="curator",
        grant=epistemic_grant(),
        proposal_id=f"add-{evidence_id}",
    )
    assert added.outcome.accepted
    bound = executor.bind_evidence(
        added.context,
        EvidenceBinding(
            binding_id=f"bind-{evidence_id}",
            claim_id=claim_id,
            evidence_id=evidence_id,
            relation=EvidenceRelation.SUPPORTS,
        ),
        actor="curator",
        grant=epistemic_grant(),
        proposal_id=f"bind-{evidence_id}",
    )
    assert bound.outcome.accepted
    return bound.context


def test_assertion_binding_and_promotion_are_separate_authoritative_steps() -> None:
    context = KBIContext.genesis()
    context = execute_assert(context, claim(), proposal_id="assert-a")
    assert context.kbi.claim("claim-a").status is ClaimStatus.ASSERTED  # type: ignore[union-attr]

    context = add_support(context, evidence_id="e1", source_id="source.a")
    # Evidence binding alone never promotes the claim.
    assert context.kbi.claim("claim-a").status is ClaimStatus.ASSERTED  # type: ignore[union-attr]

    result = KBIExecutor().promote_claim(
        context,
        "claim-a",
        ClaimStatus.SUPPORTED,
        actor="curator",
        grant=epistemic_grant(),
        proposal_id="promote-supported",
    )
    assert result.outcome.accepted
    assert result.context.kbi.claim("claim-a").status is ClaimStatus.SUPPORTED  # type: ignore[union-attr]
    assert result.context.chrono.verifies_outcome(
        len(result.context.chrono.events) - 1, result.outcome
    )


def test_full_minimal_forward_lifecycle_requires_independent_support() -> None:
    context = execute_assert(KBIContext.genesis(), claim(), proposal_id="assert-a")
    context = add_support(context, evidence_id="e1", source_id="source.a")
    context = KBIExecutor().promote_claim(
        context,
        "claim-a",
        ClaimStatus.SUPPORTED,
        actor="curator",
        grant=epistemic_grant(),
        proposal_id="supported",
    ).context
    context = add_support(context, evidence_id="e2", source_id="source.b")
    assert context.kbi.independent_support_sources("claim-a") == frozenset(
        {"source.a", "source.b"}
    )
    for status in (
        ClaimStatus.CORROBORATED,
        ClaimStatus.VALIDATED,
        ClaimStatus.CANONICAL,
    ):
        result = KBIExecutor().promote_claim(
            context,
            "claim-a",
            status,
            actor="curator",
            grant=epistemic_grant(),
            proposal_id=f"promote-{status.value.lower()}",
        )
        assert result.outcome.accepted
        context = result.context
    assert context.kbi.claim("claim-a").status is ClaimStatus.CANONICAL  # type: ignore[union-attr]


def test_evidence_echo_does_not_create_independent_corroboration() -> None:
    context = execute_assert(KBIContext.genesis(), claim(), proposal_id="assert-a")
    context = add_support(context, evidence_id="e1", source_id="source.same")
    context = KBIExecutor().promote_claim(
        context,
        "claim-a",
        ClaimStatus.SUPPORTED,
        actor="curator",
        grant=epistemic_grant(),
        proposal_id="supported",
    ).context
    context = add_support(context, evidence_id="e2", source_id="source.same")
    assert context.kbi.independent_support_sources("claim-a") == frozenset({"source.same"})
    with pytest.raises(ValueError, match="two independent"):
        context.kbi.candidate_promote("claim-a", ClaimStatus.CORROBORATED)


def test_self_origin_evidence_is_not_counted_as_independent_support() -> None:
    context = execute_assert(
        KBIContext.genesis(),
        claim(origin="source.origin"),
        proposal_id="assert-a",
    )
    context = add_support(context, evidence_id="e1", source_id="source.origin")
    context = add_support(context, evidence_id="e2", source_id="source.a")
    assert context.kbi.independent_support_sources("claim-a") == frozenset({"source.a"})


def test_unauthorized_promotion_is_rejected_and_witnessed_without_commit() -> None:
    context = execute_assert(KBIContext.genesis(), claim(), proposal_id="assert-a")
    context = add_support(context, evidence_id="e1", source_id="source.a")
    before_kbi = context.kbi
    before_runtime = context.runtime_state
    before_events = len(context.chrono.events)
    result = KBIExecutor().promote_claim(
        context,
        "claim-a",
        ClaimStatus.SUPPORTED,
        actor="curator",
        grant=computational_grant(),
        proposal_id="unauthorized-promotion",
    )
    assert not result.outcome.accepted
    assert result.outcome.failure is TransitionFailure.AUTHORITY_DENIED
    assert result.context.kbi is before_kbi
    assert result.context.runtime_state is before_runtime
    assert len(result.context.chrono.events) == before_events + 1
    assert result.context.chrono.current_state_digest == before_runtime.digest
    assert result.context.chrono.verifies_outcome(
        len(result.context.chrono.events) - 1, result.outcome
    )


def test_stale_kbi_admission_is_rejected_without_kbi_change() -> None:
    context = KBIContext.genesis()
    before = context.kbi
    result = KBIExecutor().assert_claim(
        context,
        claim(),
        actor="curator",
        grant=epistemic_grant(),
        proposal_id="stale-assert",
        expected_state_digest="stale-runtime-root",
    )
    assert not result.outcome.accepted
    assert result.outcome.failure is TransitionFailure.STALE_STATE
    assert result.context.kbi is before
    assert result.context.runtime_state is context.runtime_state
    assert result.context.chrono.verifies_outcome(1, result.outcome)


def test_missing_evidence_and_duplicate_logical_bindings_fail_closed() -> None:
    context = execute_assert(KBIContext.genesis(), claim(), proposal_id="assert-a")
    with pytest.raises(ValueError, match="evidence does not exist"):
        context.kbi.candidate_add_binding(
            EvidenceBinding(
                binding_id="missing",
                claim_id="claim-a",
                evidence_id="does-not-exist",
                relation=EvidenceRelation.SUPPORTS,
            )
        )

    context = add_support(context, evidence_id="e1", source_id="source.a")
    with pytest.raises(ValueError, match="duplicate logical"):
        context.kbi.candidate_add_binding(
            EvidenceBinding(
                binding_id="different-id",
                claim_id="claim-a",
                evidence_id="e1",
                relation=EvidenceRelation.SUPPORTS,
            )
        )


def test_contradiction_is_explicit_and_cannot_be_silently_discarded() -> None:
    context = execute_assert(KBIContext.genesis(), claim("claim-a"), proposal_id="assert-a")
    context = execute_assert(context, claim("claim-b", origin="source.b"), proposal_id="assert-b")
    result = KBIExecutor().contradict_claim(
        context,
        ContradictionRecord(
            contradiction_id="contra-1",
            target_claim_id="claim-a",
            counter_claim_id="claim-b",
        ),
        actor="curator",
        grant=epistemic_grant(),
        proposal_id="contradict-a",
    )
    assert result.outcome.accepted
    assert result.context.kbi.has_contradiction("claim-a")
    assert result.context.kbi.claim("claim-a").status is ClaimStatus.CONTRADICTED  # type: ignore[union-attr]
    assert result.context.kbi.claim("claim-b").status is ClaimStatus.CONTESTED  # type: ignore[union-attr]
    assert len(result.context.kbi.contradictions) == 1


def test_kbi_records_and_state_are_frozen() -> None:
    record = claim()
    state_value = KBIState(claims=(record,))
    with pytest.raises(FrozenInstanceError):
        record.status = ClaimStatus.CANONICAL  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        state_value.claims = ()  # type: ignore[misc]


def test_kbi_registry_enum_parity() -> None:
    payload = json.loads((ROOT / "registry" / "kbi.json").read_text(encoding="utf-8"))
    assert payload["claim_statuses"] == [item.value for item in ClaimStatus]
    assert payload["evidence_classes"] == [item.value for item in EvidenceClass]
    assert payload["evidence_relations"] == [item.value for item in EvidenceRelation]


def test_kbi_schema_enum_parity() -> None:
    payload = json.loads((ROOT / "schemas" / "kbi.schema.json").read_text(encoding="utf-8"))
    assert payload["$defs"]["claim_status"]["enum"] == [item.value for item in ClaimStatus]
    assert payload["$defs"]["evidence_class"]["enum"] == [item.value for item in EvidenceClass]
    assert payload["$defs"]["evidence_relation"]["enum"] == [item.value for item in EvidenceRelation]
