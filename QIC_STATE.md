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
- Architectural implementation sequence `I00` through `I11` is documented in the canonical manuscript.
- Distribution strategy exists for ChatGPT, Gemini, NotebookLM, GitHub public, local/CodexStation, and the Omega public-LLM container.

## Not yet established

- Python package/runtime skeleton.
- Canonical serializer and digest kernel.
- Executable ontology/maturity types.
- Authority/capability runtime.
- Transition/invariant gate.
- Chrono/witness implementation.
- Minimal KBI implementation.
- Genesis CLI.
- CI qualification and adversarial constitutional test closure.
- Lean/formal conformance artifacts.
- FQNP reference federation.
- Physical hardware qualification.

These remain targets, not completed capabilities.

## Current exit criteria for G0

G0 should close when the repository contains:

- professional public project documentation;
- `pyproject.toml` and package skeleton;
- `constitution/`, `schemas/`, `registry/`, `qic/core/`, `tests/`, `docs/adr/`;
- initial machine-readable constitutional/claim-boundary metadata;
- CI that installs the project and runs the genesis test suite;
- a traceable implementation issue/PR sequence.

## Next admissible action

Create the first G0 implementation branch/issue and add the executable package/test/CI skeleton. After G0 is reviewed, proceed to `QIC-G1 — Canonical serializer + digest kernel`.

## Continuation rule

Every substantial implementation change should update this file if phase, maturity, blockers, or next action change. Public maturity statements must remain consistent with `CLAIM_BOUNDARY.md`.
