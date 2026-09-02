# QIC State

Last updated: 2026-09-02

## Canonical status

**Phase:** Post-RC0 reliability engineering

**Active slice:** `QIC-G9 — Durable transaction journal + crash recovery`

**Release candidate baseline:** `1.0.0rc0`

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Qualified baseline

- G0–G7 are merged constitutional implementation slices.
- G8 adversarial qualification merged as `b0c4f446dce21317cbd4cfc943633ee57507a8c8`.
- RC0 integrated release convergence merged via PR #21 as `588694dda816c6cb712d1812c6bbe23ca5092198`.
- RC0 exact evidence head `7a3234cb433e3b61bc9f858e8de9b0645378a845` passed final run `33675547670` with source tests, clean wheel/sdist installs, installed verification/qualification, and cross-Python reproducibility.
- RC0 publication metadata PR #25 merged as `74acec6c1d6569e04eec51c8745f718009f24d3d`; Issue #24 tracks the still-unpublished GitHub `v1.0.0rc0` tag/release.
- T4 Physical and T5 Evolutionary remain `NOT_ENABLED`.

## G9 execution

- Issue: #22
- Draft PR: #23
- Branch: `qic-g9/durable-recovery`
- G9 remains draft until the complete recovery contract is qualified.

Implemented on the G9 branch:

- immutable `JournalPhase` and hash-linked `JournalRecord`;
- legal PREPARED → VALIDATED → STATE_COMMITTED → CHRONO_COMMITTED → WITNESS_COMMITTED → COMPLETE progression plus terminal ABORTED/QUARANTINED;
- phase-specific state/outcome/Chrono/witness digest requirements;
- explicit protection against transaction/sequence/phase/link rebinding;
- `JournalFileStore` with temp-write → flush/fsync → atomic replace → directory fsync reference policy;
- immutable persisted records with schema/digest/sequence/link/phase validation;
- idempotent retry of identical durable records and conflict rejection for divergent duplicates;
- deterministic journal failpoints before/after atomic promotion;
- startup scanning that contains corrupt transactions without hiding valid ones;
- phase-specific nonexecuting `assess_recovery()` classification;
- `DurableArtifactView` and conservative `reconcile_recovery()`;
- mismatch/ahead-of-journal evidence quarantines instead of inferred forward progress;
- immutable `RecoveryEvidenceBundle` bound to exact transaction, journal sequence, and journal-head digest;
- `RecoveryEvidenceStore` with atomic immutable bundle persistence and exact-retry idempotence;
- restart-idempotent reconciliation and no-double-state-commit classification;
- deterministic crash/restart campaign for state, Chrono, and witness boundaries;
- recovery schema/runtime parity checks and ADR-0011;
- G9 traceability map.

## Defects discovered and contained during G9

1. `JournalRecord.successor(phase, **changes)` allowed Python argument binding to throw before QIC could explicitly reject forged `phase=` rebinding. The API parameter is now `next_phase`, so protected-field rebinding reaches the constitutional guard and fails with the intended QIC error.
2. The initial durable-store append ordering rejected an exact retry of an already-durable terminal record before checking idempotence. Exact durable duplicates are now recognized first; conflicting duplicates remain fail-closed.

## Current evidence state

Head `e360330c923db97349722bb3b7cd8b3647135df7` passed CI run `33680622144` completely, including source tests on Python 3.12/3.13 and inherited RC0 artifact/reproducibility regression gates.

Subsequent G9 commits add immutable recovery evidence bundles, restart/crash qualification, schema, ADR, traceability, and manifest/state synchronization. The exact final head must pass a fresh complete CI run before PR #23 can leave draft.

## Recovery law

`artifact ahead of journal OR digest mismatch OR missing required evidence => QUARANTINE / NO SYNTHESIS`

`STATE_COMMITTED + exact state/outcome evidence => next admissible boundary is CHRONO commit, never state commit again`

Recovery classification is descriptive only. It does not mint authority, replay a transition, create KBI state, append Chrono, or synthesize a witness.

## Claim boundary

The G9 reference implementation tests local durability/restart behavior under the declared Python/OS/filesystem semantics. It is not a universal filesystem/controller/VM/network-storage/power-loss proof. While G9 is active, QIC retains the public nonclaim of durable crash-recovery completion.

Public maturity remains semantic `TESTED`, evidence `SUPPORTED`, formal `NONE`, hardware `NONE`, deployment `LOCAL`. G9 adds no federation, distributed consensus, T4/T5 enablement, physical-control readiness, formal-runtime proof, hardware qualification, or semantic/scientific truth certification.

## Next admissible action

Run fresh exact-head Python 3.12/3.13 CI and inherited RC0 regression gates; inspect the complete G9 diff adversarially for filesystem, idempotence, evidence-binding, authority-synthesis, and double-commit gaps. If review finds defects, fix and rerun. Mark PR #23 ready and merge only after the corrected exact head is green and the G9 claim boundary remains conservative.

## Continuation rule

Preserve RC0 as a frozen qualified baseline. Every substantial reliability change must maintain claim boundaries, T4/T5 disabled status, source↔packaged manifest parity where applicable, and evidence-before-merge discipline.
