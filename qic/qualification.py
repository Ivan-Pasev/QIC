"""G8 adversarial constitutional qualification for the QIC genesis stack.

This module exercises declared structural properties only. It deliberately
contains modeled mutants representing plausible constitutional gate-removal
bugs. A mutant is "killed" when the real runtime rejects/contains the case while
the permissive mutant would incorrectly accept it.

Qualification PASS is not certification of truth, security, formal correctness,
physical safety, legal compliance, deployment readiness, or crash durability.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Callable

from .core import (
    AuthorityDomain,
    AuthorityGrant,
    AuthorityRequirement,
    ChronoChain,
    ClaimRecord,
    ClaimStatus,
    EvidenceBinding,
    EvidenceClass,
    EvidenceRecord,
    EvidenceRelation,
    KBIState,
    MaturityVector,
    StateSnapshot,
    TransitionEngine,
    TransitionFamily,
    TransitionProposal,
    TransitionSpec,
    canonical_bytes,
    digest_hex,
)
from .core.canonical import CanonicalizationError
from .core.maturity_vector import (
    DeploymentMaturity,
    EvidenceMaturity,
    FormalMaturity,
    HardwareMaturity,
    SemanticMaturity,
)
from .core.transition import ENABLED_FAMILIES, FAMILY_AUTHORITY, TransitionFailure


CLAIM_BOUNDARY = (
    "G8 qualification establishes only the declared local structural properties "
    "tested by this campaign. It is not certification of semantic truth, "
    "production security, formal correctness, physical safety, legal compliance, "
    "deployment readiness, cryptographic identity, federation, or durable recovery."
)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _check(name: str, passed: bool, detail: str) -> dict[str, object]:
    return {"check": name, "detail": detail, "pass": bool(passed)}


def check_canonical_fail_closed() -> dict[str, object]:
    float_rejected = False
    bad_key_rejected = False
    try:
        canonical_bytes(1.25)
    except CanonicalizationError:
        float_rejected = True
    try:
        canonical_bytes({1: "ambiguous"})
    except CanonicalizationError:
        bad_key_rejected = True
    domain_separated = digest_hex("same", domain="qualification.a") != digest_hex(
        "same", domain="qualification.b"
    )
    return _check(
        "canonical_fail_closed",
        float_rejected and bad_key_rejected and domain_separated,
        f"float={float_rejected},mapping_key={bad_key_rejected},domain_separated={domain_separated}",
    )


def check_maturity_partial_order() -> dict[str, object]:
    semantic_only = MaturityVector(
        semantic=SemanticMaturity.TESTED,
        evidence=EvidenceMaturity.NONE,
        formal=FormalMaturity.NONE,
        hardware=HardwareMaturity.NONE,
        deployment=DeploymentMaturity.NONE,
    )
    hardware_only = MaturityVector(
        semantic=SemanticMaturity.CONCEPTUAL,
        evidence=EvidenceMaturity.NONE,
        formal=FormalMaturity.NONE,
        hardware=HardwareMaturity.HARDWARE_TESTED,
        deployment=DeploymentMaturity.NONE,
    )
    formal_only = MaturityVector(formal=FormalMaturity.MACHINE_CHECKED)
    independent = (
        not semantic_only.satisfies(hardware_only)
        and not hardware_only.satisfies(semantic_only)
        and not formal_only.satisfies(hardware_only)
    )
    return _check(
        "maturity_partial_order",
        independent,
        f"semantic_vs_hardware={semantic_only.satisfies(hardware_only)},hardware_vs_semantic={hardware_only.satisfies(semantic_only)},formal_vs_hardware={formal_only.satisfies(hardware_only)}",
    )


def _authority_fixture() -> tuple[AuthorityGrant, AuthorityRequirement]:
    grant = AuthorityGrant(
        grant_id="qualification-parent",
        subject="operator",
        issuer="qic.root",
        domains=frozenset({AuthorityDomain.COMPUTATIONAL}),
        capabilities=frozenset({"state.increment"}),
        resources=frozenset({"state.counter"}),
    )
    requirement = AuthorityRequirement(
        domains=frozenset({AuthorityDomain.COMPUTATIONAL}),
        capabilities=frozenset({"state.increment", "state.delete"}),
        resources=frozenset({"state.counter"}),
    )
    return grant, requirement


def check_authority_nonamplification() -> dict[str, object]:
    parent, missing_capability = _authority_fixture()
    expanded = AuthorityGrant(
        grant_id="qualification-child",
        subject="child",
        issuer="operator",
        parent_grant_id=parent.grant_id,
        domains=frozenset({AuthorityDomain.COMPUTATIONAL, AuthorityDomain.EPISTEMIC}),
        capabilities=frozenset({"state.increment"}),
        resources=frozenset({"state.counter"}),
    )
    revoked_denies = not parent.revoked_copy().satisfies(
        AuthorityRequirement(domains=frozenset({AuthorityDomain.COMPUTATIONAL}))
    )
    passed = (
        not parent.satisfies(missing_capability)
        and not parent.can_delegate(expanded)
        and revoked_denies
    )
    return _check(
        "authority_nonamplification",
        passed,
        f"missing_capability={parent.satisfies(missing_capability)},expanded_delegate={parent.can_delegate(expanded)},revoked_denies={revoked_denies}",
    )


def _transition_fixture(
    family: TransitionFamily = TransitionFamily.COMPUTATIONAL,
) -> tuple[StateSnapshot, TransitionProposal, AuthorityGrant, TransitionEngine]:
    state = StateSnapshot(revision=0, entries=(("counter", "0"),))
    operation = "state.increment" if family is TransitionFamily.COMPUTATIONAL else "lab.effect"
    capability = operation
    resource = "state.counter" if family is TransitionFamily.COMPUTATIONAL else "lab.reference"
    domain = FAMILY_AUTHORITY[family]
    requirement = AuthorityRequirement(
        domains=frozenset({domain}) if domain is not None else frozenset(),
        capabilities=frozenset({capability}),
        resources=frozenset({resource}),
    )
    spec = TransitionSpec(operation=operation, family=family, authority=requirement)
    grant = AuthorityGrant(
        grant_id=f"qualification-{family.value.lower()}-grant",
        subject="worker",
        issuer="qic.root",
        domains=requirement.domains,
        capabilities=requirement.capabilities,
        resources=requirement.resources,
    )
    proposal = TransitionProposal(
        proposal_id=f"qualification-{family.value.lower()}-proposal",
        actor="worker",
        operation=operation,
        expected_state_digest=state.digest,
        payload=(("key", "counter"),),
    )

    def rule(current: StateSnapshot, requested: TransitionProposal) -> StateSnapshot | None:
        return StateSnapshot(
            revision=current.revision + 1,
            entries=(("counter", "1"),),
        )

    return state, proposal, grant, TransitionEngine(specs=(spec,), rules={operation: rule})


def check_transition_atomicity_and_disabled_families() -> dict[str, object]:
    state, proposal, grant, engine = _transition_fixture()
    stale = replace(proposal, expected_state_digest="stale-digest")
    stale_outcome = engine.execute(state=state, proposal=stale, grant=grant)
    wrong_grant = AuthorityGrant(
        grant_id="wrong-domain",
        subject="worker",
        issuer="qic.root",
        domains=frozenset({AuthorityDomain.EPISTEMIC}),
        capabilities=grant.capabilities,
        resources=grant.resources,
    )
    denied = engine.execute(state=state, proposal=proposal, grant=wrong_grant)

    disabled_ok = True
    disabled_details: list[str] = []
    for family in (TransitionFamily.PHYSICAL, TransitionFamily.EVOLUTIONARY):
        f_state, f_proposal, f_grant, f_engine = _transition_fixture(family)
        outcome = f_engine.execute(state=f_state, proposal=f_proposal, grant=f_grant)
        ok = (
            not outcome.accepted
            and outcome.failure is TransitionFailure.FAMILY_NOT_ENABLED
            and outcome.after_state is f_state
        )
        disabled_ok = disabled_ok and ok
        disabled_details.append(f"{family.value}={ok}")

    atomic = (
        not stale_outcome.accepted
        and stale_outcome.failure is TransitionFailure.STALE_STATE
        and stale_outcome.after_state is state
        and not denied.accepted
        and denied.failure is TransitionFailure.AUTHORITY_DENIED
        and denied.after_state is state
    )
    return _check(
        "transition_atomicity_and_disabled_families",
        atomic and disabled_ok,
        f"atomic={atomic}," + ",".join(disabled_details),
    )


def check_chrono_tamper_and_anchor_boundary() -> dict[str, object]:
    state, proposal, grant, engine = _transition_fixture()
    outcome = engine.execute(state=state, proposal=proposal, grant=grant)
    chain = ChronoChain.genesis(state).append_outcome(outcome)
    valid, _ = chain.verify()

    tampered_event = replace(chain.events[1], after_state_digest="tampered")
    tampered = ChronoChain(
        events=(chain.events[0], tampered_event),
        witnesses=chain.witnesses,
    )
    tampered_ok, _ = tampered.verify()

    prefix = ChronoChain.genesis(state)
    prefix_valid, _ = prefix.verify()
    anchored_valid, anchored_reason = prefix.verify(
        expected_length=len(chain.events),
        expected_head_event_digest=chain.head_event.digest,
        expected_head_witness_digest=chain.head_witness.digest,
    )
    passed = valid and not tampered_ok and prefix_valid and not anchored_valid
    return _check(
        "chrono_tamper_and_anchor_boundary",
        passed,
        f"full={valid},tampered={tampered_ok},unanchored_prefix={prefix_valid},anchored_prefix={anchored_valid}:{anchored_reason}",
    )


def _echo_state() -> KBIState:
    claim = ClaimRecord(
        claim_id="echo-claim",
        statement="Qualification echo claim",
        origin_source_id="source.origin",
    )
    evidence_a = EvidenceRecord(
        evidence_id="echo-a",
        evidence_class=EvidenceClass.OBSERVED,
        source_id="source.echo",
        artifact_digest="artifact-a",
    )
    evidence_b = EvidenceRecord(
        evidence_id="echo-b",
        evidence_class=EvidenceClass.ATTESTED,
        source_id="source.echo",
        artifact_digest="artifact-b",
    )
    return KBIState(
        claims=(claim,),
        evidence=(evidence_a, evidence_b),
        bindings=(
            EvidenceBinding(
                binding_id="binding-a",
                claim_id=claim.claim_id,
                evidence_id=evidence_a.evidence_id,
                relation=EvidenceRelation.SUPPORTS,
            ),
            EvidenceBinding(
                binding_id="binding-b",
                claim_id=claim.claim_id,
                evidence_id=evidence_b.evidence_id,
                relation=EvidenceRelation.SUPPORTS,
            ),
        ),
    )


def check_kbi_echo_and_contradiction_containment() -> dict[str, object]:
    echo = _echo_state()
    echo_sources = echo.independent_support_sources("echo-claim")
    echo_blocked = False
    try:
        supported = echo.candidate_promote("echo-claim", ClaimStatus.SUPPORTED)
        supported.candidate_promote("echo-claim", ClaimStatus.CORROBORATED)
    except ValueError:
        echo_blocked = True

    claim_a = ClaimRecord(
        claim_id="claim-a",
        statement="A",
        origin_source_id="origin-a",
        status=ClaimStatus.CORROBORATED,
    )
    claim_b = ClaimRecord(
        claim_id="claim-b",
        statement="B",
        origin_source_id="origin-b",
    )
    contradictory = KBIState(claims=(claim_a, claim_b)).candidate_add_contradiction(
        __import__("qic.core.kbi", fromlist=["ContradictionRecord"]).ContradictionRecord(
            contradiction_id="contradiction-1",
            target_claim_id="claim-a",
            counter_claim_id="claim-b",
        )
    )
    contradiction_preserved = (
        contradictory.claim("claim-a").status is ClaimStatus.CONTRADICTED  # type: ignore[union-attr]
        and contradictory.claim("claim-b").status is ClaimStatus.CONTESTED  # type: ignore[union-attr]
        and contradictory.has_contradiction("claim-a")
    )
    return _check(
        "kbi_echo_and_contradiction_containment",
        len(echo_sources) == 1 and echo_blocked and contradiction_preserved,
        f"distinct_echo_sources={len(echo_sources)},echo_blocked={echo_blocked},contradiction_preserved={contradiction_preserved}",
    )


def check_registry_runtime_parity() -> dict[str, object]:
    root = _root()
    try:
        transitions = json.loads((root / "registry" / "transitions.json").read_text(encoding="utf-8"))
        authority = json.loads((root / "registry" / "authority_domains.json").read_text(encoding="utf-8"))
        kbi = json.loads((root / "registry" / "kbi.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return _check("registry_runtime_parity", False, f"read_failure={exc}")

    rows = {row["id"]: row for row in transitions["transitions"]}
    transitions_ok = set(rows) == {family.value for family in TransitionFamily}
    for family in TransitionFamily:
        expected_domain = FAMILY_AUTHORITY[family]
        row = rows.get(family.value, {})
        transitions_ok = transitions_ok and row.get("authority_domain") == (
            expected_domain.value if expected_domain else None
        )
        if family in ENABLED_FAMILIES:
            transitions_ok = transitions_ok and row.get("status", "ENABLED") != "NOT_ENABLED"
        else:
            transitions_ok = transitions_ok and row.get("status") == "NOT_ENABLED"

    authority_ok = [row["id"] for row in authority["domains"]] == [
        domain.value for domain in AuthorityDomain
    ]
    kbi_ok = (
        kbi["claim_statuses"] == [item.value for item in ClaimStatus]
        and kbi["evidence_classes"] == [item.value for item in EvidenceClass]
        and kbi["evidence_relations"] == [item.value for item in EvidenceRelation]
    )
    return _check(
        "registry_runtime_parity",
        transitions_ok and authority_ok and kbi_ok,
        f"transitions={transitions_ok},authority={authority_ok},kbi={kbi_ok}",
    )


def check_public_claim_surface() -> dict[str, object]:
    root = _root()
    try:
        manifest = json.loads((root / "QIC_MANIFEST.json").read_text(encoding="utf-8"))
        cli_text = (root / "qic" / "cli.py").read_text(encoding="utf-8")
        claim_boundary = (root / "CLAIM_BOUNDARY.md").read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        return _check("public_claim_surface", False, f"read_failure={exc}")

    maturity = manifest.get("maturity", {})
    maturity_ok = (
        maturity.get("formal") == "NONE"
        and maturity.get("hardware") == "NONE"
        and maturity.get("deployment") == "LOCAL"
    )
    transition_profile = manifest.get("transition_profile", {})
    disabled_ok = transition_profile.get("not_enabled") == ["T4", "T5"]
    nonclaims = " ".join(manifest.get("explicit_nonclaims", [])).lower()
    nonclaims_ok = all(
        token in nonclaims
        for token in ("formal", "hardware", "physical", "federation", "durable", "truth")
    )
    mutation_surface_absent = all(
        token not in cli_text
        for token in (
            "mint_grant(",
            "bypass_authority",
            "enable_physical",
            "enable_evolutionary",
        )
    )
    boundary_ok = "does not" in claim_boundary.lower() or "not" in claim_boundary.lower()
    return _check(
        "public_claim_surface",
        maturity_ok and disabled_ok and nonclaims_ok and mutation_surface_absent and boundary_ok,
        f"maturity={maturity_ok},disabled={disabled_ok},nonclaims={nonclaims_ok},cli_no_bypass={mutation_surface_absent},boundary={boundary_ok}",
    )


def _mutant_scalar_maturity() -> bool:
    actual = MaturityVector(
        semantic=SemanticMaturity.TESTED,
        hardware=HardwareMaturity.NONE,
    )
    required = MaturityVector(
        semantic=SemanticMaturity.CONCEPTUAL,
        hardware=HardwareMaturity.HARDWARE_TESTED,
    )
    production_accepts = actual.satisfies(required)
    mutant_accepts = int(actual.semantic) + int(actual.hardware) >= int(required.semantic) + int(required.hardware)
    return (not production_accepts) and mutant_accepts


def _mutant_authority_any_of() -> bool:
    grant, requirement = _authority_fixture()
    production_accepts = grant.satisfies(requirement)
    mutant_accepts = (
        bool(requirement.domains & grant.domains)
        or bool(requirement.capabilities & grant.capabilities)
        or bool(requirement.resources & grant.resources)
    )
    return (not production_accepts) and mutant_accepts


def _mutant_enable_t4() -> bool:
    state, proposal, grant, engine = _transition_fixture(TransitionFamily.PHYSICAL)
    production = engine.execute(state=state, proposal=proposal, grant=grant)
    mutant_accepts = TransitionFamily.PHYSICAL not in ENABLED_FAMILIES and grant.satisfies(
        AuthorityRequirement(
            domains=frozenset({AuthorityDomain.PHYSICAL}),
            capabilities=frozenset({"lab.effect"}),
            resources=frozenset({"lab.reference"}),
        )
    )
    return (
        not production.accepted
        and production.failure is TransitionFailure.FAMILY_NOT_ENABLED
        and mutant_accepts
    )


def _mutant_ignore_chrono_anchor() -> bool:
    state, proposal, grant, engine = _transition_fixture()
    outcome = engine.execute(state=state, proposal=proposal, grant=grant)
    full = ChronoChain.genesis(state).append_outcome(outcome)
    prefix = ChronoChain.genesis(state)
    production, _ = prefix.verify(
        expected_length=len(full.events),
        expected_head_event_digest=full.head_event.digest,
        expected_head_witness_digest=full.head_witness.digest,
    )
    mutant, _ = prefix.verify()
    return (not production) and mutant


def _mutant_count_echo_bindings() -> bool:
    state = _echo_state()
    production_count = len(state.independent_support_sources("echo-claim"))
    mutant_count = len(state.supporting_evidence("echo-claim"))
    return production_count < 2 <= mutant_count


_MUTANTS: tuple[tuple[str, Callable[[], bool]], ...] = (
    ("scalar_maturity_collapse", _mutant_scalar_maturity),
    ("authority_any_of", _mutant_authority_any_of),
    ("enable_t4", _mutant_enable_t4),
    ("ignore_chrono_anchor", _mutant_ignore_chrono_anchor),
    ("count_echo_bindings", _mutant_count_echo_bindings),
)


def check_modeled_mutants_killed() -> dict[str, object]:
    results = {name: bool(mutant()) for name, mutant in _MUTANTS}
    killed = sum(1 for value in results.values() if value)
    return _check(
        "modeled_mutants_killed",
        killed == len(results),
        f"killed={killed}/{len(results)};" + ",".join(f"{name}={value}" for name, value in results.items()),
    )


_CHECKS: tuple[Callable[[], dict[str, object]], ...] = (
    check_canonical_fail_closed,
    check_maturity_partial_order,
    check_authority_nonamplification,
    check_transition_atomicity_and_disabled_families,
    check_chrono_tamper_and_anchor_boundary,
    check_kbi_echo_and_contradiction_containment,
    check_registry_runtime_parity,
    check_public_claim_surface,
    check_modeled_mutants_killed,
)


def qualification_verify() -> dict[str, object]:
    checks: list[dict[str, object]] = []
    for check in _CHECKS:
        try:
            checks.append(check())
        except Exception as exc:  # fail closed at the aggregate boundary
            checks.append(_check(check.__name__, False, f"unexpected_exception={type(exc).__name__}:{exc}"))
    return {
        "claim_boundary": CLAIM_BOUNDARY,
        "checks": checks,
        "pass": all(bool(check["pass"]) for check in checks),
        "scope": "G8 adversarial constitutional qualification over G0-G7",
    }
