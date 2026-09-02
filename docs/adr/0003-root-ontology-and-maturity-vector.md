# ADR-0003 — Root Ontology and Vector Maturity

- **Status:** Accepted for G2 implementation
- **Date:** 2026-09-02

## Context

QIC needs stable root object classes and maturity metadata before authority, transition, witness, and release objects can be modeled consistently. A single ordinal maturity ladder is unsafe because simulation, formal modeling, hardware evidence, deployment, and independent replication are different evidence dimensions.

## Decision

QIC freezes seven root ontology classes with stable identifiers:

- STATE
- ACTOR
- OPERATION
- CONSTRAINT
- EVIDENCE
- RESOURCE
- WITNESS

The identifiers are `qic:ontology:<NAME>` and are compatibility-sensitive.

QIC also introduces an immutable five-dimensional `MaturityVector`:

- semantic
- evidence
- formal
- hardware
- deployment

Each dimension has a local ordering used only to compare values inside that dimension. The vector is compared component-wise. No cross-dimension inference exists.

Examples that are intentionally legal:

- hardware=SIMULATED, formal=NONE;
- formal=MACHINE_CHECKED, hardware=NONE;
- deployment=DEPLOYED, evidence=SUPPORTED;
- evidence=INDEPENDENTLY_REPLICATED, deployment=NONE.

## Compatibility

Changing a root ontology identifier or reinterpreting an existing maturity enum value is a compatibility change. New dimensions or incompatible semantics require explicit versioned migration rather than silent reinterpretation.

## Claim boundary

Ontology membership and maturity metadata classify structural/evidence state only. They do not grant truth, authority, provenance correctness, safety, physical validity, or execution rights.

## Legacy G0 labels

`qic.core.maturity.Maturity` remains as a flat non-cumulative label surface for compatibility with G0. G2 `MaturityVector` is the canonical structured model for multi-dimensional maturity requirements. The flat labels must not be treated as an ordinal ladder.

## Deferred

G2 does not implement authority delegation, capability grants, transition execution, KBI admission, Chrono, federation, or physical effects.
