# QIC State

Last updated: 2026-09-02

## Canonical status

**Phase:** Implementation Convergence

**Active slice:** `QIC-G5 — Chrono + witness`

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Established

- Dedicated public QIC repository and canonical Drive working tree exist.
- `QIC-G0 — Repository + Constitutional Spine` is closed and merged to `main` as `27da6862fe61f8efc394b3ac2b22443370f85cbf`.
- `QIC-G1 — Canonical serializer + digest kernel` is closed and merged to `main` as `27d46780fc39132fff314c5020e254c55161378f`.
- `QIC-G2 — Root ontology + maturity vector` is closed and merged to `main` as `37445fb52456cf15a6f2c7a0e2bc389c61e307cf`.
- `QIC-G3 — Authority + capability model` is closed and merged to `main` as `37ab95ac0aa691cf488bc21996ca90508121ca1c`.
- `QIC-G4 — Transition engine + invariant gate` is closed and merged via PR #11; current `main` includes its deterministic transition kernel.
- G4 enforces current-state freshness, actor/grant binding, scoped authority, pure rules, invariant gates, exact denial codes, and narrow in-memory no-commit-on-failure semantics.
- T4 Physical and T5 Evolutionary remain explicitly `NOT_ENABLED`.
- G5 Issue exists as `#12` and branch `qic-g5/chrono-witness` is active.

## G5 implementation boundary

Implemented on the active branch:

- immutable `ChronoEvent` and `WitnessRecord`;
- explicit genesis event/witness rules;
- monotonically increasing causal sequence numbers;
- previous-event and previous-witness digest linkage;
- immutable `ChronoChain` whose append operation returns a new chain;
- exact G4 proposal/outcome and before/after state digest binding;
- accepted and rejected transition event semantics;
- rejected outcomes remain witnessable while preserving `before_state_digest == after_state_digest`;
- local chain verification for sequence/link/state/witness continuity;
- external G4 outcome-to-event/witness verification;
- deterministic Chrono/witness digests and fixed golden vectors;
- machine-readable Chrono/witness JSON Schema and enum parity tests;
- adversarial tests for event deletion, reordering, forged linkage, event mutation, witness mutation, and outcome mismatch;
- ADR-0006 documenting structural witness boundaries.

## Claim boundary

A valid G5 Chrono chain or witness establishes only structural composition under the declared canonicalization/digest rules. It does not establish semantic truth, authority, authenticated identity, distributed consensus, trustworthy wall-clock time, durable persistence, crash-recovery atomicity, or successful external/physical effects.

G5 is local and unsigned. It does not implement KBI claim admission, persistent journal recovery, identity cryptography, federation, or physical control.

## Current G5 exit gate

- open a G5 PR from `qic-g5/chrono-witness`;
- require CI on Python 3.12 and 3.13;
- review the full diff for any history rewrite path, witness circularity, or false durability/nonrepudiation claim;
- verify rejected outcomes cannot imply a state commit;
- verify tampering/reordering/deletion and witness mismatch are detected;
- verify schema/runtime parity and Chrono golden stability;
- merge only after the reviewed head is green.

## Next admissible action

Open and qualify the G5 PR. If review-clean and green, merge G5, close Issue #12, and instantiate `QIC-G6 — Minimal KBI`.

## Continuation rule

Every substantial implementation change should update this file if phase, maturity, blockers, or next action change. Public maturity statements must remain consistent with `CLAIM_BOUNDARY.md`.
