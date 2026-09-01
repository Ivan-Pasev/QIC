# Contributing to QIC

QIC welcomes contributions that improve the implementation, tests, formal models, documentation, evidence quality, and reproducibility of the project.

## Before contributing

Read:

- `README.md`
- `ARCHITECTURE.md`
- `CLAIM_BOUNDARY.md`
- `GOVERNANCE.md`
- `QIC_STATE.md`

## Contribution principles

1. Preserve explicit authority boundaries.
2. Keep generated/derived output separate from canonical state mutation.
3. Prefer deterministic, inspectable reference implementations before adding optimization or acceleration.
4. Add tests with runtime changes.
5. Do not overstate formal, scientific, hardware, or deployment maturity.
6. Keep secrets and private infrastructure out of the public repository.
7. Prefer small coherent PRs that close one traceable implementation slice.

## Pull requests

A good PR includes:

- problem/requirement;
- implementation summary;
- affected invariants or interfaces;
- tests and evidence;
- claim-boundary impact;
- migration/compatibility notes when relevant.

## Architecture changes

Changes to constitutional rules, authority, core state transitions, processor contracts, federation semantics, physical transition semantics, or release evidence should include an ADR in `docs/adr/`.

## Tests

The project will progressively add unit, golden-vector, property-based, adversarial, mutation, recovery, conformance, benchmark, federation, simulation, and hardware-reference test layers. Contributors should use the narrowest layer that actually substantiates the claim.

## Style

Prefer explicit types, deterministic behavior, small interfaces, machine-readable manifests, and human-readable explanations. Avoid hidden authority, magic state mutation, and opaque one-number truth or safety scores.
