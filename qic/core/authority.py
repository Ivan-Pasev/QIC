"""Scoped, non-amplifying authority model for QIC.

G3 models authority state and static authorization requirements. It does not
execute transitions or mutate KBI/runtime state.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


_TOKEN_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._:-][a-z0-9]+)*$")


class AuthorityDomain(str, Enum):
    EPISTEMIC = "A_E"
    COMPUTATIONAL = "A_C"
    PHYSICAL = "A_P"
    EVOLUTION = "A_X"


class GrantState(str, Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


def _validated_tokens(values: frozenset[str], *, kind: str) -> frozenset[str]:
    for value in values:
        if not value or value == "*" or not _TOKEN_RE.fullmatch(value):
            raise ValueError(f"invalid {kind} identifier: {value!r}")
    return values


@dataclass(frozen=True, slots=True)
class AuthorityRequirement:
    """Exact authority required for a future operation."""

    domains: frozenset[AuthorityDomain] = frozenset()
    capabilities: frozenset[str] = frozenset()
    resources: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        _validated_tokens(self.capabilities, kind="capability")
        _validated_tokens(self.resources, kind="resource")


@dataclass(frozen=True, slots=True)
class AuthorityGrant:
    """Immutable scoped authority description.

    A grant is descriptive constitutional state. Possession of this Python
    object is not itself a runtime authorization token or side effect.
    """

    grant_id: str
    subject: str
    issuer: str
    domains: frozenset[AuthorityDomain] = frozenset()
    capabilities: frozenset[str] = frozenset()
    resources: frozenset[str] = frozenset()
    state: GrantState = GrantState.ACTIVE
    parent_grant_id: str | None = None

    def __post_init__(self) -> None:
        for field_name, value in (
            ("grant_id", self.grant_id),
            ("subject", self.subject),
            ("issuer", self.issuer),
        ):
            if not value or "\x00" in value:
                raise ValueError(f"{field_name} must be non-empty and contain no NUL")
        _validated_tokens(self.capabilities, kind="capability")
        _validated_tokens(self.resources, kind="resource")

    @property
    def active(self) -> bool:
        return self.state is GrantState.ACTIVE

    def satisfies(self, requirement: AuthorityRequirement) -> bool:
        """Component-wise static authorization check."""

        return (
            self.active
            and requirement.domains.issubset(self.domains)
            and requirement.capabilities.issubset(self.capabilities)
            and requirement.resources.issubset(self.resources)
        )

    def can_delegate(self, child: "AuthorityGrant") -> bool:
        """Return whether *child* is a non-amplifying direct delegation.

        G3 requires the child issuer to equal the parent subject and the child
        to reference this grant explicitly. Authority may be preserved or
        reduced, never expanded.
        """

        return (
            self.active
            and child.active
            and child.issuer == self.subject
            and child.parent_grant_id == self.grant_id
            and child.domains.issubset(self.domains)
            and child.capabilities.issubset(self.capabilities)
            and child.resources.issubset(self.resources)
        )

    def revoked_copy(self) -> "AuthorityGrant":
        """Return a revoked immutable successor representation."""

        return AuthorityGrant(
            grant_id=self.grant_id,
            subject=self.subject,
            issuer=self.issuer,
            domains=self.domains,
            capabilities=self.capabilities,
            resources=self.resources,
            state=GrantState.REVOKED,
            parent_grant_id=self.parent_grant_id,
        )
