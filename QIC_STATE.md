# QIC State

Last updated: 2026-09-02

## Canonical status

**Phase:** Implementation Convergence

**Active slice:** `QIC-G6 — Minimal KBI`

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Established

- Dedicated public QIC repository and canonical Drive working tree exist.
- `QIC-G0 — Repository + Constitutional Spine` is closed and merged to `main` as `27da6862fe61f8efc394b3ac2b22443370f85cbf`.
- `QIC-G1 — Canonical serializer + digest kernel` is closed and merged to `main` as `27d46780fc39132fff314c5020e254c55161378f`.
- `QIC-G2 — Root ontology + maturity vector` is closed and merged to `main` as `37445fb52456cf15a6f2c7a0e2bc389c61e307cf`.
- `QIC-G3 — Authority + capability model` is closed and merged to `main` as `37ab95ac0aa691cf488bc21996ca90508121ca1c`.
- `QIC-G4 — Transition engine + invariant gate` is closed and merged via PR #11.
- `QIC-G5 — Chrono + witness` is closed and merged to `main` as `3dcfe3b08378d5a71eaeb5c0ee834db85308b830`.
- G5 provides immutable local causal event/witness chains, rejected-transition witnessing, and optional externally anchored head/length verification for suffix-truncation detection.
- T4 Physical and T5 Evolutionary remain explicitly `NOT_ENABLED`.
- G6 Issue exists as `#14` and branch `qic-g6/minimal-kbi` is active.

## G6 implementation boundary

Implemented on the active branch:

- immutable `ClaimRecord`, `EvidenceRecord`, `EvidenceBinding`, and `ContradictionRecord`;
- explicit claim lifecycle statuses ASSERTED through CANONICAL plus CONTESTED, CONTRADICTED, SUPERSEDED, and QUARANTINED;
- evidence classes OBSERVED, DERIVED, SIMULATED, FORMALLY_PROVED, ATTESTED, REMOTE_OBSERVED; MEASURED remains reserved for later physical slices;
- immutable deterministic `KBIState` with referential-integrity checks;
- pure non-authoritative candidate transformations;
- `KBIContext` binding KBI root, G4 runtime snapshot, and G5 Chrono head;
- `KBIExecutor` as the reference authoritative path through T2 / A_E / exact capability / `state.kbi` checks;
- accepted and rejected epistemic outcomes appended to Chrono;
- evidence binding separated from claim promotion;
- independent corroboration counts distinct non-origin `source_id` values rather than binding count;
- duplicate logical bindings rejected;
- explicit contradiction preservation and contradiction-aware validation/canonicalization gates;
- registry/schema enum parity tests;
- deterministic KBI golden vectors;
- adversarial tests for evidence echo, self-support, unauthorized promotion, stale admission, missing evidence, contradiction suppression, and direct mutation attempts;
- ADR-0007 documenting structural construction vs authoritative admission.

## Claim boundary

Constructing or canonicalizing a KBI object is not authoritative admission. A `CANONICAL` label on a standalone object does not establish that it passed the QIC KBI transition path.

Within the G6 reference path, `CANONICAL` means accepted into the local declared KBI lifecycle after the implemented evidence/authority gates. It does not establish universal truth, scientific consensus, legal fact, physical validity, or correctness beyond represented evidence and rules.

Source independence is currently represented by explicit `source_id`; it is not cryptographic or institutional independence proof. G6 is local and does not implement federation, physical measurement, Holo/Topo/Knot, Hermes, MLCO, or Omnius.

## Current G6 exit gate

- open a G6 PR from `qic-g6/minimal-kbi`;
- require CI on Python 3.12 and 3.13;
- review the diff for any direct authoritative mutation path outside G4/A_E execution;
- verify evidence echo/self-origin cannot manufacture independent corroboration;
- verify unauthorized/stale operations preserve KBI/runtime state while producing rejected Chrono records;
- verify contradictions cannot be silently discarded during validation/canonicalization;
- verify schema/runtime parity and KBI golden stability;
- merge only after the reviewed head is green.

## Next admissible action

Open and qualify the G6 PR. If review-clean and green, merge G6, close Issue #14, and instantiate `QIC-G7 — Genesis CLI + verification`.

## Continuation rule

Every substantial implementation change should update this file if phase, maturity, blockers, or next action change. Public maturity statements must remain consistent with `CLAIM_BOUNDARY.md`.
