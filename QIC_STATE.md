# QIC State

Last updated: 2026-09-02

## Canonical status

**Phase:** Release Convergence

**Active slice:** `QIC-v1 RC0 — Integrated genesis release convergence`

**Release candidate:** `1.0.0rc0`

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Qualified baseline

- G0–G7 are merged constitutional implementation slices.
- G8 merged via PR #19 as `b0c4f446dce21317cbd4cfc943633ee57507a8c8`.
- G8 report-sealed head `d0416802c58590e67d580826c2868ee14bf74477` passed Python 3.12/3.13 run `33657284850`.
- T4 Physical and T5 Evolutionary remain `NOT_ENABLED`.
- RC0 Issue #20 and PR #21 operate on branch `qic-v1/rc0-convergence`.

## RC0 release engineering

RC0 adds no constitutional capability. It normalizes package version to `1.0.0rc0`, packages manifest/claim-boundary/registries under `qic.resources`, uses a read-only installed-artifact CLI adapter, and requires source↔package parity.

CI now requires, on Python 3.12 and 3.13, source-suite PASS, wheel+sdist build, deterministic sdist normalization, required resource inspection, clean wheel install outside checkout, clean normalized-sdist install, aggregate verification PASS, G8 qualification PASS, runtime/metadata version equality, SHA-256 inventory generation, and cross-Python equality of artifact hashes and verification evidence.

## RC0 defects discovered and contained

1. Editable-source verification depended on repository-relative metadata; packaged resources now remove that dependency.
2. The first artifact-aware claim audit self-detected its own forbidden-token literals; the final adapter restores G8's original audit scope over the real CLI implementation.
3. Independent archives initially differed only in container metadata. A fixed build epoch made wheels reproducible, and deterministic sdist normalization now fixes tar/gzip member metadata without changing source file bytes.

## Current evidence

Candidate head `fef715b716c6e9927e3c1b23b0c35be9daba8715` passed full GitHub Actions run `33675312598`:

- source tests: PASS on Python 3.12 and 3.13;
- wheel clean-install verification: PASS on both;
- normalized-sdist clean-install verification: PASS on both;
- aggregate `qic --json verify`: PASS;
- `qic --json verify qualification`: PASS;
- cross-Python reproducibility job: PASS.

Reproducible artifact SHA-256 values:

- wheel: `4b6c7af7113db82fbdd55b42e94cbb6a960b35a54eb0ee88876ffa3f3b60b1a6`
- normalized sdist: `4d248bb4aef7ae8892eecdc711e6ef7e82661d8e63f39edb2b2903b85d6a221d`

The release notes/state sealing these values moved the branch head after that run. Therefore RC0 is still **ACTIVE** until the exact evidence-sealed head passes the same complete gate and the PR diff is reviewed.

## Claim boundary

RC0 release engineering does not upgrade maturity. Public maturity remains semantic `TESTED`, evidence `SUPPORTED`, formal `NONE`, hardware `NONE`, deployment `LOCAL`. RC0 is not formal verification, security certification, hardware qualification, physical-control readiness, federation/distributed-consensus evidence, durable crash-recovery proof, or semantic/scientific truth certification.

## Next admissible action

Run the complete exact-head RC0 CI after evidence sealing; inspect the full PR diff; merge only the reviewed green head; then decide/create the `v1.0.0rc0` GitHub prerelease/tag and synchronize the canonical Drive handoff.

## Continuation rule

Every substantial implementation/release change should update this file if phase, maturity, blockers, or next action change. Public claims must remain consistent with `CLAIM_BOUNDARY.md`, `QIC_MANIFEST.json`, G8 qualification, and RC0 release evidence.
