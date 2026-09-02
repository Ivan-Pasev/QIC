# ADR-0006 — Chrono and Witness Semantics

- **Status:** Accepted for G5 implementation
- **Date:** 2026-09-02

## Context

G4 can produce deterministic in-memory transition outcomes, but it does not yet preserve causal history. QIC needs a minimal local append-only event/witness layer before KBI state can acquire lineage semantics.

## Decision

G5 introduces two immutable structural records:

- `ChronoEvent` — one causal event with monotonically increasing sequence number and previous-event digest linkage;
- `WitnessRecord` — one unsigned structural witness bound to the corresponding event and its genesis-state or transition-outcome digest.

`ChronoChain` is an immutable reference chain. Appending a G4 `TransitionOutcome` returns a new chain and never rewrites existing events.

Genesis is explicit at sequence `0`. It has no previous-event/witness digest and binds one initial `StateSnapshot` digest. Every later event is a transition event and must:

1. link to the previous event digest;
2. begin from the previous event's resulting state digest;
3. bind the exact G4 proposal/outcome digests;
4. carry accepted/failure semantics consistent with G4;
5. have a witness linked to the previous witness and exact event/outcome digest.

Rejected G4 outcomes are valid historical events. They preserve `before_state_digest == after_state_digest` and therefore record a failed proposal without implying a state commit.

## Verification

The local verifier detects, within this declared in-memory model:

- sequence gaps/reordering;
- deletion or insertion that breaks internal sequence/linkage;
- previous-event or previous-witness digest mismatch;
- causal state discontinuity;
- event mutation that invalidates its witness binding;
- witness/outcome mismatch;
- rejected events that claim a state change.

A hash-linked prefix is still internally valid. Therefore suffix truncation cannot be detected from the retained prefix alone. `ChronoChain.verify` accepts independently retained anchors — expected chain length, expected head-event digest, and/or expected head-witness digest — so a caller that has preserved a prior head can detect truncation relative to that anchor. Without such an anchor, G5 does not claim completeness or recency of the retained chain.

An external G4 outcome can be checked against its event/witness binding with `verifies_outcome`.

## Claim boundary

A valid Chrono chain or witness establishes only structural composition under the declared canonicalization/digest rules. It does **not** establish semantic truth, legal or institutional authority, authenticated identity, nonrepudiation, distributed consensus, trustworthy wall-clock time, durable persistence, crash-recovery atomicity, chain completeness without an external anchor, or successful external/physical effects.

G5 is local and unsigned. Signatures, federation, distributed causal coordinates, durable transaction journaling, and recovery semantics are deferred.

## Consequences

Positive:

- G4 outcomes acquire deterministic causal lineage;
- accepted and rejected proposals are both reconstructible;
- later KBI objects can reference stable event/witness roots;
- tampering with internal chain composition becomes detectable;
- retained external head anchors can detect suffix truncation.

Costs:

- the reference chain is in memory and grows linearly;
- event time is represented by causal sequence, not a trusted timestamp;
- local hash linkage is not consensus or nonrepudiation;
- an unanchored valid prefix cannot prove it is the latest/complete chain.

## Deferred

G5 does not implement KBI claim admission, persistent journal recovery, identity cryptography, federation, FQNP, physical effects, or distributed consensus.
