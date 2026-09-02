# QIC v1.0.0rc0 — Release Candidate Notes

## Release class

`1.0.0rc0` is the first integrated release candidate for the qualified local QIC constitutional genesis stack. It converges G0–G8 into reproducible installable Python artifacts and does not add a new constitutional capability layer.

## Included implementation

The RC0 baseline includes deterministic canonical serialization and domain-separated digests; root ontology and independent maturity vector; scoped non-amplifying authority; deterministic T0–T3 transition/invariant execution with T4/T5 disabled; local Chrono/witness; authority-gated Minimal KBI; installable read/verify CLI; and G8 adversarial qualification with nine structural checks and five modeled critical mutants.

## G8 qualification provenance

G8 merged via PR #19 as `b0c4f446dce21317cbd4cfc943633ee57507a8c8`. Its final report-sealed head `d0416802c58590e67d580826c2868ee14bf74477` passed GitHub Actions run `33657284850` on Python 3.12 and 3.13 before merge.

G8 remains local structural evidence only; it is not formal verification, security certification, hardware qualification, a physical safety case, federation evidence, legal/compliance certification, distributed-consensus evidence, durable crash-recovery proof, or semantic/scientific truth certification.

## RC0 defects discovered and contained

RC0 found that editable-source verification depended on repository-relative registry and claim-metadata paths, so a wheel could build while lacking its verification resources. RC0 packages the public registries, release manifest, and claim boundary under `qic.resources`, and the installed `qic` entry point redirects read-only lookup there. Authority, transition, KBI, Chrono, and G8 semantics are unchanged.

The first artifact-aware claim audit also produced a self-referential false positive by scanning the release adapter's own audit literals. The final adapter preserves G8's original scope and inspects the actual CLI implementation only.

Independent builds initially produced logically identical but byte-different archives because build metadata/timestamps varied. RC0 now fixes the build epoch and deterministically normalizes sdist member order, timestamps, uid/gid, owner names, PAX metadata, and gzip mtime. File bytes and semantic package contents are preserved.

## Qualified artifact evidence

Candidate source head `fef715b716c6e9927e3c1b23b0c35be9daba8715` passed GitHub Actions run `33675312598` with:

- complete source tests on Python 3.12 and 3.13;
- independently built wheel and normalized sdist on both Python versions;
- required packaged-resource inspection;
- clean wheel installation outside the repository checkout;
- clean normalized-sdist installation in a second environment;
- `qic --json verify` PASS from both artifact forms;
- `qic --json verify qualification` PASS from both artifact forms;
- runtime/package metadata version equality at `1.0.0rc0`;
- cross-Python equality of verification evidence and release artifact SHA-256 inventories.

Artifact SHA-256:

- `qic_core-1.0.0rc0-py3-none-any.whl` — `4b6c7af7113db82fbdd55b42e94cbb6a960b35a54eb0ee88876ffa3f3b60b1a6`
- `qic_core-1.0.0rc0.tar.gz` — `4d248bb4aef7ae8892eecdc711e6ef7e82661d8e63f39edb2b2903b85d6a221d`

These hashes were identical across the independently built Python 3.12 and 3.13 artifacts in run `33675312598`.

## Maturity statement

RC0 does not increase the public maturity vector merely because packaging/reproducibility succeeds: semantic `TESTED`, evidence `SUPPORTED`, formal `NONE`, hardware `NONE`, deployment `LOCAL`. T4 Physical and T5 Evolutionary remain `NOT_ENABLED`.

## Explicit nonclaims

RC0 does not claim a quantum computer or quantum advantage result, formal-runtime verification, production security certification, durable crash-recovery guarantees, hardware qualification, physical actuation readiness, federation/distributed consensus, or scientific/universal truth.

## Release decision gate

A GitHub `v1.0.0rc0` prerelease/tag is admissible only after this evidence-sealed source head itself passes the complete exact-head CI again, the full PR diff is reviewed for semantic/maturity expansion, and PR #21 is merged without an intervening source change.
