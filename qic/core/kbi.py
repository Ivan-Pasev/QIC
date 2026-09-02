"""Minimal Knowledge Base Infrastructure for QIC G6.

KBI objects are immutable structural records. Candidate transformations are pure
and non-authoritative. `KBIExecutor` is the authoritative reference path: it
projects a candidate KBI root into a G4 epistemic transition, enforces current
A_E authority, and records accepted/rejected outcomes in the G5 Chrono chain.

Evidence binding and status metadata do not establish semantic truth.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .authority import AuthorityDomain, AuthorityGrant, AuthorityRequirement
from .chrono import ChronoChain
from .digest import digest_hex
from .transition import (
    StateSnapshot,
    TransitionEngine,
    TransitionFamily,
    TransitionOutcome,
    TransitionProposal,
    TransitionSpec,
)


class ClaimStatus(str, Enum):
    ASSERTED = "ASSERTED"
    SUPPORTED = "SUPPORTED"
    CORROBORATED = "CORROBORATED"
    VALIDATED = "VALIDATED"
    CANONICAL = "CANONICAL"
    CONTESTED = "CONTESTED"
    CONTRADICTED = "CONTRADICTED"
    SUPERSEDED = "SUPERSEDED"
    QUARANTINED = "QUARANTINED"


class EvidenceClass(str, Enum):
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    SIMULATED = "SIMULATED"
    FORMALLY_PROVED = "FORMALLY_PROVED"
    ATTESTED = "ATTESTED"
    REMOTE_OBSERVED = "REMOTE_OBSERVED"


class EvidenceRelation(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"


def _text(value: str, *, field: str) -> str:
    if type(value) is not str or not value or "\x00" in value:
        raise ValueError(f"{field} must be a non-empty NUL-free string")
    return value


def _refs(values: tuple[str, ...], *, field: str) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeError(f"{field} must be an immutable tuple")
    if not all(type(item) is str and item and "\x00" not in item for item in values):
        raise ValueError(f"{field} must contain non-empty NUL-free strings")
    if values != tuple(sorted(values)) or len(values) != len(set(values)):
        raise ValueError(f"{field} must be unique and sorted")
    return values


@dataclass(frozen=True, slots=True)
class ClaimRecord:
    claim_id: str
    statement: str
    origin_source_id: str
    status: ClaimStatus = ClaimStatus.ASSERTED
    provenance_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.claim_id, field="claim_id")
        _text(self.statement, field="statement")
        _text(self.origin_source_id, field="origin_source_id")
        if type(self.status) is not ClaimStatus:
            raise TypeError("status must be ClaimStatus")
        _refs(self.provenance_refs, field="provenance_refs")

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="kbi.claim")


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    evidence_id: str
    evidence_class: EvidenceClass
    source_id: str
    artifact_digest: str
    provenance_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.evidence_id, field="evidence_id")
        if type(self.evidence_class) is not EvidenceClass:
            raise TypeError("evidence_class must be EvidenceClass")
        _text(self.source_id, field="source_id")
        _text(self.artifact_digest, field="artifact_digest")
        _refs(self.provenance_refs, field="provenance_refs")

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="kbi.evidence")


@dataclass(frozen=True, slots=True)
class EvidenceBinding:
    binding_id: str
    claim_id: str
    evidence_id: str
    relation: EvidenceRelation

    def __post_init__(self) -> None:
        _text(self.binding_id, field="binding_id")
        _text(self.claim_id, field="claim_id")
        _text(self.evidence_id, field="evidence_id")
        if type(self.relation) is not EvidenceRelation:
            raise TypeError("relation must be EvidenceRelation")

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="kbi.binding")


@dataclass(frozen=True, slots=True)
class ContradictionRecord:
    contradiction_id: str
    target_claim_id: str
    counter_claim_id: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.contradiction_id, field="contradiction_id")
        _text(self.target_claim_id, field="target_claim_id")
        _text(self.counter_claim_id, field="counter_claim_id")
        if self.target_claim_id == self.counter_claim_id:
            raise ValueError("a claim cannot contradict itself")
        _refs(self.evidence_refs, field="evidence_refs")

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="kbi.contradiction")


def _unique_sorted(records: tuple[object, ...], *, id_attr: str, field: str) -> None:
    if type(records) is not tuple:
        raise TypeError(f"{field} must be an immutable tuple")
    identifiers = []
    for record in records:
        identifier = getattr(record, id_attr, None)
        if type(identifier) is not str:
            raise TypeError(f"{field} contains an invalid record")
        identifiers.append(identifier)
    if identifiers != sorted(identifiers) or len(identifiers) != len(set(identifiers)):
        raise ValueError(f"{field} must be sorted by unique {id_attr}")


@dataclass(frozen=True, slots=True)
class KBIState:
    claims: tuple[ClaimRecord, ...] = ()
    evidence: tuple[EvidenceRecord, ...] = ()
    bindings: tuple[EvidenceBinding, ...] = ()
    contradictions: tuple[ContradictionRecord, ...] = ()

    def __post_init__(self) -> None:
        if not all(type(item) is ClaimRecord for item in self.claims):
            raise TypeError("claims must contain ClaimRecord values exactly")
        if not all(type(item) is EvidenceRecord for item in self.evidence):
            raise TypeError("evidence must contain EvidenceRecord values exactly")
        if not all(type(item) is EvidenceBinding for item in self.bindings):
            raise TypeError("bindings must contain EvidenceBinding values exactly")
        if not all(type(item) is ContradictionRecord for item in self.contradictions):
            raise TypeError("contradictions must contain ContradictionRecord values exactly")
        _unique_sorted(self.claims, id_attr="claim_id", field="claims")
        _unique_sorted(self.evidence, id_attr="evidence_id", field="evidence")
        _unique_sorted(self.bindings, id_attr="binding_id", field="bindings")
        _unique_sorted(
            self.contradictions,
            id_attr="contradiction_id",
            field="contradictions",
        )

        claim_ids = {item.claim_id for item in self.claims}
        evidence_ids = {item.evidence_id for item in self.evidence}
        seen_binding_edges: set[tuple[str, str, EvidenceRelation]] = set()
        for binding in self.bindings:
            if binding.claim_id not in claim_ids:
                raise ValueError(f"binding references unknown claim: {binding.claim_id}")
            if binding.evidence_id not in evidence_ids:
                raise ValueError(f"binding references unknown evidence: {binding.evidence_id}")
            edge = (binding.claim_id, binding.evidence_id, binding.relation)
            if edge in seen_binding_edges:
                raise ValueError("duplicate logical evidence binding is not allowed")
            seen_binding_edges.add(edge)
        for contradiction in self.contradictions:
            if contradiction.target_claim_id not in claim_ids:
                raise ValueError("contradiction target claim is unknown")
            if contradiction.counter_claim_id not in claim_ids:
                raise ValueError("contradiction counter claim is unknown")
            if not set(contradiction.evidence_refs).issubset(evidence_ids):
                raise ValueError("contradiction references unknown evidence")

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="kbi.state")

    def runtime_snapshot(self, *, revision: int) -> StateSnapshot:
        return StateSnapshot(revision=revision, entries=(("kbi.root", self.digest),))

    def claim(self, claim_id: str) -> ClaimRecord | None:
        return next((item for item in self.claims if item.claim_id == claim_id), None)

    def evidence_record(self, evidence_id: str) -> EvidenceRecord | None:
        return next((item for item in self.evidence if item.evidence_id == evidence_id), None)

    def supporting_evidence(self, claim_id: str) -> tuple[EvidenceRecord, ...]:
        evidence_by_id = {item.evidence_id: item for item in self.evidence}
        records = [
            evidence_by_id[binding.evidence_id]
            for binding in self.bindings
            if binding.claim_id == claim_id
            and binding.relation is EvidenceRelation.SUPPORTS
        ]
        return tuple(sorted(records, key=lambda item: item.evidence_id))

    def independent_support_sources(self, claim_id: str) -> frozenset[str]:
        claim = self.claim(claim_id)
        if claim is None:
            return frozenset()
        return frozenset(
            item.source_id
            for item in self.supporting_evidence(claim_id)
            if item.source_id != claim.origin_source_id
        )

    def has_contradiction(self, claim_id: str) -> bool:
        if any(
            item.target_claim_id == claim_id or item.counter_claim_id == claim_id
            for item in self.contradictions
        ):
            return True
        return any(
            binding.claim_id == claim_id and binding.relation is EvidenceRelation.CONTRADICTS
            for binding in self.bindings
        )

    def candidate_add_claim(self, claim: ClaimRecord) -> "KBIState":
        if type(claim) is not ClaimRecord:
            raise TypeError("claim must be ClaimRecord exactly")
        if claim.status is not ClaimStatus.ASSERTED:
            raise ValueError("new claims must enter KBI as ASSERTED")
        if self.claim(claim.claim_id) is not None:
            raise ValueError("claim_id already exists")
        return replace(self, claims=tuple(sorted((*self.claims, claim), key=lambda item: item.claim_id)))

    def candidate_add_evidence(self, evidence: EvidenceRecord) -> "KBIState":
        if type(evidence) is not EvidenceRecord:
            raise TypeError("evidence must be EvidenceRecord exactly")
        if self.evidence_record(evidence.evidence_id) is not None:
            raise ValueError("evidence_id already exists")
        return replace(
            self,
            evidence=tuple(sorted((*self.evidence, evidence), key=lambda item: item.evidence_id)),
        )

    def candidate_add_binding(self, binding: EvidenceBinding) -> "KBIState":
        if type(binding) is not EvidenceBinding:
            raise TypeError("binding must be EvidenceBinding exactly")
        if any(item.binding_id == binding.binding_id for item in self.bindings):
            raise ValueError("binding_id already exists")
        if self.claim(binding.claim_id) is None:
            raise ValueError("binding claim does not exist")
        if self.evidence_record(binding.evidence_id) is None:
            raise ValueError("binding evidence does not exist")
        logical = (binding.claim_id, binding.evidence_id, binding.relation)
        if any(
            (item.claim_id, item.evidence_id, item.relation) == logical
            for item in self.bindings
        ):
            raise ValueError("duplicate logical evidence binding is not allowed")
        return replace(
            self,
            bindings=tuple(sorted((*self.bindings, binding), key=lambda item: item.binding_id)),
        )

    def candidate_promote(self, claim_id: str, target: ClaimStatus) -> "KBIState":
        if type(target) is not ClaimStatus:
            raise TypeError("target must be ClaimStatus")
        claim = self.claim(claim_id)
        if claim is None:
            raise ValueError("claim does not exist")
        legal_next = {
            ClaimStatus.ASSERTED: ClaimStatus.SUPPORTED,
            ClaimStatus.SUPPORTED: ClaimStatus.CORROBORATED,
            ClaimStatus.CORROBORATED: ClaimStatus.VALIDATED,
            ClaimStatus.VALIDATED: ClaimStatus.CANONICAL,
        }
        if legal_next.get(claim.status) is not target:
            raise ValueError("claim status transition is not a legal forward promotion")
        support = self.supporting_evidence(claim_id)
        if target is ClaimStatus.SUPPORTED and not support:
            raise ValueError("SUPPORTED requires at least one supporting evidence binding")
        if target in {
            ClaimStatus.CORROBORATED,
            ClaimStatus.VALIDATED,
            ClaimStatus.CANONICAL,
        } and len(self.independent_support_sources(claim_id)) < 2:
            raise ValueError("corroboration requires at least two independent support sources")
        if target in {ClaimStatus.VALIDATED, ClaimStatus.CANONICAL} and self.has_contradiction(claim_id):
            raise ValueError("contradicted/contested claim cannot be validated or canonicalized")
        updated = replace(claim, status=target)
        return replace(
            self,
            claims=tuple(updated if item.claim_id == claim_id else item for item in self.claims),
        )

    def candidate_add_contradiction(self, contradiction: ContradictionRecord) -> "KBIState":
        if type(contradiction) is not ContradictionRecord:
            raise TypeError("contradiction must be ContradictionRecord exactly")
        if any(
            item.contradiction_id == contradiction.contradiction_id
            for item in self.contradictions
        ):
            raise ValueError("contradiction_id already exists")
        target = self.claim(contradiction.target_claim_id)
        counter = self.claim(contradiction.counter_claim_id)
        if target is None or counter is None:
            raise ValueError("contradiction claims must already exist")
        if not set(contradiction.evidence_refs).issubset(
            {item.evidence_id for item in self.evidence}
        ):
            raise ValueError("contradiction references unknown evidence")
        target_updated = replace(target, status=ClaimStatus.CONTRADICTED)
        counter_status = (
            counter.status
            if counter.status in {ClaimStatus.CONTRADICTED, ClaimStatus.QUARANTINED}
            else ClaimStatus.CONTESTED
        )
        counter_updated = replace(counter, status=counter_status)
        return replace(
            self,
            claims=tuple(
                target_updated
                if item.claim_id == target.claim_id
                else counter_updated
                if item.claim_id == counter.claim_id
                else item
                for item in self.claims
            ),
            contradictions=tuple(
                sorted(
                    (*self.contradictions, contradiction),
                    key=lambda item: item.contradiction_id,
                )
            ),
        )


@dataclass(frozen=True, slots=True)
class KBIContext:
    kbi: KBIState
    runtime_state: StateSnapshot
    chrono: ChronoChain

    def __post_init__(self) -> None:
        if type(self.kbi) is not KBIState:
            raise TypeError("kbi must be KBIState exactly")
        if type(self.runtime_state) is not StateSnapshot:
            raise TypeError("runtime_state must be StateSnapshot exactly")
        if type(self.chrono) is not ChronoChain:
            raise TypeError("chrono must be ChronoChain exactly")
        if self.runtime_state.get("kbi.root") != self.kbi.digest:
            raise ValueError("runtime state KBI root does not match KBIState")
        if self.chrono.current_state_digest != self.runtime_state.digest:
            raise ValueError("Chrono head does not match runtime state")
        valid, reason = self.chrono.verify()
        if not valid:
            raise ValueError(f"Chrono chain is invalid: {reason}")

    @classmethod
    def genesis(cls, kbi: KBIState | None = None) -> "KBIContext":
        state = kbi or KBIState()
        if type(state) is not KBIState:
            raise TypeError("kbi must be KBIState exactly")
        runtime = state.runtime_snapshot(revision=0)
        return cls(kbi=state, runtime_state=runtime, chrono=ChronoChain.genesis(runtime))


@dataclass(frozen=True, slots=True)
class KBIExecutionResult:
    context: KBIContext
    outcome: TransitionOutcome


_CAPABILITIES = {
    "kbi.claim.assert": "kbi.claim.assert",
    "kbi.evidence.add": "kbi.evidence.add",
    "kbi.evidence.bind": "kbi.evidence.bind",
    "kbi.claim.promote": "kbi.claim.promote",
    "kbi.claim.contradict": "kbi.claim.contradict",
}


class KBIExecutor:
    """Reference authority-gated executor for minimal local KBI operations."""

    resource = "state.kbi"

    def assert_claim(
        self,
        context: KBIContext,
        claim: ClaimRecord,
        *,
        actor: str,
        grant: AuthorityGrant,
        proposal_id: str,
        expected_state_digest: str | None = None,
    ) -> KBIExecutionResult:
        candidate = context.kbi.candidate_add_claim(claim)
        return self._execute_candidate(
            context,
            candidate,
            operation="kbi.claim.assert",
            actor=actor,
            grant=grant,
            proposal_id=proposal_id,
            expected_state_digest=expected_state_digest,
            target_id=claim.claim_id,
        )

    def add_evidence(
        self,
        context: KBIContext,
        evidence: EvidenceRecord,
        *,
        actor: str,
        grant: AuthorityGrant,
        proposal_id: str,
        expected_state_digest: str | None = None,
    ) -> KBIExecutionResult:
        candidate = context.kbi.candidate_add_evidence(evidence)
        return self._execute_candidate(
            context,
            candidate,
            operation="kbi.evidence.add",
            actor=actor,
            grant=grant,
            proposal_id=proposal_id,
            expected_state_digest=expected_state_digest,
            target_id=evidence.evidence_id,
        )

    def bind_evidence(
        self,
        context: KBIContext,
        binding: EvidenceBinding,
        *,
        actor: str,
        grant: AuthorityGrant,
        proposal_id: str,
        expected_state_digest: str | None = None,
    ) -> KBIExecutionResult:
        candidate = context.kbi.candidate_add_binding(binding)
        return self._execute_candidate(
            context,
            candidate,
            operation="kbi.evidence.bind",
            actor=actor,
            grant=grant,
            proposal_id=proposal_id,
            expected_state_digest=expected_state_digest,
            target_id=binding.binding_id,
        )

    def promote_claim(
        self,
        context: KBIContext,
        claim_id: str,
        target: ClaimStatus,
        *,
        actor: str,
        grant: AuthorityGrant,
        proposal_id: str,
        expected_state_digest: str | None = None,
    ) -> KBIExecutionResult:
        candidate = context.kbi.candidate_promote(claim_id, target)
        return self._execute_candidate(
            context,
            candidate,
            operation="kbi.claim.promote",
            actor=actor,
            grant=grant,
            proposal_id=proposal_id,
            expected_state_digest=expected_state_digest,
            target_id=claim_id,
            extra=("target_status", target.value),
        )

    def contradict_claim(
        self,
        context: KBIContext,
        contradiction: ContradictionRecord,
        *,
        actor: str,
        grant: AuthorityGrant,
        proposal_id: str,
        expected_state_digest: str | None = None,
    ) -> KBIExecutionResult:
        candidate = context.kbi.candidate_add_contradiction(contradiction)
        return self._execute_candidate(
            context,
            candidate,
            operation="kbi.claim.contradict",
            actor=actor,
            grant=grant,
            proposal_id=proposal_id,
            expected_state_digest=expected_state_digest,
            target_id=contradiction.target_claim_id,
        )

    def _execute_candidate(
        self,
        context: KBIContext,
        candidate: KBIState,
        *,
        operation: str,
        actor: str,
        grant: AuthorityGrant,
        proposal_id: str,
        expected_state_digest: str | None,
        target_id: str,
        extra: tuple[str, str] | None = None,
    ) -> KBIExecutionResult:
        if type(context) is not KBIContext:
            raise TypeError("context must be KBIContext exactly")
        if type(candidate) is not KBIState:
            raise TypeError("candidate must be KBIState exactly")
        capability = _CAPABILITIES[operation]
        requirement = AuthorityRequirement(
            domains=frozenset({AuthorityDomain.EPISTEMIC}),
            capabilities=frozenset({capability}),
            resources=frozenset({self.resource}),
        )
        spec = TransitionSpec(
            operation=operation,
            family=TransitionFamily.EPISTEMIC,
            authority=requirement,
        )

        payload_items = [
            ("candidate_root", candidate.digest),
            ("target_id", target_id),
        ]
        if extra is not None:
            payload_items.append(extra)
        payload = tuple(sorted(payload_items))
        proposal = TransitionProposal(
            proposal_id=proposal_id,
            actor=actor,
            operation=operation,
            expected_state_digest=expected_state_digest or context.runtime_state.digest,
            payload=payload,
        )

        def commit_candidate_root(
            current: StateSnapshot, requested: TransitionProposal
        ) -> StateSnapshot | None:
            if current.get("kbi.root") != context.kbi.digest:
                return None
            if requested.get("candidate_root") != candidate.digest:
                return None
            return candidate.runtime_snapshot(revision=current.revision + 1)

        transition = TransitionEngine(
            specs=(spec,),
            rules={operation: commit_candidate_root},
        ).execute(
            state=context.runtime_state,
            proposal=proposal,
            grant=grant,
        )

        next_kbi = candidate if transition.accepted else context.kbi
        next_runtime = transition.after_state
        next_chrono = context.chrono.append_outcome(transition)
        next_context = KBIContext(
            kbi=next_kbi,
            runtime_state=next_runtime,
            chrono=next_chrono,
        )
        return KBIExecutionResult(context=next_context, outcome=transition)
