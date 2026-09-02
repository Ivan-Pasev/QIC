# QIC G9 Recovery Qualification Report

**Status:** active; final exact-head CI and review pending

**Scope:** local durable transaction journal, immutable recovery evidence receipts, and conservative crash/restart reconciliation for the QIC reference Python runtime.

## Qualification boundary

A G9 PASS establishes only the declared local behaviors exercised by the test campaign under the CI operating-system/filesystem/runtime environment. It is not a universal filesystem/controller/VM/network-storage/power-loss guarantee, formal verification, production-security certification, hardware qualification, federation evidence, physical-control readiness, or semantic/scientific truth certification.

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

## Retained limitations

- Recovery classification does not automatically execute state, Chrono, or witness writes.
- `RecoveryEvidenceBundle` contains verified digest receipts, not the underlying authoritative object bytes.
- A future executing recovery coordinator must separately re-check current authority and exact artifact identity before any consequence.
- G9 does not upgrade T4/T5, federation, formal, hardware, or universal durability maturity.

## Closure gate

G9 is eligible to close only after the final reviewed branch head:

- passes the full source suite on Python 3.12 and 3.13;
- passes inherited G8 qualification;
- passes RC0 wheel/sdist clean-install regression gates and reproducibility where the workflow applies them;
- retains source↔packaged manifest parity;
- contains no unresolved authority-synthesis, double-commit, overwrite-race, corruption-containment, or claim-inflation defect found during final diff review.

Exact final head/run evidence must be added only after those gates complete. Until then this report remains **ACTIVE**, not a durability certification.
