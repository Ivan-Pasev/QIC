"""Minimal deterministic transition and invariant kernel for QIC G4.

The engine binds a proposal to the current immutable state and a current G3
authority grant, evaluates a pure operation rule, then evaluates invariants.
Any rejection returns the original state object unchanged. T4/T5 are disabled.

G4 does not persist state, append Chrono events, mutate KBI, sign witnesses, or
create physical effects.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Final

from .authority import AuthorityDomain, AuthorityGrant, AuthorityRequirement
from .digest import digest_hex


_OPERATION_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._:-][a-z0-9]+)*$")


class TransitionFamily(str, Enum):
    OBSERVATION = "T0"
    DERIVATION = "T1"
    EPISTEMIC = "T2"
    COMPUTATIONAL = "T3"
    PHYSICAL = "T4"
    EVOLUTIONARY = "T5"


FAMILY_AUTHORITY: Final[dict[TransitionFamily, AuthorityDomain | None]] = {
    TransitionFamily.OBSERVATION: None,
    TransitionFamily.DERIVATION: AuthorityDomain.COMPUTATIONAL,
    TransitionFamily.EPISTEMIC: AuthorityDomain.EPISTEMIC,
    TransitionFamily.COMPUTATIONAL: AuthorityDomain.COMPUTATIONAL,
    TransitionFamily.PHYSICAL: AuthorityDomain.PHYSICAL,
    TransitionFamily.EVOLUTIONARY: AuthorityDomain.EVOLUTION,
}

ENABLED_FAMILIES: Final[frozenset[TransitionFamily]] = frozenset(
    {
        TransitionFamily.OBSERVATION,
        TransitionFamily.DERIVATION,
        TransitionFamily.EPISTEMIC,
        TransitionFamily.COMPUTATIONAL,
    }
)


class TransitionFailure(str, Enum):
    UNKNOWN_OPERATION = "UNKNOWN_OPERATION"
    FAMILY_NOT_ENABLED = "FAMILY_NOT_ENABLED"
    STALE_STATE = "STALE_STATE"
    SUBJECT_MISMATCH = "SUBJECT_MISMATCH"
    AUTHORITY_DENIED = "AUTHORITY_DENIED"
    RULE_REJECTED = "RULE_REJECTED"
    INVARIANT_FAILED = "INVARIANT_FAILED"


@dataclass(frozen=True, slots=True)
class StateSnapshot:
    """Small immutable G4 reference state.

    Values are strings deliberately; richer typed state belongs to later slices.
    Entries must be sorted by key and unique so one logical state has one
    constructor representation before canonicalization.
    """

    revision: int = 0
    entries: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if type(self.revision) is not int or self.revision < 0:
            raise ValueError("revision must be a non-negative int")
        if not isinstance(self.entries, tuple):
            raise TypeError("entries must be a tuple")
        keys: list[str] = []
        for item in self.entries:
            if not isinstance(item, tuple) or len(item) != 2:
                raise TypeError("each state entry must be a (str, str) tuple")
            key, value = item
            if not isinstance(key, str) or not isinstance(value, str):
                raise TypeError("state keys and values must be strings")
            if not key or "\x00" in key or "\x00" in value:
                raise ValueError("state keys must be non-empty and state text cannot contain NUL")
            keys.append(key)
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("state entries must have unique keys in sorted order")

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="state.snapshot")

    def get(self, key: str) -> str | None:
        for candidate, value in self.entries:
            if candidate == key:
                return value
        return None


@dataclass(frozen=True, slots=True)
class TransitionSpec:
    operation: str
    family: TransitionFamily
    authority: AuthorityRequirement = AuthorityRequirement()
    invariant_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_operation(self.operation)
        if not isinstance(self.family, TransitionFamily):
            raise TypeError("family must be a TransitionFamily")
        if not isinstance(self.authority, AuthorityRequirement):
            raise TypeError("authority must be an AuthorityRequirement")
        if not isinstance(self.invariant_ids, tuple) or not all(
            isinstance(item, str) and item for item in self.invariant_ids
        ):
            raise TypeError("invariant_ids must be a tuple of non-empty strings")
        required_domain = FAMILY_AUTHORITY[self.family]
        if required_domain is not None and required_domain not in self.authority.domains:
            raise ValueError(
                f"{self.family.value} transition requires authority domain {required_domain.value}"
            )


@dataclass(frozen=True, slots=True)
class TransitionProposal:
    proposal_id: str
    actor: str
    operation: str
    expected_state_digest: str
    payload: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("proposal_id", self.proposal_id),
            ("actor", self.actor),
            ("expected_state_digest", self.expected_state_digest),
        ):
            if not isinstance(value, str) or not value or "\x00" in value:
                raise ValueError(f"{name} must be a non-empty NUL-free string")
        _validate_operation(self.operation)
        if not isinstance(self.payload, tuple):
            raise TypeError("payload must be a tuple")
        keys: list[str] = []
        for item in self.payload:
            if not isinstance(item, tuple) or len(item) != 2:
                raise TypeError("each payload entry must be a (str, str) tuple")
            key, value = item
            if not isinstance(key, str) or not isinstance(value, str):
                raise TypeError("payload keys and values must be strings")
            if not key or "\x00" in key or "\x00" in value:
                raise ValueError("payload keys must be non-empty and payload text cannot contain NUL")
            keys.append(key)
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("payload entries must have unique keys in sorted order")

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="transition.proposal")

    def get(self, key: str) -> str | None:
        for candidate, value in self.payload:
            if candidate == key:
                return value
        return None


@dataclass(frozen=True, slots=True)
class TransitionOutcome:
    accepted: bool
    failure: TransitionFailure | None
    proposal_digest: str
    before_state: StateSnapshot
    after_state: StateSnapshot
    failed_invariant: str | None = None

    def __post_init__(self) -> None:
        if type(self.accepted) is not bool:
            raise TypeError("accepted must be bool")
        if self.accepted and self.failure is not None:
            raise ValueError("accepted outcome cannot carry a failure")
        if not self.accepted and self.failure is None:
            raise ValueError("rejected outcome must carry a failure")
        if self.accepted and self.failed_invariant is not None:
            raise ValueError("accepted outcome cannot carry failed_invariant")

    @property
    def before_digest(self) -> str:
        return self.before_state.digest

    @property
    def after_digest(self) -> str:
        return self.after_state.digest

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="transition.outcome")


TransitionRule = Callable[[StateSnapshot, TransitionProposal], StateSnapshot | None]
Invariant = Callable[[StateSnapshot], bool]


class TransitionEngine:
    """Pure reference transition engine for the G4 compute profile."""

    def __init__(
        self,
        *,
        specs: tuple[TransitionSpec, ...],
        rules: dict[str, TransitionRule],
        invariants: dict[str, Invariant] | None = None,
        global_invariant_ids: tuple[str, ...] = (),
    ) -> None:
        if not isinstance(specs, tuple):
            raise TypeError("specs must be a tuple")
        self._specs = {spec.operation: spec for spec in specs}
        if len(self._specs) != len(specs):
            raise ValueError("transition operation names must be unique")
        if set(rules) != set(self._specs):
            raise ValueError("rules must exist for exactly the declared operations")
        self._rules = dict(rules)
        self._invariants = dict(invariants or {})
        if not isinstance(global_invariant_ids, tuple):
            raise TypeError("global_invariant_ids must be a tuple")
        for invariant_id in global_invariant_ids:
            if invariant_id not in self._invariants:
                raise ValueError(f"unknown global invariant: {invariant_id}")
        for spec in specs:
            for invariant_id in spec.invariant_ids:
                if invariant_id not in self._invariants:
                    raise ValueError(
                        f"unknown invariant {invariant_id!r} for operation {spec.operation!r}"
                    )
        self._global_invariant_ids = global_invariant_ids

    def execute(
        self,
        *,
        state: StateSnapshot,
        proposal: TransitionProposal,
        grant: AuthorityGrant,
    ) -> TransitionOutcome:
        if not isinstance(state, StateSnapshot):
            raise TypeError("state must be a StateSnapshot")
        if not isinstance(proposal, TransitionProposal):
            raise TypeError("proposal must be a TransitionProposal")
        if not isinstance(grant, AuthorityGrant):
            raise TypeError("grant must be an AuthorityGrant")

        spec = self._specs.get(proposal.operation)
        if spec is None:
            return _reject(TransitionFailure.UNKNOWN_OPERATION, state, proposal)
        if spec.family not in ENABLED_FAMILIES:
            return _reject(TransitionFailure.FAMILY_NOT_ENABLED, state, proposal)
        if proposal.expected_state_digest != state.digest:
            return _reject(TransitionFailure.STALE_STATE, state, proposal)
        if grant.subject != proposal.actor:
            return _reject(TransitionFailure.SUBJECT_MISMATCH, state, proposal)
        if not grant.satisfies(spec.authority):
            return _reject(TransitionFailure.AUTHORITY_DENIED, state, proposal)

        candidate = self._rules[proposal.operation](state, proposal)
        if candidate is None:
            return _reject(TransitionFailure.RULE_REJECTED, state, proposal)
        if not isinstance(candidate, StateSnapshot):
            raise TypeError("transition rules must return StateSnapshot or None")

        for invariant_id in (*self._global_invariant_ids, *spec.invariant_ids):
            invariant = self._invariants[invariant_id]
            if not invariant(candidate):
                return _reject(
                    TransitionFailure.INVARIANT_FAILED,
                    state,
                    proposal,
                    failed_invariant=invariant_id,
                )

        return TransitionOutcome(
            accepted=True,
            failure=None,
            proposal_digest=proposal.digest,
            before_state=state,
            after_state=candidate,
        )


def _validate_operation(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("operation must be a string")
    if not _OPERATION_RE.fullmatch(value):
        raise ValueError(f"invalid transition operation identifier: {value!r}")
    return value


def _reject(
    failure: TransitionFailure,
    state: StateSnapshot,
    proposal: TransitionProposal,
    *,
    failed_invariant: str | None = None,
) -> TransitionOutcome:
    return TransitionOutcome(
        accepted=False,
        failure=failure,
        proposal_digest=proposal.digest,
        before_state=state,
        after_state=state,
        failed_invariant=failed_invariant,
    )
