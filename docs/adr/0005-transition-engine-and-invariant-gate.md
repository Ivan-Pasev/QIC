# ADR-0005 — Transition Engine and Invariant Gate

- **Status:** Accepted for G4 implementation
- **Date:** 2026-09-02

## Context

G0–G3 established constitutional state, deterministic identity, ontology/maturity, and scoped authority. QIC now needs the first runtime kernel that can bind those objects to a state transition without silently expanding scope into KBI, Chrono, federation, or physical control.

## Decision

G4 introduces a small pure transition engine with immutable `StateSnapshot`, `TransitionSpec`, `TransitionProposal`, and `TransitionOutcome` objects.

Execution order is fixed:

1. resolve the declared operation;
2. reject disabled transition families;
3. compare the proposal's expected state digest to the current state;
4. bind proposal actor to current grant subject;
5. evaluate the G3 authority requirement;
6. execute the registered pure transition rule;
7. evaluate global and operation-scoped invariants;
8. expose the candidate as committed output only if every gate passes.

Any rejected path returns the exact original `StateSnapshot` object as `after_state`.

## Transition families

The runtime mirrors T0–T5. In the G4 reference compute profile, T0–T3 are enabled. T4 Physical and T5 Evolutionary remain `NOT_ENABLED` regardless of whether a caller presents A_P or A_X authority.

## Authority

A grant is evaluated at execution time and its subject must equal the proposal actor. No missing domain/capability/resource is inferred. Revoked grants fail through the G3 authority check.

## Rule and invariant model

Rules and invariants are pure callables in the reference implementation. Rules return either a candidate immutable state or `None` for rejection. Invariants inspect only the candidate state and return a boolean. Persistence, external I/O, signatures, and physical effects are outside G4.

## Atomicity claim

G4's atomicity claim is deliberately narrow: within this in-memory reference kernel, no rejected validation/authority/rule/invariant path exposes a changed `after_state`. This is not yet crash-recovery or durable-transaction atomicity; those require later journal/persistence layers.

## Claim boundary

A successful `TransitionOutcome` demonstrates that the candidate passed the declared G4 structural gates. It does not prove semantic truth, physical safety, external side-effect completion, provenance completeness, or durable persistence.

## Deferred

Chrono and witness persistence are G5. KBI admission is G6. Federation and cyber-physical execution remain later implementation epochs.
