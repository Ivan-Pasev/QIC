# QIC State

Last updated: 2026-09-03

## Canonical status

**Active slice:** `QIC-G11 — Canonicalizer Algorithmic Optimization + Byte-Identity Preservation + Measured Regression Evidence`

**Status:** QUALIFIED / READY FOR MERGE

**G11 issue:** #30

**G11 PR:** #31

**Current branch:** `qic-g11/canonicalizer-optimization`

**Final qualified head:** `aae57341567b1e4d393222deda5d35e32e06a1f0`

**Final exact-head CI:** `33799262848` — PASS

**Counterbalanced measurement run:** `33798799289` — PASS on measurement head `e3d0f2b612be1861dd66a87e345d35695466c595`

**Release candidate baseline:** `1.0.0rc0`

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Frozen qualified baseline

- G0–G8 merged constitutional implementation/qualification stack.
- RC0 integrated release convergence merged; actual GitHub `v1.0.0rc0` tag/release remains publication-pending until directly verified.
- G9 durable journal/recovery merged and post-merge sealed.
- G10 performance observatory merged and post-merge sealed.
- T4 Physical and T5 Evolutionary remain `NOT_ENABLED`.

## G10 evidence-selected problem

`G10-BF-001 = SERIALIZATION_BOUND`

Scope: the current CPython `canonical.digest` path for a tuple of 1000 integers in two measured GitHub-hosted Linux environments only.

G10 decision: `AlgorithmicImprovementBeforeHardwareAcceleration`.

## G11 candidate

The production `canonical_bytes` path now emits the already-declared typed JSON representation directly, avoiding the intermediate normalized Python object tree used by the frozen G1 implementation.

The frozen implementation remains available as `_canonical_bytes_reference` only for differential qualification.

The candidate preserves exact `QIC-CANONICAL/1.0` bytes across the declared differential corpus. Any future byte divergence remains a release blocker regardless of performance.

## Byte-identity evidence

Differential tests cover existing canonical semantics, Enum/IntEnum, dataclasses, mappings, lists/tuples, sets/frozensets, Unicode/escaping, bytes, unsupported/fail-closed cases, >200 deterministic generated nested values, and the measured tuple-of-1000 hot path.

The final exact-head source suites passed on Python 3.12 and 3.13.

## Counterbalanced measured improvement

Run `33798799289` measured both `reference -> candidate` and `candidate -> reference` orderings in the same job/environment using 3 warmups and 15 measured repetitions per order block.

Artifacts:

- Python 3.12: `9910239274`, digest `sha256:8b28b32bfbc3a9034ba768ca9a74b1168cad5ca366ab7f4e082af7ea5f12f6b7`
- Python 3.13: `9910240220`, digest `sha256:4d698005945f35e63990c19fd0a20a40f9bcd62823c3819af7bc0829509b49e8`

At size 1000:

- Python 3.12 frozen reference median: `892,979 ns`
- Python 3.12 candidate median: `497,965.5 ns`
- measured improvement: `44.2355%`

- Python 3.13 frozen reference median: `895,359 ns`
- Python 3.13 candidate median: `495,893.5 ns`
- measured improvement: `44.6151%`

The improvement direction remains stable when measurement order is reversed in both environments.

## Residual digest-path observation

Same-job independently timed digest measurements estimate optimized canonical serialization at:

- Python 3.12: `950,296 ppm` / `95.0296%` of size-1000 digest-path median
- Python 3.13: `947,894 ppm` / `94.7894%` of size-1000 digest-path median

This is a bounded decomposition estimate, not exact nested instrumentation. The absolute serialization cost is materially reduced, while the narrow residual workload remains serialization-dominant.

## Final qualification

Exact sealed head `aae57341567b1e4d393222deda5d35e32e06a1f0` passed run `33799262848` across:

- Python 3.12 source tests;
- Python 3.13 source tests;
- G10 observatory regressions on both Python versions;
- G11 counterbalanced comparison jobs on both Python versions;
- RC0 wheel and normalized-sdist clean-install verification on both Python versions;
- installed aggregate/qualification checks;
- cross-Python release reproducibility.

## Engineering decision

The algorithmic optimization is admitted on measured evidence and exact-byte compatibility.

No accelerator is selected by G11. Any future optimization or accelerator hypothesis must start from the optimized baseline and preserve canonical byte identity plus all constitutional/recovery/observability gates.

## Public maturity and claim boundary

Public maturity remains:

- semantic: `TESTED`
- evidence: `SUPPORTED`
- formal: `NONE`
- hardware: `NONE`
- deployment: `LOCAL`

G11 is environment-specific software optimization evidence. It does not add federation, hardware qualification, physical control, T4/T5, formal proof, production-security certification, accelerator readiness, or semantic/scientific truth certification.

## Next admissible action

Merge PR #31 only at exact head `aae57341567b1e4d393222deda5d35e32e06a1f0`, then perform post-merge truth sealing before opening the next evidence-selected optimization/research slice.
