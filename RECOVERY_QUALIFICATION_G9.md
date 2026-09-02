# QIC G9 Recovery Qualification Report

**Status:** PASS — merged via PR #23

**Scope:** local durable transaction journal, immutable recovery evidence receipts, and conservative crash/restart reconciliation for the QIC reference Python runtime.

## Qualification boundary

This PASS establishes only the declared local behaviors exercised by the test campaign under the CI operating-system/filesystem/runtime environment. It is not a universal filesystem/controller/VM/network-storage/power-loss guarantee, formal verification, production-security certification, hardware qualification, federation evidence, physical-control readiness, or semantic/scientific truth certification.

The reference promotion strategy requires same-filesystem hard-link semantics. G9 does not claim that every supported Python host/storage stack implements those semantics or directory fsync identically.

## Recovery laws exercised

1. `RecoveryMayReconcileRecordedIntent != RecoveryMayInventAuthorityOrCommit`.
2. `UnwitnessedAuthorityMustNeverBeSynthesizedDuringRecovery`.
3. `artifact ahead of journal OR mismatch OR missing required evidence => QUARANTINE / NO SYNTHESIS`.
4. `STATE_COMMITTED + matching state/outcome => resume Chrono, never repeat state commit`.
5. `concurrent durable target: identical => idempotent; different => conflict; never overwrite`.

## Implemented evidence surfaces

- immutable `JournalRecord` hash chain and legal phase model;
- `JournalFileStore` with unique temp files, file fsync, atomic no-replace hard-link publication, temp cleanup, and directory fsync;
- journal corruption, sequence, phase, link, and transaction-directory validation;
- deterministic journal failpoints before and after publication;
- `DurableArtifactView` + conservative `reconcile_recovery()`;
- immutable exact-head-bound `RecoveryEvidenceBundle`;
- `RecoveryEvidenceStore` with no-replace publication;
- `reconcile_evidence_bundle()` exact transaction/sequence/head binding;
- recovery schema and runtime phase parity;
- restart campaign across PREPARED, VALIDATED, STATE_COMMITTED, CHRONO_COMMITTED, WITNESS_COMMITTED, COMPLETE;
- ahead-of-journal state/Chrono/witness quarantine cases;
- rejected G4 transition → ABORTED restart case;
- torn/unknown/cross-transaction persistence cases;
- concurrent conflicting journal/evidence publication race cases;
- stale temp residue case;
- repeated restart/reconciliation idempotence.

## Defects discovered during G9 and corrected before closure

1. **Protected phase rebinding was intercepted by Python before QIC.** `JournalRecord.successor(phase, **changes)` was changed to `successor(next_phase, **changes)` so an attempted `phase=` rewrite reaches the explicit protected-field guard.
2. **Terminal idempotent retry ordering.** The first store checked terminal-head progression before recognizing an identical already-durable record. Exact duplicate recognition now occurs first.
3. **Replace-overwrite race.** `os.replace` could overwrite a concurrent winner after a stale pre-check. Both stores now use atomic no-replace hard-link promotion.
4. **Fixed temp-name crash residue.** A process death could leave one fixed temp filename and block later writers. Unique same-directory temp names now prevent that stale-file denial.
5. **Concurrent identical temp residue.** The losing writer in an identical promotion race now cleans its unique temp before returning idempotently.
6. **RC0 lifecycle assertions lagged the merged repository state.** Legacy tests still required `RC0 == ACTIVE` after PR #21 had merged. Tests were aligned to the actual merged lifecycle without relaxing maturity or claim boundaries.
7. **One claim-boundary test was grammar-sensitive rather than semantic.** The literal wording check was replaced by substantive checks that semantic truth and universal durable crash recovery remain outside the certified scope.

## Exact qualification evidence

Implementation candidate head:

`dc96f4b063d40d727c22a2b9d4ed124cd9cf0f71`

Candidate run:

`33683203029` — PASS

Documentation-sealed merge head:

`883f4bea90cc4c59f66e097f8415d39b90940658`

Final exact-head GitHub Actions run:

`33683360428` — PASS

Merge commit:

`8b297fea49d6dc76c0236fa9cca6bf8d9af7f249`

Observed final gates:

- source suite PASS on Python 3.12;
- source suite PASS on Python 3.13;
- RC0 wheel build, packaged-resource inspection, clean wheel install, and installed verification PASS on Python 3.12/3.13;
- normalized sdist clean install and verification PASS on Python 3.12/3.13;
- inherited G8 qualification PASS through installed verification surfaces;
- cross-Python RC0 reproducibility PASS;
- final PR mergeability review PASS;
- Issue #22 closed as completed by the merge.

## Retained limitations

- Recovery classification does not automatically execute state, Chrono, or witness writes.
- `RecoveryEvidenceBundle` contains verified digest receipts, not the underlying authoritative object bytes.
- A future executing recovery coordinator must separately re-check current authority and exact artifact identity before any consequence.
- G9 does not upgrade T4/T5, federation, formal, hardware, or universal durability maturity.

## Closure

G9 is **CLOSED / MERGED / QUALIFIED within its declared local reference scope**.

This is not a universal durability certification. The next engineering slice must preserve this boundary and may not infer broader storage, deployment, federation, hardware, physical, or epistemic maturity from G9 alone.
