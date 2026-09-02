# QIC State

Last updated: 2026-09-02

## Canonical status

**Phase:** Implementation Convergence

**Active slice:** `QIC-G3 — Authority + capability model`

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Established

- Dedicated public QIC repository and canonical Drive working tree exist.
- `QIC-G0 — Repository + Constitutional Spine` is closed and merged to `main` as `27da6862fe61f8efc394b3ac2b22443370f85cbf`.
- `QIC-G1 — Canonical serializer + digest kernel` is closed and merged to `main` as `27d46780fc39132fff314c5020e254c55161378f`.
- `QIC-G2 — Root ontology + maturity vector` is closed and merged to `main` as `37445fb52456cf15a6f2c7a0e2bc389c61e307cf`.
- G2 contains the seven stable root ontology classes, independent five-dimensional maturity vector, schema/registry parity tests, and canonical/digest golden coverage.
- T4 Physical and T5 Evolutionary remain explicitly `NOT_ENABLED`.
- G3 Issue exists as `#8` and branch `qic-g3/authority-capability` is active.

## G3 implementation boundary

Implemented on the active branch:

- four authority domains: `A_E`, `A_C`, `A_P`, `A_X`;
- immutable `AuthorityRequirement` and `AuthorityGrant`;
- exact capability identifiers and exact resource scopes;
- explicit `ACTIVE` / `REVOKED` grant state;
- component-wise requirement satisfaction;
- direct delegation lineage checks;
- delegation non-amplification across domains, capabilities, and resources;
- wildcard/invalid token rejection;
- authority domain registry and authority-grant JSON Schema;
- representative canonical/digest golden vector;
- adversarial tests for cross-domain noninheritance, amplification attempts, revoked grants, and schema/registry parity;
- ADR-0004 documenting scoped authority semantics.

## Claim boundary

An authority grant is static constitutional metadata. Possessing, serializing, digesting, or receiving a grant object does not execute an operation, mutate KBI, create physical effects, or authenticate an external identity.

G3 does not implement transition execution, KBI mutation, Chrono, signatures, federation, or physical control.

## Current G3 exit gate

- open a G3 PR from `qic-g3/authority-capability`;
- require CI on Python 3.12 and 3.13;
- review the diff for hidden wildcard, implicit superuser, or cross-domain inheritance semantics;
- verify schema/runtime parity and authority-grant golden stability;
- merge only after the reviewed head is green.

## Next admissible action

Open and qualify the G3 PR. If review-clean and green, merge G3, close Issue #8, and instantiate `QIC-G4 — Transition engine + invariant gate`.

## Continuation rule

Every substantial implementation change should update this file if phase, maturity, blockers, or next action change. Public maturity statements must remain consistent with `CLAIM_BOUNDARY.md`.
