# QIC State

Last updated: 2026-09-03

## Canonical status

**Phase:** `QIC-G10 — Performance Observatory + Workload Atlas + Scaling/Bottleneck Evidence`

**Status:** ACTIVE / final qualification pending

**Issue:** #27

**PR:** #28 (draft until exact-head closure gate)

**Branch:** `qic-g10/performance-observatory`

**Qualified frozen baseline:** G0–G9 + RC0

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Frozen baseline

- G0–G7 merged constitutional implementation slices.
- G8 adversarial qualification merged as `b0c4f446dce21317cbd4cfc943633ee57507a8c8`.
- RC0 integrated release convergence merged via PR #21 as `588694dda816c6cb712d1812c6bbe23ca5092198`.
- RC0 publication metadata PR #25 merged as `74acec6c1d6569e04eec51c8745f718009f24d3d`; actual GitHub `v1.0.0rc0` release/tag remains separately publication-pending until directly verified.
- G9 durable journal/recovery merged via PR #23 as `8b297fea49d6dc76c0236fa9cca6bf8d9af7f249`.
- G9 post-merge state seal merged as `4f53e008fa85694b4c0a3c48f262a0290658e87e`.
- T4 Physical and T5 Evolutionary remain `NOT_ENABLED`.

## G10 implemented on active branch

- immutable `PerformanceEnvironment`, `WorkloadDescriptor`, `PerformanceSample`, and derived `PerformanceSummary`;
- explicit warmups versus measured repetitions;
- wall/CPU/optional traced-memory capture;
- semantic-result digest stability and result-preserving measurement;
- `MICROKERNEL` versus `END_TO_END` distinction;
- current G0–G9 workload atlas with fail-closed live-symbol resolution;
- scaling/cost/regression/bottleneck/accelerator-hypothesis evidence models;
- canonical fixed-point policy for performance identity fields;
- immutable raw `CampaignSpec` / `CampaignRecord` and `PerformanceCampaignStore`;
- tamper detection, conflicting campaign rejection, and idempotent identical persistence;
- CI-generated raw performance artifacts on Python 3.12 and 3.13;
- ADR-0012;
- human-readable measured baseline and findings records.

## Canonical-float defect discovered and contained

The first performance-evidence model attempted to include floating statistics/runtime shares inside `QIC-CANONICAL/1.0`. CI correctly failed because G1 forbids floats. G10 preserved the G1 law: canonical performance identity now uses integer/fixed-point fields and raw sample evidence; floating summaries remain derived non-identity views.

## First measured campaign

GitHub Actions run: `33719689186`

Measured source head: `849c78fd4df5d5c0c0881ef7dfb2f5b20a75f61f`

Artifacts:

- Python 3.12: artifact `9879769833`, digest `sha256:0de255c8b52b74df4a5787799d738f698e0a38c415c7efea02fbc5552c812d39`
- Python 3.13: artifact `9879770182`, digest `sha256:58f985f5b620d7e6b3d4143631387b88d43b3e342d2adc5c9b6aa3d6271bef90`

Campaign: canonical serialization and domain-separated digest at sizes 10, 100, and 1000; 2 warmups + 7 measured repetitions; environment-specific timing only.

## First bottleneck finding

`G10-BF-001 = SERIALIZATION_BOUND`

Scope: current Python `canonical.digest` path for a tuple of 1000 integers in the two measured GitHub-hosted Linux environments.

At size 1000, paired medians indicate canonical serialization contributes approximately:

- Python 3.12: `985,568 ppm` / `98.5568%` of digest-path median;
- Python 3.13: `991,476 ppm` / `99.1476%` of digest-path median.

This is a narrow measured software finding, not a QIC-wide bottleneck claim.

## Decision

`AlgorithmicImprovementBeforeHardwareAcceleration`

No GPU, FPGA, ASIC, SIMD, multicore, photonic, or QPU accelerator candidate is admitted from G10-BF-001.

The next optimization target is the software canonicalization algorithm/representation while preserving exact `QIC-CANONICAL/1.0` bytes and the full G1/G8/G9 regression surface.

## Prime laws

`NoAcceleratorWithoutMeasuredBottleneck`

`MeasuredBottleneck != AutomaticSiliconCandidate`

`AlgorithmicImprovementBeforeHardwareAcceleration`

## Claim boundary

G10 adds environment-specific software performance evidence only. It does not increase semantic, formal, hardware, deployment, federation, physical, security, or truth maturity. Public maturity remains semantic `TESTED`, evidence `SUPPORTED`, formal `NONE`, hardware `NONE`, deployment `LOCAL`.

T4/T5 remain disabled. G10 does not create a privileged benchmark path and does not bypass authority, invariants, canonical serialization, Chrono, witness, KBI, qualification, journal, or recovery semantics.

## Closure gate still pending

Before G10 merges:

1. synchronize `TRACEABILITY.yaml` and source/packaged manifests;
2. keep G10 lifecycle `ACTIVE` until exact-head CI is green;
3. require Python 3.12/3.13 source suites;
4. require G10 raw observatory artifact jobs;
5. require both RC0 clean wheel/sdist installed verification paths;
6. require cross-Python RC0 reproducibility;
7. adversarially review PR #28 for measurement/authority/claim-boundary drift;
8. merge only the exact qualified head;
9. perform a post-merge state seal setting G10 to `MERGED`.

## Continuation rule

Preserve RC0 and G9 as frozen qualified baselines. Performance evidence may justify software optimization or a future accelerator hypothesis only within its measured scope; it may not silently promote architecture or maturity.
