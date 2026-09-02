# QIC State

Last updated: 2026-09-02

## Canonical status

**Phase:** Genesis Qualification

**Active slice:** `QIC-G8 — Adversarial constitutional qualification`

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Established

- G0 constitutional spine merged as `27da6862fe61f8efc394b3ac2b22443370f85cbf`.
- G1 canonical serializer/digest merged as `27d46780fc39132fff314c5020e254c55161378f`.
- G2 root ontology/maturity vector merged as `37445fb52456cf15a6f2c7a0e2bc389c61e307cf`.
- G3 authority/capability merged as `37ab95ac0aa691cf488bc21996ca90508121ca1c`.
- G4 transition/invariant kernel is merged via PR #11.
- G5 Chrono/witness merged as `3dcfe3b08378d5a71eaeb5c0ee834db85308b830`.
- G6 Minimal KBI merged as `8b71654e55e9b17055385ebdf85f2ba3ca94bf95`.
- G7 Genesis CLI + verification merged as `a6de352bae6624eaebd4a984bb26fe67dba0f7e3` after Python 3.12/3.13 CI passed.
- T4 Physical and T5 Evolutionary remain explicitly `NOT_ENABLED`.
- G8 Issue is `#18`; branch `qic-g8/adversarial-qualification` is active.

## G8 implementation boundary

Implemented on the active branch:

- `qic/qualification.py` centralized adversarial qualification runtime;
- nine structural qualification checks spanning G1–G7;
- five deterministic modeled constitutional mutants;
- release-blocking rule: any failed check or surviving declared critical mutant blocks G8 closure;
- `qic verify qualification` and aggregate G8 verification through the public CLI;
- independent adversarial tests under `tests/adversarial/`;
- explicit failure atlas under `docs/qualification/FAILURE_ATLAS.yaml`;
- `QUALIFICATION_REPORT.md` with qualification scope and residual limitations;
- ADR-0009;
- G8 manifest and traceability updates.

Modeled mutants:

- `scalar_maturity_collapse`
- `authority_any_of`
- `enable_t4`
- `ignore_chrono_anchor`
- `count_echo_bindings`

## Claim boundary

A G8 PASS establishes only the declared local structural properties exercised by the qualification campaign on the tested source/environment. It does not certify semantic truth, production security, formal correctness, physical safety, legal compliance, deployment readiness, cryptographic identity, federation, distributed consensus, hardware qualification, or durable crash recovery.

A valid Chrono prefix still cannot prove its own completeness/recency. Suffix truncation detection requires an independently retained expected length/head anchor.

## Current G8 exit gate

- open a G8 PR from `qic-g8/adversarial-qualification`;
- require fresh install and full tests on Python 3.12 and 3.13;
- require all nine qualification checks to pass;
- require all five declared critical modeled mutants to be killed;
- adversarially review the complete diff and public claim surfaces;
- fix any discovered constitutional defect and rerun CI on the corrected exact head;
- update `QUALIFICATION_REPORT.md` with exact final evidence;
- merge only the reviewed green head.

## Next admissible action

Open and qualify the G8 PR. If clean and green, merge G8 and instantiate `QIC-v1 RC0 — integrated genesis release convergence` rather than adding a new architecture-expansion layer.

## Continuation rule

Every substantial implementation change should update this file if phase, maturity, blockers, or next action change. Public maturity statements must remain consistent with `CLAIM_BOUNDARY.md` and `QIC_MANIFEST.json`.
