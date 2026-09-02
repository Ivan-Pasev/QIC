# QIC State

Last updated: 2026-09-02

## Canonical status

**Phase:** Implementation Convergence

**Active slice:** `QIC-G0 — Repository + Constitutional Spine`

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Established

- Dedicated public QIC repository exists.
- Canonical Drive working tree exists.
- Public README, claim boundary, architecture, roadmap, governance, contribution guide, and security policy exist.
- G0 implementation issue exists as `#1`.
- G0 implementation branch exists as `qic-g0/bootstrap`.
- Draft implementation PR exists as `#2`.
- Python 3.12+ installable project skeleton exists on the G0 branch.
- `qic.core` contains an immutable genesis constitutional snapshot and explicit non-cumulative maturity labels.
- Machine-readable constitution, maturity schema, and transition-registry seeds exist.
- T4 Physical and T5 Evolutionary transitions remain explicitly `NOT_ENABLED` at G0.
- Genesis tests and GitHub Actions CI exist; the initial PR head passed on Python 3.12 and 3.13 before a maturity-semantics correction.
- Diff review caught and corrected a linear-maturity bug so `SIMULATED` no longer implies `FORMALLY_MODELED` (and vice versa).
- Architectural implementation sequence `I00` through `I11` is documented in the canonical manuscript.
- Distribution strategy exists for ChatGPT, Gemini, NotebookLM, GitHub public, local/CodexStation, and the Omega public-LLM container.

## Not yet established

- Deterministic canonical serializer and digest kernel (`QIC-G1`).
- Authority/capability runtime (`QIC-G3`).
- Transition/invariant execution engine (`QIC-G4`).
- Chrono/witness implementation (`QIC-G5`).
- Minimal KBI implementation (`QIC-G6`).
- Genesis CLI (`QIC-G7`).
- Adversarial constitutional closure (`QIC-G8`).
- Lean/formal conformance artifacts.
- FQNP reference federation.
- Physical hardware qualification.

These remain targets, not completed capabilities.

## G0 review state

Current PR: https://github.com/Ivan-Pasev/QIC/pull/2

G0 exit evidence currently includes:

- professional public documentation;
- package skeleton;
- constitutional/registry/schema surfaces;
- executable genesis core objects;
- genesis tests;
- CI definition;
- ADR-0001;
- issue/branch/PR traceability.

Final merge gate: corrected PR head must pass CI and the diff must remain free of maturity/authority overclaim.

## Next admissible action

Confirm CI on the corrected PR head. If green, mark PR #2 ready and merge G0. Then close Issue #1 if its full exit gate remains satisfied and open `QIC-G1 — Canonical serializer + digest kernel`.

## Continuation rule

Every substantial implementation change should update this file if phase, maturity, blockers, or next action change. Public maturity statements must remain consistent with `CLAIM_BOUNDARY.md`.
