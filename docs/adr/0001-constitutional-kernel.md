# ADR-0001 — Constitutional Kernel First

- **Status:** Accepted
- **Date:** 2026-09-02

## Context

QIC has a broad architecture spanning epistemic state, cognitive execution, orchestration, federation, scientific closure, cyber-physical control, adaptation, and engineering evolution. Implementing those layers before a small explicit constitutional kernel would make authority, maturity, and evidence boundaries difficult to audit.

## Decision

The public implementation starts with a deliberately small constitutional kernel before higher-level processors.

The first executable surface includes:

- explicit prime laws;
- immutable constitutional snapshot;
- public maturity labels;
- root ontology/transition registry metadata;
- installable package skeleton;
- tests and CI.

Deterministic canonical serialization/digest semantics are intentionally deferred to `QIC-G1` rather than being implied by G0.

## Consequences

Positive:

- public claims can remain narrower than the architecture;
- future KBI/MLCO/Omnius work has a stable authority vocabulary;
- tests can enforce boundary semantics early;
- later formal/runtime work has a smaller refinement target.

Costs:

- early repository capability is intentionally modest;
- architecture documents describe components that are not yet implemented;
- contributors must maintain maturity labels and claim boundaries carefully.

## Rejected alternative

Implement a large agent/orchestration stack first and add governance afterward. Rejected because that would make hidden authority and maturity drift more likely.
