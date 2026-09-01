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

A proved theorem establishes a property of the declared formal model under its assumptions. It does not automatically prove:

- implementation correctness outside the refinement scope;
- physical-device behavior;
- external service behavior;
- scientific truth of modeled assumptions;
- safety in every deployment context.

Formal/runtime conformance claims must identify the modeled transition subset and assumptions.

## Cyber-physical boundary

- Decision != physical actuation.
- Command acknowledgement != observed physical consequence.
- Measurement != interpretation.
- Software simulation evidence must never be labeled measured physical evidence.

Reference cyber-physical work should remain low-consequence until separately engineered, qualified, and commissioned.

## Adaptive/evolution boundary

- Learning may update bounded models/parameters only under declared authority.
- Learning cannot silently rewrite hard safety constraints.
- A generated design cannot directly mutate an operational physical baseline.
- Material hardware change requires engineering change, as-built capture, commissioning, and a successor baseline.

## Heterogeneous/quantum-compute boundary

QIC is designed to support heterogeneous backends including future QPU research interfaces. This does not mean the current public repository contains a quantum computer, a quantum advantage demonstration, or validated quantum hardware.

A QPU output, when such a backend exists, is a computational result requiring the same evidence/admission discipline as other backend results.

## Publication rule

Every public release, benchmark, white paper, or demo should answer:

1. What exactly exists?
2. What was tested?
3. Under which environment and assumptions?
4. What evidence is available?
5. What remains conceptual, simulated, or unverified?

Ambiguity should resolve toward the lower maturity claim.
