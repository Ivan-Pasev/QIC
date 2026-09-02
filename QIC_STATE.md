# QIC State

Last updated: 2026-09-03

## Canonical status

**Phase:** Post-G9 evidence-driven expansion

**Completed slice:** `QIC-G9 — Durable transaction journal + crash recovery`

**Next slice:** `QIC-G10 — Performance Observatory + Workload Atlas + Scaling/Bottleneck Evidence` (not yet activated)

**Release candidate baseline:** `1.0.0rc0`

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Qualified baseline

- G0–G7 merged constitutional implementation slices.
- G8 adversarial qualification merged as `b0c4f446dce21317cbd4cfc943633ee57507a8c8`.
- RC0 integrated release convergence merged via PR #21 as `588694dda816c6cb712d1812c6bbe23ca5092198`.
- RC0 exact evidence head `7a3234cb433e3b61bc9f858e8de9b0645378a845` passed final run `33675547670` with source tests, clean wheel/sdist installs, installed verification/qualification, and cross-Python reproducibility.
- RC0 publication metadata PR #25 merged as `74acec6c1d6569e04eec51c8745f718009f24d3d`; Issue #24 tracks the still-unpublished GitHub `v1.0.0rc0` tag/release.
- G9 durable journal/recovery merged via PR #23 as `8b297fea49d6dc76c0236fa9cca6bf8d9af7f249`.
- G9 documentation-sealed head `883f4bea90cc4c59f66e097f8415d39b90940658` passed full run `33683360428` including Python 3.12/3.13 source suites, clean wheel/sdist verification, inherited G8 qualification surfaces, and RC0 reproducibility.
- Issue #22 is CLOSED / COMPLETED.
- T4 Physical and T5 Evolutionary remain `NOT_ENABLED`.

## G9 closure

G9 establishes a bounded local durability/recovery substrate for the reference Python runtime:

- immutable `JournalPhase` and hash-linked `JournalRecord`;
- PREPARED → VALIDATED → STATE_COMMITTED → CHRONO_COMMITTED → WITNESS_COMMITTED → COMPLETE plus terminal ABORTED/QUARANTINED;
- unique same-directory temp files;
- file fsync + directory fsync reference policy;
- atomic no-replace hard-link publication;
- exact retry idempotence;
- divergent/concurrent conflict without overwrite;
- startup corruption containment;
- `DurableArtifactView` and conservative reconciliation;
- immutable exact-head-bound `RecoveryEvidenceBundle` / `RecoveryEvidenceStore`;
- no-double-state-commit classification;
- ahead-of-journal and digest-mismatch quarantine;
- rejected transition restart remains non-commit;
- deterministic crash/restart/race/corruption tests;
- recovery schema/runtime parity and ADR-0011;
- `RECOVERY_QUALIFICATION_G9.md` as the human-readable qualification record.

## Recovery law

`RecoveryMayReconcileRecordedIntent != RecoveryMayInventAuthorityOrCommit`

`artifact ahead of journal OR digest mismatch OR missing required evidence => QUARANTINE / NO SYNTHESIS`

`STATE_COMMITTED + exact state/outcome evidence => next admissible boundary is CHRONO commit, never state commit again`

`concurrent durable target exists => IDENTICAL = IDEMPOTENT; DIFFERENT = CONFLICT; NEVER OVERWRITE`

## Claim boundary

G9 qualifies tested local reference durability/restart properties only. It is not a universal filesystem/controller/VM/network-storage/power-loss proof and does not automatically replay authority-sensitive consequences.

Public maturity remains semantic `TESTED`, evidence `SUPPORTED`, formal `NONE`, hardware `NONE`, deployment `LOCAL`.

G9 adds no federation, distributed consensus, T4/T5 enablement, physical-control readiness, formal-runtime proof, hardware qualification, production-security certification, or semantic/scientific truth certification.

## Next admissible action

Open G10 as a **measurement-first performance slice** before federation or accelerator work:

1. implement a read-only Performance Observatory;
2. define deterministic workload/corpus profiles;
3. measure end-to-end and decomposed cost without bypassing authority, invariants, Chrono, witness, or serialization;
4. establish scaling curves and bottleneck classifications;
5. require `NoAcceleratorWithoutMeasuredBottleneck`;
6. preserve G9 durability/recovery regression tests and RC0 distribution gates;
7. do not begin FQNP federation or hardware acceleration until evidence justifies the next architectural move.

## Continuation rule

Preserve RC0 and G9 as frozen qualified baselines. Every substantial next-layer change must maintain claim boundaries, T4/T5 disabled status, source↔packaged manifest parity where applicable, and evidence-before-merge discipline.
