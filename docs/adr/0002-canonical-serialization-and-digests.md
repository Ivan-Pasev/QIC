# ADR-0002 — Canonical Serialization and Domain-Separated Digests

- **Status:** Accepted for G1 implementation
- **Date:** 2026-09-02

## Context

QIC needs byte-stable representations before later work can safely bind state roots, witnesses, Chrono entries, formal/runtime vectors, or federated capsules to digests. General Python serialization is not suitable because object identity, mapping order, float rendering, implementation details, and unsupported types can introduce ambiguity.

## Decision

QIC-G1 defines `QIC-CANONICAL/1.0` as a deliberately narrow typed canonical representation encoded as deterministic UTF-8 JSON.

The first version supports:

- null;
- booleans;
- arbitrary-precision integers encoded as decimal strings;
- Unicode strings;
- bytes encoded as lowercase hexadecimal;
- lists and tuples as distinct types;
- sets/frozensets sorted by the canonical bytes of their normalized members;
- mappings with string keys sorted lexicographically;
- dataclass instances with explicit fully-qualified class identity and named fields;
- enum instances with explicit fully-qualified class identity, member name, and canonical value.

Floats are rejected. Non-string mapping keys are rejected. Unknown types are rejected. There is no fallback to `repr()`, pickle, object IDs, or arbitrary coercion.

## Digest semantics

`QIC-DIGEST/1.0` uses SHA-256 over:

```text
QIC-DIGEST/1.0 NUL <domain UTF-8> NUL <QIC-CANONICAL/1.0 bytes>
```

The domain must be non-empty and may not contain NUL. This provides explicit domain separation so identical canonical payloads used as different object classes do not automatically receive the same QIC digest.

## Claim boundary

A matching digest demonstrates canonical byte identity under the declared version and digest domain. It does **not** demonstrate:

- semantic truth;
- epistemic admission;
- authority;
- provenance correctness;
- formal proof;
- physical measurement validity;
- safety;
- execution success.

## Compatibility

The version strings are part of the wire semantics. Any incompatible encoding change requires a new canonicalization/digest version rather than silently changing `1.0`.

## Consequences

Positive:

- state and witness roots can later be reproducible across processes;
- ambiguous types fail closed;
- list/tuple and bool/int distinctions are preserved;
- set order is made deterministic;
- digest use is semantically scoped by explicit domains.

Costs:

- the supported type surface is intentionally narrow;
- floats require a separate future numeric policy;
- class identity for dataclasses/enums is sensitive to intentional module/class renames;
- cross-language implementations must reproduce the exact tagged representation and UTF-8 JSON rules.

## Deferred

G1 does not define state-transition semantics, authority, KBI admission, Chrono chaining, federation capsules, physical evidence, or a generalized numeric/decimal standard.
