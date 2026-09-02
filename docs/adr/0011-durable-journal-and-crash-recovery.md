# ADR-0011 — Durable Journal and Crash-Recovery Policy

- **Status:** Accepted for G9 qualification
- **Date:** 2026-09-02

## Context

RC0 qualified the local constitutional kernel but explicitly retained `No durable crash-recovery claim`. G4 provides in-memory no-commit-on-failure semantics and G5 provides local Chrono/witness structure, but neither establishes what happens if a process terminates between persistence boundaries.

G9 introduces a narrowly scoped local recovery substrate without creating a privileged authority path.

## Decision

G9 uses an immutable per-transaction journal with legal phases:

`PREPARED → VALIDATED → STATE_COMMITTED → CHRONO_COMMITTED → WITNESS_COMMITTED → COMPLETE`

with bounded terminal exits `ABORTED` and `QUARANTINED`.

Each successor is hash-linked to the previous record and carries only digest references required by the phase already crossed.

The reference `JournalFileStore` persists records by:

1. creating a new temporary file;
2. writing the complete immutable record;
3. flushing and fsyncing the file;
4. atomically replacing the target path;
5. fsyncing the containing directory.

Existing immutable records are never overwritten. Retrying the exact same record is idempotent; a different record at the same sequence is a conflict.

## Recovery evidence

The journal is not treated as proof that state, Chrono, or witness artifacts actually exist. Separately verified durable artifact digests are represented by `DurableArtifactView` and may be persisted in an immutable `RecoveryEvidenceBundle` bound to the exact transaction ID, journal sequence, and journal-head digest.

Persisting a recovery evidence bundle is receipt persistence only. It does not grant epistemic authority or transform the referenced artifact into authoritative state.

## Reconciliation rule

Recovery is conservative and descriptive.

- If journal and separately verified durable evidence agree exactly, the classifier returns only the next missing boundary.
- If evidence is ahead of the journal, QIC does **not** infer that an unrecorded commit happened; it quarantines the transaction.
- If any state/outcome/Chrono/witness digest disagrees with the journal, the transaction is quarantined.
- If required evidence is absent, recovery does not synthesize it.
- A `STATE_COMMITTED` restart can only resume at Chrono commit, never repeat state commit.
- A `CHRONO_COMMITTED` restart can only resume at witness commit.
- A `WITNESS_COMMITTED` restart can only finalize the journal.
- `ABORTED` and `QUARANTINED` never become resumable through reconciliation.

The G9 reference layer does not automatically execute those next steps. A future recovery executor must separately prove current authority and artifact identity before any consequence.

## Crash campaign

Deterministic tests cover:

- failure before atomic journal promotion;
- failure after replacement but before directory-fsync completion is reported by a failpoint while leaving only whatever valid target the filesystem has exposed;
- restart from every journal phase;
- repeated restart/reconciliation idempotence;
- state evidence ahead of a `VALIDATED` journal;
- Chrono evidence ahead of a `STATE_COMMITTED` journal;
- witness evidence ahead of a `CHRONO_COMMITTED` journal;
- missing required evidence;
- tampered records and evidence bundles;
- sequence gaps and conflicting duplicates;
- no-double-state-commit classification after `STATE_COMMITTED`.

## Claim boundary

G9 demonstrates tested behavior of the declared local Python reference implementation on the CI filesystem/runtime. It is not a universal storage-durability proof and does not establish behavior for every filesystem, controller cache, virtual-machine stack, network filesystem, kernel, power-loss mode, or hardware failure.

G9 does not:

- mint or restore authority;
- automatically replay a transition;
- create KBI state;
- fabricate a Chrono event or witness;
- enable T4/T5;
- add federation or distributed consensus;
- provide a physical safety case.

The public maturity vector is not automatically promoted merely because G9 passes. Any broader deployment/durability maturity statement requires separate evidence and explicit review.

## Consequences

Positive:

- crash boundaries become explicit and testable;
- exact durable receipt binding prevents cross-transaction/head reuse;
- ambiguous evidence fails closed into quarantine;
- restart classification cannot silently double-commit state;
- recovery logic remains outside authority creation.

Limitations:

- the current recovery layer classifies but does not execute authoritative replay;
- `RecoveryEvidenceBundle` stores verified digest receipts, not the underlying state/Chrono/witness objects;
- storage guarantees remain conditional on the reference OS/filesystem semantics actually provided to the process.
