# QIC State

Last updated: 2026-09-02

## Canonical status

**Phase:** Implementation Convergence

**Active slice:** `QIC-G7 — Genesis CLI + verification`

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Established

- G0 constitutional spine merged as `27da6862fe61f8efc394b3ac2b22443370f85cbf`.
- G1 canonical serializer/digest merged as `27d46780fc39132fff314c5020e254c55161378f`.
- G2 root ontology/maturity vector merged as `37445fb52456cf15a6f2c7a0e2bc389c61e307cf`.
- G3 authority/capability merged as `37ab95ac0aa691cf488bc21996ca90508121ca1c`.
- G4 transition/invariant kernel is merged via PR #11.
- G5 Chrono/witness merged as `3dcfe3b08378d5a71eaeb5c0ee834db85308b830`.
- G6 Minimal KBI merged as `8b71654e55e9b17055385ebdf85f2ba3ca94bf95` after the reviewed freshness-input correction passed Python 3.12/3.13 CI.
- T4 Physical and T5 Evolutionary remain explicitly `NOT_ENABLED`.
- G7 Issue is `#16`; branch `qic-g7/genesis-cli-verification` is active.

## G7 implementation boundary

Implemented on the active branch:

- dependency-free `qic` console entry point;
- `version`, `status`, `constitution`, `registry`, and `verify` command families;
- aggregate and targeted canonical/registry/transition/Chrono/KBI structural verification;
- deterministic compact JSON output mode;
- reference G4 campaign confirms T4 remains disabled even with matching A_P grant;
- reference G5 campaign verifies a valid chain and anchored-prefix truncation boundary;
- reference G6 campaign verifies binding-vs-promotion separation and unauthorized promotion non-commit/witnessing;
- `QIC_MANIFEST.json` with conservative maturity and explicit nonclaims;
- `TRACEABILITY.yaml` mapping G0–G7 artifacts/tests/ADRs;
- installed-console and module CLI tests;
- ADR-0008 documenting the non-certification and non-authority boundary.

## Claim boundary

A passing `qic verify` run establishes only the declared local structural checks for the installed source state/environment. It does not certify semantic truth, production security, formal correctness, physical safety, legal compliance, deployment readiness, cryptographic identity, distributed consensus, or durable crash recovery.

CLI inspection and reference verification do not mint authority or create a privileged mutation path. G7 remains local and has no network daemon or physical I/O.

## Current G7 exit gate

- open a G7 PR from `qic-g7/genesis-cli-verification`;
- require fresh install/CLI tests on Python 3.12 and 3.13;
- verify deterministic JSON and stable exit codes;
- audit manifest maturity/nonclaims against implemented evidence;
- audit CLI help/subcommands for mutation/authority bypass surfaces;
- merge only after the reviewed head is green.

## Next admissible action

Open and qualify the G7 PR. If review-clean and green, merge G7, close Issue #16, and instantiate `QIC-G8 — Adversarial constitutional qualification`.

## Continuation rule

Every substantial implementation change should update this file if phase, maturity, blockers, or next action change. Public maturity statements must remain consistent with `CLAIM_BOUNDARY.md`.
