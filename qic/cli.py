"""QIC genesis command-line inspection and structural verification surface."""

from __future__ import annotations

import argparse
import json
from importlib.metadata import PackageNotFoundError, version
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
    KBIContext,
    KBIExecutor,
    PRIME_LAWS,
    ROOT_ONTOLOGY,
    StateSnapshot,
    TransitionEngine,
    TransitionFamily,
    TransitionProposal,
    TransitionSpec,
)
from .core.authority import GrantState
from .core.kbi import EvidenceClass as RuntimeEvidenceClass
from .core.transition import ENABLED_FAMILIES, FAMILY_AUTHORITY, TransitionFailure


EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2
_CLAIM_BOUNDARY = (
    "QIC verification establishes only declared structural properties; it does not "
    "certify semantic truth, production security, formal correctness, physical "
    "safety, legal compliance, or deployment readiness."
)


def _version() -> str:
    try:
        return version("qic-core")
    except PackageNotFoundError:
        return "0+uninstalled"


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _emit(payload: object, *, json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return
    if isinstance(payload, dict):
        for key in sorted(payload):
            print(f"{key}: {payload[key]}")
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            print(item)
    else:
        print(payload)


def _result(name: str, passed: bool, detail: str) -> dict[str, object]:
    return {"check": name, "detail": detail, "pass": passed}


def verify_canonical() -> dict[str, object]:
    state = StateSnapshot(revision=0, entries=(("counter", "0"),))
    expected = "4b6e70f26ea0336f48e3fbd71afcc5979f08f9c642b088a6777d8c7d16b44198"
    first = state.digest
    second = state.digest
    return _result(
        "canonical",
        first == second == expected,
        f"state_digest={first}",
    )


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_registries() -> dict[str, object]:
    root = _root()
    try:
        transitions = _load_json(root / "registry" / "transitions.json")
        ontology = _load_json(root / "registry" / "root_ontology.json")
        authority = _load_json(root / "registry" / "authority_domains.json")
        kbi = _load_json(root / "registry" / "kbi.json")
    except (OSError, ValueError) as exc:
        return _result("registries", False, f"registry read failed: {exc}")

    assert isinstance(transitions, dict)
    assert isinstance(ontology, dict)
    assert isinstance(authority, dict)
    assert isinstance(kbi, dict)

    transition_rows = {row["id"]: row for row in transitions["transitions"]}
    transition_ok = set(transition_rows) == {item.value for item in TransitionFamily}
    for family in TransitionFamily:
        row = transition_rows.get(family.value, {})
        expected_domain = FAMILY_AUTHORITY[family]
        transition_ok = transition_ok and row.get("authority_domain") == (
            expected_domain.value if expected_domain else None
        )
        transition_ok = transition_ok and (
            (family in ENABLED_FAMILIES and row.get("status", "ENABLED") != "NOT_ENABLED")
            or (family not in ENABLED_FAMILIES and row.get("status") == "NOT_ENABLED")
        )

    ontology_ok = [(row["name"], row["id"]) for row in ontology["classes"]] == [
        (item.name, item.value) for item in ROOT_ONTOLOGY
    ]
    authority_ok = [(row["name"], row["id"]) for row in authority["domains"]] == [
        (item.name, item.value) for item in AuthorityDomain
    ]
    kbi_ok = (
        kbi["claim_statuses"] == [item.value for item in ClaimStatus]
        and kbi["evidence_classes"] == [item.value for item in RuntimeEvidenceClass]
        and kbi["evidence_relations"] == [item.value for item in EvidenceRelation]
    )
    passed = transition_ok and ontology_ok and authority_ok and kbi_ok
    return _result(
        "registries",
        passed,
        f"transition={transition_ok},ontology={ontology_ok},authority={authority_ok},kbi={kbi_ok}",
    )


def _transition_fixture() -> tuple[StateSnapshot, TransitionProposal, AuthorityGrant, TransitionEngine]:
    state = StateSnapshot(revision=0, entries=(("counter", "0"),))
    proposal = TransitionProposal(
        proposal_id="cli-transition-001",
        actor="worker",
        operation="state.increment",
        expected_state_digest=state.digest,
        payload=(("key", "counter"),),
    )
    grant = AuthorityGrant(
        grant_id="cli-grant",
        subject="worker",
        issuer="qic.root",
        domains=frozenset({AuthorityDomain.COMPUTATIONAL}),
        capabilities=frozenset({"state.increment"}),
        resources=frozenset({"state.counter"}),
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

    def increment(current: StateSnapshot, requested: TransitionProposal) -> StateSnapshot | None:
        if requested.get("key") != "counter" or current.get("counter") != "0":
            return None
        return StateSnapshot(revision=current.revision + 1, entries=(("counter", "1"),))

    return state, proposal, grant, TransitionEngine(
        specs=(spec,), rules={"state.increment": increment}
    )


def verify_transition() -> dict[str, object]:
    state, proposal, grant, engine = _transition_fixture()
    outcome = engine.execute(state=state, proposal=proposal, grant=grant)
    physical = TransitionSpec(
        operation="lab.effect",
        family=TransitionFamily.PHYSICAL,
        authority=AuthorityRequirement(
            domains=frozenset({AuthorityDomain.PHYSICAL}),
            capabilities=frozenset({"lab.effect"}),
            resources=frozenset({"lab.reference"}),
        ),
    )
    physical_grant = AuthorityGrant(
        grant_id="physical-grant",
        subject="worker",
        issuer="qic.root",
        domains=frozenset({AuthorityDomain.PHYSICAL}),
        capabilities=frozenset({"lab.effect"}),
        resources=frozenset({"lab.reference"}),
    )

    def forbidden(current: StateSnapshot, requested: TransitionProposal) -> StateSnapshot | None:
        return StateSnapshot(revision=current.revision + 1, entries=(("counter", "99"),))

    blocked = TransitionEngine(specs=(physical,), rules={"lab.effect": forbidden}).execute(
        state=state,
        proposal=TransitionProposal(
            proposal_id="physical-disabled",
            actor="worker",
            operation="lab.effect",
            expected_state_digest=state.digest,
        ),
        grant=physical_grant,
    )
    passed = (
        outcome.accepted
        and outcome.after_state.revision == 1
        and outcome.after_state.get("counter") == "1"
        and not blocked.accepted
        and blocked.failure is TransitionFailure.FAMILY_NOT_ENABLED
        and blocked.after_state is state
    )
    return _result(
        "transition",
        passed,
        f"accepted={outcome.accepted},t4_failure={blocked.failure.value if blocked.failure else None}",
    )


def verify_chrono() -> dict[str, object]:
    state, proposal, grant, engine = _transition_fixture()
    outcome = engine.execute(state=state, proposal=proposal, grant=grant)
    chain = ChronoChain.genesis(state).append_outcome(outcome)
    valid, reason = chain.verify()
    anchored, anchored_reason = ChronoChain.genesis(state).verify(
        expected_length=len(chain.events),
        expected_head_event_digest=chain.head_event.digest,
        expected_head_witness_digest=chain.head_witness.digest,
    )
    passed = valid and not anchored and anchored_reason in {
        "CHAIN_LENGTH_MISMATCH",
        "HEAD_EVENT_DIGEST_MISMATCH",
        "HEAD_WITNESS_DIGEST_MISMATCH",
    } and chain.verifies_outcome(1, outcome)
    return _result(
        "chrono",
        passed,
        f"chain={valid}:{reason},prefix_anchor={anchored}:{anchored_reason}",
    )


def _epistemic_grant(*, authorized: bool = True) -> AuthorityGrant:
    return AuthorityGrant(
        grant_id="cli-kbi-grant" if authorized else "cli-compute-grant",
        subject="curator",
        issuer="qic.root",
        domains=frozenset({
            AuthorityDomain.EPISTEMIC if authorized else AuthorityDomain.COMPUTATIONAL
        }),
        capabilities=frozenset({
            "kbi.claim.assert",
            "kbi.evidence.add",
            "kbi.evidence.bind",
            "kbi.claim.promote",
        }),
        resources=frozenset({"state.kbi"}),
        state=GrantState.ACTIVE,
    )


def verify_kbi() -> dict[str, object]:
    executor = KBIExecutor()
    context = KBIContext.genesis()
    asserted = executor.assert_claim(
        context,
        ClaimRecord(
            claim_id="claim-cli",
            statement="CLI reference claim",
            origin_source_id="source.origin",
        ),
        actor="curator",
        grant=_epistemic_grant(),
        proposal_id="cli-claim-assert",
    )
    added = executor.add_evidence(
        asserted.context,
        EvidenceRecord(
            evidence_id="e-cli",
            evidence_class=EvidenceClass.OBSERVED,
            source_id="source.independent",
            artifact_digest="artifact-cli",
        ),
        actor="curator",
        grant=_epistemic_grant(),
        proposal_id="cli-evidence-add",
    )
    bound = executor.bind_evidence(
        added.context,
        EvidenceBinding(
            binding_id="b-cli",
            claim_id="claim-cli",
            evidence_id="e-cli",
            relation=EvidenceRelation.SUPPORTS,
        ),
        actor="curator",
        grant=_epistemic_grant(),
        proposal_id="cli-evidence-bind",
    )
    status_before = bound.context.kbi.claim("claim-cli").status  # type: ignore[union-attr]
    promoted = executor.promote_claim(
        bound.context,
        "claim-cli",
        ClaimStatus.SUPPORTED,
        actor="curator",
        grant=_epistemic_grant(),
        proposal_id="cli-promote",
    )
    denied = executor.promote_claim(
        bound.context,
        "claim-cli",
        ClaimStatus.SUPPORTED,
        actor="curator",
        grant=_epistemic_grant(authorized=False),
        proposal_id="cli-denied-promote",
    )
    passed = (
        asserted.outcome.accepted
        and added.outcome.accepted
        and bound.outcome.accepted
        and status_before is ClaimStatus.ASSERTED
        and promoted.outcome.accepted
        and promoted.context.kbi.claim("claim-cli").status is ClaimStatus.SUPPORTED  # type: ignore[union-attr]
        and not denied.outcome.accepted
        and denied.outcome.failure is TransitionFailure.AUTHORITY_DENIED
        and denied.context.kbi is bound.context.kbi
        and denied.context.runtime_state is bound.context.runtime_state
        and denied.context.chrono.verifies_outcome(
            len(denied.context.chrono.events) - 1, denied.outcome
        )
    )
    return _result(
        "kbi",
        passed,
        f"binding_status={status_before.value},promotion={promoted.outcome.accepted},unauthorized={denied.outcome.failure.value if denied.outcome.failure else None}",
    )


_VERIFIERS: dict[str, Callable[[], dict[str, object]]] = {
    "canonical": verify_canonical,
    "registries": verify_registries,
    "transition": verify_transition,
    "chrono": verify_chrono,
    "kbi": verify_kbi,
}


def aggregate_verify() -> dict[str, object]:
    checks = [verifier() for verifier in _VERIFIERS.values()]
    return {
        "claim_boundary": _CLAIM_BOUNDARY,
        "checks": checks,
        "pass": all(bool(check["pass"]) for check in checks),
        "scope": "G0-G7 structural verification",
    }


def _registry_payload(name: str) -> object:
    path_map = {
        "transitions": "transitions.json",
        "ontology": "root_ontology.json",
        "authority": "authority_domains.json",
        "kbi": "kbi.json",
    }
    return _load_json(_root() / "registry" / path_map[name])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qic", description="QIC genesis structural verifier")
    parser.add_argument("--json", action="store_true", dest="json_mode")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("version")
    sub.add_parser("status")
    sub.add_parser("constitution")
    registry = sub.add_parser("registry")
    registry.add_argument("name", choices=("transitions", "ontology", "authority", "kbi"))
    verify = sub.add_parser("verify")
    verify.add_argument("target", nargs="?", choices=tuple(_VERIFIERS), default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    json_mode = bool(args.json_mode)

    if args.command == "version":
        _emit({"package": "qic-core", "version": _version()}, json_mode=json_mode)
        return EXIT_PASS
    if args.command == "status":
        payload = {
            "active_implementation": "G7",
            "claim_boundary": _CLAIM_BOUNDARY,
            "implemented_through": "G6",
            "transition_families_enabled": [item.value for item in sorted(ENABLED_FAMILIES, key=lambda x: x.value)],
            "transition_families_not_enabled": ["T4", "T5"],
        }
        _emit(payload, json_mode=json_mode)
        return EXIT_PASS
    if args.command == "constitution":
        _emit({"prime_laws": list(PRIME_LAWS)}, json_mode=json_mode)
        return EXIT_PASS
    if args.command == "registry":
        try:
            payload = _registry_payload(args.name)
        except (OSError, ValueError) as exc:
            _emit({"error": str(exc), "pass": False}, json_mode=json_mode)
            return EXIT_FAIL
        _emit(payload, json_mode=json_mode)
        return EXIT_PASS
    if args.command == "verify":
        payload = aggregate_verify() if args.target is None else _VERIFIERS[args.target]()
        _emit(payload, json_mode=json_mode)
        return EXIT_PASS if bool(payload["pass"]) else EXIT_FAIL
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
