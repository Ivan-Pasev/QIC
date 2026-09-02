# QIC v1.0.0rc0 — Release Candidate Notes

## Release class

`1.0.0rc0` is the first integrated release candidate for the qualified local QIC constitutional genesis stack. It converges G0–G8 into an installable Python artifact and does not add a new constitutional capability layer.

## Included implementation

The RC0 baseline includes:

- deterministic canonical serialization and domain-separated digests;
- root ontology and independent maturity vector;
- scoped non-amplifying authority domains and grants;
- deterministic T0–T3 transition/invariant kernel with T4/T5 disabled;
- local append-only Chrono/witness structures and explicit external-anchor limitation;
- authority-gated Minimal KBI with explicit claim/evidence/contradiction lifecycle;
- installable read/verify CLI;
- G8 adversarial constitutional qualification with nine structural checks and five modeled critical mutants.

## G8 qualification provenance

G8 merged via PR #19 as `b0c4f446dce21317cbd4cfc943633ee57507a8c8`.

The final report-sealed G8 head `d0416802c58590e67d580826c2868ee14bf74477` passed GitHub Actions run `33657284850` on Python 3.12 and 3.13 before merge.

G8 qualification remains local structural evidence only; it is not formal verification, security certification, hardware qualification, a physical safety case, federation evidence, legal/compliance certification, distributed-consensus evidence, durable crash-recovery proof, or semantic/scientific truth certification.

## RC0 packaging correction

RC0 discovered that editable-source verification relied on repository-relative registry and claim-metadata paths. That could make a built wheel incomplete even while editable CI stayed green.

RC0 therefore packages the public registries, release manifest, and claim boundary under `qic.resources` and routes the installed `qic` entry point through a read-only release wrapper. The wrapper changes metadata lookup only; authority, transition, KBI, Chrono, and qualification semantics are not relaxed or replaced.

## Artifact qualification contract

The RC0 CI gate must, on Python 3.12 and 3.13:

1. pass the complete source test suite;
2. build wheel and source distribution;
3. verify required release resources exist inside the wheel;
4. install the wheel into a clean virtual environment;
5. execute from outside the repository checkout;
6. pass `qic --json verify`;
7. pass `qic --json verify qualification`;
8. confirm package metadata and runtime version both equal `1.0.0rc0`;
9. generate SHA-256 inventories for release artifacts;
10. upload the artifacts and verification evidence for inspection.

## Maturity statement

RC0 does not increase the public maturity vector merely because packaging succeeds.

- semantic: `TESTED`
- evidence: `SUPPORTED`
- formal: `NONE`
- hardware: `NONE`
- deployment: `LOCAL`

T4 Physical and T5 Evolutionary remain `NOT_ENABLED`.

## Explicit nonclaims

RC0 does not claim:

- a quantum computer or quantum advantage result;
- formal-runtime verification;
- production security certification;
- durable crash-recovery guarantees;
- hardware qualification;
- physical actuation readiness;
- federation or distributed consensus;
- scientific or universal truth.

## Release decision

A GitHub `v1.0.0rc0` prerelease/tag is admissible only after the exact reviewed RC0 head passes both source and built-artifact gates and its uploaded evidence is inspected. Any runtime-semantic fix required during RC0 reopens the relevant G8 qualification checks.
