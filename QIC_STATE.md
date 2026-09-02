# QIC State

Last updated: 2026-09-02

## Canonical status

**Phase:** Implementation Convergence

**Active slice:** `QIC-G1 — Canonical serializer + digest kernel`

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Established

- Dedicated public QIC repository and canonical Drive working tree exist.
- Professional public documentation, claim boundary, governance, contribution, security, roadmap, and architecture surfaces exist.
- `QIC-G0 — Repository + Constitutional Spine` is closed and merged to `main` as commit `27da6862fe61f8efc394b3ac2b22443370f85cbf`.
- G0 CI passed on Python 3.12 and 3.13 after correcting the non-cumulative maturity semantics.
- `qic.core` contains the immutable genesis constitutional snapshot and explicit non-cumulative maturity labels.
- Machine-readable constitution, maturity schema, and transition-registry seeds exist.
- T4 Physical and T5 Evolutionary remain explicitly `NOT_ENABLED`.
- G1 Issue exists as `#4` and branch `qic-g1/canonical-digest` is active.
- G1 branch contains `QIC-CANONICAL/1.0`, domain-separated `QIC-DIGEST/1.0`, golden vectors, negative tests, and ADR-0002.
- Architectural implementation sequence `I00` through `I11` remains documented in the canonical manuscript.
- Distribution strategy exists for ChatGPT, Gemini, NotebookLM, GitHub public, local/CodexStation, and the Omega public-LLM container.

## G1 implementation boundary

Implemented on the active branch:

- deterministic typed canonical UTF-8 JSON representation;
- stable mapping-key ordering;
- deterministic set/frozenset ordering by normalized canonical bytes;
- explicit distinctions for list/tuple, bool/int, strings/integers;
- dataclass and enum typed representations;
- explicit rejection of floats, unknown objects, and non-string mapping keys;
- SHA-256 digesting with explicit QIC version/domain separation;
- fixed golden vectors and repeatability tests.

Not implemented by G1:

- authority/capability runtime (`QIC-G3`);
- transition/invariant execution engine (`QIC-G4`);
- Chrono/witness implementation (`QIC-G5`);
- minimal KBI (`QIC-G6`);
- federation, physical control, or formal verification.

Canonical/digest identity demonstrates structural byte identity only and does not imply truth, authority, provenance correctness, safety, or execution success.

## Current G1 exit gate

- open a G1 PR from `qic-g1/canonical-digest`;
- require CI on Python 3.12 and 3.13;
- inspect the full diff for unstable serialization or accidental semantic/authority claims;
- verify golden vectors remain byte- and digest-stable;
- merge only after the corrected head is green.

## Next admissible action

Open and qualify the G1 PR. If green and review-clean, merge G1, close Issue #4, and instantiate `QIC-G2 — Root ontology + maturity vector`.

## Continuation rule

Every substantial implementation change should update this file if phase, maturity, blockers, or next action change. Public maturity statements must remain consistent with `CLAIM_BOUNDARY.md`.
