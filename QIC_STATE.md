# QIC State

Last updated: 2026-09-03

## Canonical status

**Completed slice:** `QIC-G10 — Performance Observatory + Workload Atlas + Scaling/Bottleneck Evidence`

**Status:** MERGED / state seal in qualification

**G10 issue:** #27

**G10 PR:** #28 — MERGED

**G10 merge commit:** `4d3d6896091c3b70355168d549ea172f1f92e0c7`

**Qualified G10 head:** `d9e279cd494cd481dbbfeaec8ee4279dd1854276`

**Final G10 CI:** `33720658546` — PASS

**Release candidate baseline:** `1.0.0rc0`

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Frozen qualified baseline

- G0–G8 merged constitutional implementation/qualification stack.
- RC0 integrated release convergence merged; actual GitHub `v1.0.0rc0` tag/release remains separately publication-pending until directly verified.
- G9 durable journal/recovery merged and post-merge sealed.
- G10 performance observatory merged after exact-head qualification.
- T4 Physical and T5 Evolutionary remain `NOT_ENABLED`.

## G10 closure

G10 established a read-only measurement substrate over the existing G0–G9 runtime:

- immutable environment/workload/sample records;
- explicit warmup versus measured repetitions;
- wall/CPU/optional traced-memory observation;
- semantic-result identity enforcement and unchanged workload result;
- workload atlas bound only to live current callables;
- raw immutable campaign evidence persistence with tamper/conflict detection;
- canonical integer/fixed-point performance evidence; floating summaries remain derived views;
- scaling, cost, regression, bottleneck, and accelerator-hypothesis evidence objects;
- CI-emitted raw campaign artifacts on Python 3.12 and 3.13;
- benchmark authority-denial regression proving observability does not bypass G4 authority;
- ADR-0012, traceability, measured baseline, and findings records.

## G10 measured evidence

Initial campaign run: `33719689186`

Measured head: `849c78fd4df5d5c0c0881ef7dfb2f5b20a75f61f`

Initial artifacts:

- Python 3.12 artifact `9879769833`, digest `sha256:0de255c8b52b74df4a5787799d738f698e0a38c415c7efea02fbc5552c812d39`
- Python 3.13 artifact `9879770182`, digest `sha256:58f985f5b620d7e6b3d4143631387b88d43b3e342d2adc5c9b6aa3d6271bef90`

Finding:

`G10-BF-001 = SERIALIZATION_BOUND`

Scope: current CPython `canonical.digest` path for a tuple of 1000 integers in the two measured GitHub-hosted Linux environments only.

Estimated canonical-serialization share of digest-path median:

- Python 3.12: `985,568 ppm` / `98.5568%`
- Python 3.13: `991,476 ppm` / `99.1476%`

This is not a QIC-wide bottleneck claim.

## Decision

`AlgorithmicImprovementBeforeHardwareAcceleration`

No accelerator candidate is admitted from G10-BF-001.

The evidence-selected next slice is **G11 — Canonicalizer Algorithmic Optimization + Byte-Identity Preservation + Measured Regression Evidence**.

G11 must:

1. optimize software canonicalization before any hardware proposal;
2. preserve exact `QIC-CANONICAL/1.0` output bytes and all G1 golden vectors;
3. preserve G8/G9/G10 authority, qualification, recovery, and observability regressions;
4. measure optimized versus frozen G10 baseline under equal semantic work;
5. reject an optimization if canonical bytes differ;
6. admit performance improvement only from measured evidence;
7. reconsider accelerator hypotheses only if a material residual bottleneck remains after software optimization.

## Claim boundary

Public maturity remains semantic `TESTED`, evidence `SUPPORTED`, formal `NONE`, hardware `NONE`, deployment `LOCAL`.

G10 adds environment-specific software performance evidence only. It does not add federation, hardware, physical control, T4/T5, formal proof, production-security certification, or semantic/scientific truth certification.

## Continuation rule

Preserve RC0, G9, and G10 as frozen qualified baselines. The next implementation must be measured algorithmic optimization of the canonicalizer, not premature acceleration.
