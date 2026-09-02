# QIC Claim Boundary

This document defines how QIC communicates maturity, evidence, and system claims.

## Prime rule

**No plane may claim operational maturity beyond its actual evidence.**

## Maturity classes

QIC uses explicit maturity labels rather than treating design intent as implementation fact.

- **CONCEPTUAL** — architecture/design only.
- **IMPLEMENTED** — code/artifact exists.
- **TESTED** — implementation has relevant automated/manual test evidence.
- **FORMALLY_MODELED** — properties are represented in a formal model; this does not imply the whole runtime is formally verified.
- **SIMULATED** — behavior demonstrated in a simulator/digital model.
- **HARDWARE_TESTED** — behavior demonstrated on identified physical hardware.
- **DEPLOYED** — running in a defined operational environment.
- **INDEPENDENTLY_REPLICATED** — result reproduced by an independent implementation, apparatus, or party under declared criteria.

These classes are not automatically cumulative; a release manifest must state what each claim actually has.

## Epistemic boundary

- Proposal != canonical knowledge.
- Derived relation != canonical relation.
- Model output != observation.
- Simulation != physical measurement.
- Signature != truth.
- Remote state != local authority.

KBI admission is a separate transition from generation, derivation, receipt, or recommendation.

## Formal-method boundary

A proved theorem establishes a property of the declared formal model under its assumptions. It does not automatically prove implementation correctness outside the refinement scope, physical-device behavior, external service behavior, scientific truth of modeled assumptions, or safety in every deployment context.

## Cyber-physical boundary

- Decision != physical actuation.
- Command acknowledgement != observed physical consequence.
- Measurement != interpretation.
- Software simulation evidence must never be labeled measured physical evidence.

## Heterogeneous/quantum-compute boundary

QIC is designed to support heterogeneous backends including future QPU research interfaces. This does not mean the current public repository contains a quantum computer, a quantum advantage demonstration, or validated quantum hardware.

## Publication rule

Every public release should identify what exists, what was tested, the environment and assumptions, available evidence, and what remains conceptual, simulated, or unverified. Ambiguity resolves toward the lower maturity claim.
