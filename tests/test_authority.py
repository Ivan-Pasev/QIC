from __future__ import annotations

import json
from pathlib import Path

import pytest

from qic.core import canonical_text, digest_hex
from qic.core.authority import AuthorityDomain, AuthorityGrant, AuthorityRequirement, GrantState


ROOT = Path(__file__).parents[1]


def grant(**overrides: object) -> AuthorityGrant:
    values = {
        "grant_id": "grant-parent",
        "subject": "hermes",
        "issuer": "qic.root",
        "domains": frozenset({AuthorityDomain.COMPUTATIONAL}),
        "capabilities": frozenset({"mission.plan", "processor.submit"}),
        "resources": frozenset({"processor.omnius", "state.derived"}),
    }
    values.update(overrides)
    return AuthorityGrant(**values)  # type: ignore[arg-type]


def test_computational_authority_does_not_imply_other_domains() -> None:
    parent = grant()
    assert parent.satisfies(AuthorityRequirement(domains=frozenset({AuthorityDomain.COMPUTATIONAL})))
    assert not parent.satisfies(AuthorityRequirement(domains=frozenset({AuthorityDomain.EPISTEMIC})))
    assert not parent.satisfies(AuthorityRequirement(domains=frozenset({AuthorityDomain.PHYSICAL})))
    assert not parent.satisfies(AuthorityRequirement(domains=frozenset({AuthorityDomain.EVOLUTION})))


def test_delegation_can_reduce_but_not_amplify_authority() -> None:
    parent = grant()
    reduced = AuthorityGrant(
        grant_id="grant-child",
        subject="worker",
        issuer="hermes",
        parent_grant_id=parent.grant_id,
        domains=frozenset({AuthorityDomain.COMPUTATIONAL}),
        capabilities=frozenset({"processor.submit"}),
        resources=frozenset({"processor.omnius"}),
    )
    amplified_domain = AuthorityGrant(
        grant_id="grant-bad-domain",
        subject="worker",
        issuer="hermes",
        parent_grant_id=parent.grant_id,
        domains=frozenset({AuthorityDomain.COMPUTATIONAL, AuthorityDomain.EPISTEMIC}),
        capabilities=frozenset({"processor.submit"}),
        resources=frozenset({"processor.omnius"}),
    )
    amplified_capability = AuthorityGrant(
        grant_id="grant-bad-cap",
        subject="worker",
        issuer="hermes",
        parent_grant_id=parent.grant_id,
        domains=frozenset({AuthorityDomain.COMPUTATIONAL}),
        capabilities=frozenset({"processor.submit", "claim.promote"}),
        resources=frozenset({"processor.omnius"}),
    )
    amplified_resource = AuthorityGrant(
        grant_id="grant-bad-resource",
        subject="worker",
        issuer="hermes",
        parent_grant_id=parent.grant_id,
        domains=frozenset({AuthorityDomain.COMPUTATIONAL}),
        capabilities=frozenset({"processor.submit"}),
        resources=frozenset({"processor.omnius", "state.kbi"}),
    )
    assert parent.can_delegate(reduced)
    assert not parent.can_delegate(amplified_domain)
    assert not parent.can_delegate(amplified_capability)
    assert not parent.can_delegate(amplified_resource)


def test_delegation_requires_direct_lineage_and_subject_as_issuer() -> None:
    parent = grant()
    wrong_issuer = AuthorityGrant(
        grant_id="child",
        subject="worker",
        issuer="someone.else",
        parent_grant_id=parent.grant_id,
        domains=parent.domains,
        capabilities=parent.capabilities,
        resources=parent.resources,
    )
    wrong_parent = AuthorityGrant(
        grant_id="child2",
        subject="worker",
        issuer=parent.subject,
        parent_grant_id="different-parent",
        domains=parent.domains,
        capabilities=parent.capabilities,
        resources=parent.resources,
    )
    assert not parent.can_delegate(wrong_issuer)
    assert not parent.can_delegate(wrong_parent)


def test_revoked_grant_fails_closed_for_requirements_and_delegation() -> None:
    parent = grant().revoked_copy()
    requirement = AuthorityRequirement(
        domains=frozenset({AuthorityDomain.COMPUTATIONAL}),
        capabilities=frozenset({"mission.plan"}),
        resources=frozenset({"state.derived"}),
    )
    child = AuthorityGrant(
        grant_id="child",
        subject="worker",
        issuer="hermes",
        parent_grant_id=parent.grant_id,
        domains=frozenset({AuthorityDomain.COMPUTATIONAL}),
    )
    assert parent.state is GrantState.REVOKED
    assert not parent.satisfies(requirement)
    assert not parent.can_delegate(child)


def test_wildcards_and_invalid_tokens_are_rejected() -> None:
    with pytest.raises(ValueError):
        AuthorityRequirement(capabilities=frozenset({"*"}))
    with pytest.raises(ValueError):
        AuthorityRequirement(resources=frozenset({"State KBI"}))


def test_domain_and_scope_types_fail_closed() -> None:
    with pytest.raises(TypeError):
        AuthorityRequirement(domains=frozenset({"A_C"}))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        AuthorityRequirement(capabilities={"mission.plan"})  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        grant(domains=frozenset({"A_C"}))
    with pytest.raises(TypeError):
        grant(state="ACTIVE")


def test_identity_and_parent_lineage_identifiers_fail_closed() -> None:
    with pytest.raises(ValueError):
        grant(grant_id="")
    with pytest.raises(ValueError):
        grant(subject="bad\x00subject")
    with pytest.raises(ValueError):
        grant(parent_grant_id="")


def test_authority_registry_matches_runtime_domains() -> None:
    payload = json.loads((ROOT / "registry" / "authority_domains.json").read_text(encoding="utf-8"))
    assert [(item["name"], item["id"]) for item in payload["domains"]] == [
        (domain.name, domain.value) for domain in AuthorityDomain
    ]


def test_authority_schema_domain_and_state_parity() -> None:
    payload = json.loads((ROOT / "schemas" / "authority-grant.schema.json").read_text(encoding="utf-8"))
    assert payload["properties"]["domains"]["items"]["enum"] == [domain.value for domain in AuthorityDomain]
    assert payload["properties"]["state"]["enum"] == [state.value for state in GrantState]


def test_authority_grant_golden_vector() -> None:
    payload = json.loads((Path(__file__).parent / "vectors" / "authority_grant_v1.json").read_text(encoding="utf-8"))
    spec = payload["grant"]
    value = AuthorityGrant(
        grant_id=spec["grant_id"],
        subject=spec["subject"],
        issuer=spec["issuer"],
        domains=frozenset(AuthorityDomain(item) for item in spec["domains"]),
        capabilities=frozenset(spec["capabilities"]),
        resources=frozenset(spec["resources"]),
        state=GrantState(spec["state"]),
        parent_grant_id=spec["parent_grant_id"],
    )
    assert canonical_text(value) == payload["canonical"]
    assert digest_hex(value, domain=payload["digest_domain"]) == payload["sha256"]
