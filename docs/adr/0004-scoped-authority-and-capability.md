# ADR-0004 — Scoped Authority and Capability Model

- **Status:** Accepted for G3 implementation
- **Date:** 2026-09-02

## Context

QIC requires explicit authority semantics before runtime transition execution can safely exist. Authority must remain scoped, nontransitive, and inspectable; computational capability cannot silently imply epistemic, physical, or evolutionary authority.

## Decision

G3 introduces four authority domains:

- `A_E` — epistemic
- `A_C` — computational
- `A_P` — physical
- `A_X` — evolution

`AuthorityGrant` is an immutable description of scoped authority. A grant binds a subject and issuer to exact domain, capability, and resource sets. G3 has no wildcard/superuser semantics.

`AuthorityRequirement` defines the exact authority required by a future operation. A grant satisfies a requirement only when the grant is active and every required domain/capability/resource is a subset of the grant.

Direct delegation is also subset-only. A child grant must identify the parent grant, be issued by the parent subject, and may preserve or reduce domains/capabilities/resources but never amplify them.

Revocation is explicit. A revoked grant cannot satisfy requirements or delegate.

## Claim boundary

An `AuthorityGrant` object describes constitutional authority state. Merely possessing, serializing, digesting, or receiving a grant object does not execute an operation, mutate KBI, create physical effects, or prove that an external identity actually controls the named subject. Runtime transition authorization is deferred to G4.

## Identifier policy

Capabilities and resources are explicit lower-case namespaced tokens. `*` and implicit wildcard semantics are rejected by G3.

## Consequences

Positive:

- cross-domain authority is explicit;
- delegation amplification is mechanically testable;
- revocation fails closed;
- future transition execution has a small static authorization primitive;
- authority objects canonicalize/digest under G1.

Costs:

- G3 resource matching is exact rather than hierarchical/pattern-based;
- identity authentication, signatures, expiry/time, and distributed revocation are deferred;
- no runtime execution exists yet.

## Deferred

G3 does not implement transition execution, KBI mutation, Chrono, witness signing, federation, physical control, or identity cryptography.
