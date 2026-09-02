# QIC State

Last updated: 2026-09-02

## Canonical status

**Phase:** Implementation Convergence

**Active slice:** `QIC-G4 — Transition engine + invariant gate`

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Established

- Dedicated public QIC repository and canonical Drive working tree exist.
- `QIC-G0 — Repository + Constitutional Spine` is closed and merged to `main` as `27da6862fe61f8efc394b3ac2b22443370f85cbf`.
- `QIC-G1 — Canonical serializer + digest kernel` is closed and merged to `main` as `27d46780fc39132fff314c5020e254c55161378f`.
- `QIC-G2 — Root ontology + maturity vector` is closed and merged to `main` as `37445fb52456cf15a6f2c7a0e2bc389c61e307cf`.
- `QIC-G3 — Authority + capability model` is closed and merged to `main` as `37ab95ac0aa691cf488bc21996ca90508121ca1c`.
- G3 contains strict immutable authority objects, scoped A_E/A_C/A_P/A_X requirements, non-amplifying delegation, revocation, registry/schema parity, and adversarial construction tests.
- T4 Physical and T5 Evolutionary remain explicitly `NOT_ENABLED`.
- G4 Issue exists as `#10` and branch `qic-g4/transition-invariant-gate` is active.

## G4 implementation boundary

Implemented on the active branch:

- runtime `TransitionFamily` for T0–T5 with registry parity;
- immutable `StateSnapshot`, `TransitionSpec`, `TransitionProposal`, and `TransitionOutcome`;
- expected-before-state digest freshness check;
- proposal actor to current grant-subject binding;
- G3 authority enforcement at execution time;
- exact operation/rule registry;
- global and operation-scoped invariant gate;
- explicit failure codes for unknown operation, disabled family, stale state, subject mismatch, authority denial, rule rejection, and invariant failure;
- rejection returns the exact original state object as `after_state`;
- T0–T3 enabled in the reference compute profile; T4/T5 hard-disabled;
- transition JSON Schema, golden vector, and denial/atomicity tests;
- ADR-0005 documenting the narrow in-memory atomicity claim.

## Claim boundary

A successful G4 outcome demonstrates only that a candidate state passed the declared in-memory structural gates. It does not establish semantic truth, physical safety, external side-effect completion, provenance completeness, crash-recovery atomicity, durable persistence, or witness-chain completeness.

G4 does not implement KBI admission, Chrono persistence, signatures, federation, or physical control.

## Current G4 exit gate

- open a G4 PR from `qic-g4/transition-invariant-gate`;
- require CI on Python 3.12 and 3.13;
- review the full diff for any denial path that could expose changed state;
- verify T4/T5 remain non-executable even with A_P/A_X grants;
- verify registry/schema/runtime parity and transition golden stability;
- merge only after the reviewed head is green.

## Next admissible action

Open and qualify the G4 PR. If review-clean and green, merge G4, close Issue #10, and instantiate `QIC-G5 — Chrono + witness`.

## Continuation rule

Every substantial implementation change should update this file if phase, maturity, blockers, or next action change. Public maturity statements must remain consistent with `CLAIM_BOUNDARY.md`.
