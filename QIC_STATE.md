# QIC State

Last updated: 2026-09-02

## Canonical status

**Phase:** Implementation Convergence

**Active slice:** `QIC-G2 — Root ontology + maturity vector`

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Established

- Dedicated public QIC repository and canonical Drive working tree exist.
- `QIC-G0 — Repository + Constitutional Spine` is closed and merged to `main` as `27da6862fe61f8efc394b3ac2b22443370f85cbf`.
- `QIC-G1 — Canonical serializer + digest kernel` is closed and merged to `main` as `27d46780fc39132fff314c5020e254c55161378f`.
- G1 includes deterministic `QIC-CANONICAL/1.0`, domain-separated `QIC-DIGEST/1.0`, fixed golden vectors, cross-process repeatability coverage, and fail-closed unsupported types.
- T4 Physical and T5 Evolutionary remain explicitly `NOT_ENABLED`.
- G2 Issue exists as `#6` and branch `qic-g2/ontology-maturity` is active.

## G2 implementation boundary

Implemented on the active branch:

- seven stable root ontology classes: STATE, ACTOR, OPERATION, CONSTRAINT, EVIDENCE, RESOURCE, WITNESS;
- stable `qic:ontology:<NAME>` identifiers;
- independent semantic/evidence/formal/hardware/deployment maturity dimensions;
- immutable `MaturityVector`;
- component-wise `satisfies`, `shortfall`, and partial-order dominance helpers;
- machine-readable root ontology registry and maturity-vector JSON Schema;
- representative canonical/digest golden vector;
- tests proving simulation, formality, hardware evidence, deployment, and independent replication do not silently imply each other;
- ADR-0003 documenting vector maturity semantics.

## Claim boundary

Ontology membership and maturity metadata classify structural/evidence state only. They do not grant truth, authority, provenance correctness, safety, physical validity, or execution rights.

G2 does not implement authority delegation, capability grants, transition execution, KBI admission, Chrono, federation, or physical effects.

## Current G2 exit gate

- open a G2 PR from `qic-g2/ontology-maturity`;
- require CI on Python 3.12 and 3.13;
- review the diff for reintroduction of a global ordinal maturity ladder;
- verify schema/runtime enum parity and golden-vector stability;
- merge only after the reviewed head is green.

## Next admissible action

Open and qualify the G2 PR. If review-clean and green, merge G2, close Issue #6, and instantiate `QIC-G3 — Authority + capability model`.

## Continuation rule

Every substantial implementation change should update this file if phase, maturity, blockers, or next action change. Public maturity statements must remain consistent with `CLAIM_BOUNDARY.md`.
