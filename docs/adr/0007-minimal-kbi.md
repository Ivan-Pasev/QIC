# ADR-0007 — Minimal KBI Semantics

- **Status:** Accepted for G6 implementation
- **Date:** 2026-09-02

## Context

G0–G5 now provide deterministic canonicalization, scoped authority, an atomic in-memory transition gate, and local causal/witness history. QIC can therefore introduce its first epistemic state processor without conflating object construction, evidence binding, or status labels with authoritative knowledge admission.

## Decision

G6 introduces immutable structural records:

- `ClaimRecord`
- `EvidenceRecord`
- `EvidenceBinding`
- `ContradictionRecord`
- `KBIState`

The claim-status vocabulary is explicit: `ASSERTED`, `SUPPORTED`, `CORROBORATED`, `VALIDATED`, `CANONICAL`, `CONTESTED`, `CONTRADICTED`, `SUPERSEDED`, `QUARANTINED`.

Evidence classes implemented in G6 are `OBSERVED`, `DERIVED`, `SIMULATED`, `FORMALLY_PROVED`, `ATTESTED`, and `REMOTE_OBSERVED`. `MEASURED` is reserved for later physical/metrology work and is not enabled as a G6 evidence class.

### Structural construction is not admission

Python code may construct a `KBIState` or even a `ClaimRecord(status=CANONICAL)`. That proves only that the structural object is well formed and canonicalizable. It does **not** prove that the object was admitted through QIC's authoritative KBI path.

The reference authoritative path is:

`candidate KBI state → G4 T2 epistemic transition → current A_E authority check → accepted/rejected TransitionOutcome → G5 Chrono/Witness`

`KBIExecutor` implements this path. It projects the candidate KBI digest into a minimal G4 `StateSnapshot` containing `kbi.root`. On acceptance the candidate becomes the next KBI state. On rejection the previous KBI/runtime state is retained exactly, while the rejected outcome is still appended to Chrono.

### Evidence independence

Evidence binding never promotes a claim automatically.

`SUPPORTED` requires at least one supporting evidence binding.

`CORROBORATED` requires at least two distinct supporting `source_id` values that are also distinct from the claim's `origin_source_id`. Multiple evidence records or bindings from the same source therefore do not create independent corroboration, and self-origin evidence cannot manufacture independence.

`VALIDATED` and `CANONICAL` additionally require the prior forward lifecycle step and no explicit contradiction affecting the claim.

These are deliberately conservative G6 structural rules, not universal scientific truth criteria.

### Contradiction preservation

Contradictions are first-class records. An explicit contradiction transition preserves the link and marks the target `CONTRADICTED` and counterclaim `CONTESTED` unless already in a stronger defensive state. Contradictory evidence also blocks validation/canonicalization through `has_contradiction`.

Contradictions are not silently resolved by majority, binding count, or status precedence.

## Authority

All G6 authoritative operations are T2 epistemic transitions and require `A_E`, exact operation capability, and resource `state.kbi`.

Capabilities are:

- `kbi.claim.assert`
- `kbi.evidence.add`
- `kbi.evidence.bind`
- `kbi.claim.promote`
- `kbi.claim.contradict`

No G6 operation infers authority from another domain.

## Claim boundary

KBI lifecycle status is QIC-local epistemic metadata. `CANONICAL` means accepted into the declared local KBI lifecycle under the implemented rules; it does not establish universal truth, scientific consensus, legal fact, physical validity, or correctness beyond the evidence and authority model actually represented.

Evidence binding proves linkage, not truth. Chrono/witness proves structural causal composition, not semantic correctness.

G6 is local. `REMOTE_OBSERVED` is only a structural evidence class; federation trust/admission semantics do not exist yet.

## Consequences

Positive:

- epistemic state now has a concrete authoritative mutation path;
- evidence echo and self-support cannot inflate independent-source count;
- accepted and rejected epistemic proposals are causally witnessed;
- contradictions remain explicit;
- later Holo/Topo/Hermes/MLCO processors can be constrained to candidate/proposal roles.

Costs and limitations:

- source independence is currently represented by explicit `source_id`, not cryptographic or institutional independence proof;
- KBI is in memory and local;
- no provenance graph, Holo/Topo/Knot, formal-runtime proof, federation, or physical measurement exists yet;
- pure candidate-construction helpers are intentionally non-authoritative and can be called independently of `KBIExecutor`.

## Deferred

G6 does not implement Holo, Topo, Knot, Hermes, MLCO, Omnius, FQNP, remote admission, physical measurement, durable crash recovery, or distributed consensus.
