# QIC State

Last updated: 2026-09-03

## Canonical status

**Completed slice:** `QIC-G11 — Canonicalizer Algorithmic Optimization + Byte-Identity Preservation + Measured Regression Evidence`

**Status:** MERGED / post-merge state seal in qualification

**G11 issue:** #30

**G11 PR:** #31 — MERGED

**G11 merge commit:** `554e8f0ea6c2a5a187a5cb675a9d25e8fd8da70b`

**Final qualified head:** `17975bcd1659c216404a7d8f5319877dc155ed19`

**Final exact-head CI:** `33799603266` — PASS

**Counterbalanced measurement run:** `33798799289` — PASS on measurement head `e3d0f2b612be1861dd66a87e345d35695466c595`

**Post-merge seal branch:** `qic-g11/post-merge-state-seal`

**Release candidate baseline:** `1.0.0rc0`

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Frozen qualified baseline

- G0–G8 merged constitutional implementation/qualification stack.
- RC0 integrated release convergence merged; actual GitHub `v1.0.0rc0` tag/release remains publication-pending until directly verified.
- G9 durable journal/recovery merged and post-merge sealed.
- G10 performance observatory merged and post-merge sealed.
- G11 canonicalizer algorithmic optimization merged; post-merge truth seal is the current metadata-only action.
- T4 Physical and T5 Evolutionary remain `NOT_ENABLED`.

## G10 evidence-selected problem

`G10-BF-001 = SERIALIZATION_BOUND`

Scope: the current CPython `canonical.digest` path for a tuple of 1000 integers in two measured GitHub-hosted Linux environments only.

G10 decision: `AlgorithmicImprovementBeforeHardwareAcceleration`.

## G11 implementation

The production `canonical_bytes` path emits the already-declared typed JSON representation directly, avoiding the intermediate normalized Python object tree used by the frozen G1 implementation.

The frozen implementation remains available as `_canonical_bytes_reference` only for differential qualification.

Exact `QIC-CANONICAL/1.0` bytes remain the compatibility gate. Any future byte divergence is a release blocker regardless of performance.

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

Exact truth-sealed head `17975bcd1659c216404a7d8f5319877dc155ed19` passed run `33799603266` across:

- Python 3.12 source tests;
- Python 3.13 source tests;
- G10 observatory regressions on both Python versions;
- G11 counterbalanced comparison jobs on both Python versions;
- RC0 wheel and normalized-sdist clean-install verification on both Python versions;
- installed aggregate/qualification checks;
- cross-Python release reproducibility.

PR #31 merged that exact head as `554e8f0ea6c2a5a187a5cb675a9d25e8fd8da70b`.

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

Qualify and merge the metadata-only G11 post-merge state seal. After that, choose G12 from the optimized baseline using measured evidence. The conservative default is residual canonicalization cost characterization / allocation-specialization analysis before any hardware implementation. Any accelerator work must begin as a hypothesis with explicit Amdahl, transfer-cost, and verification evidence—not as an implementation assumption.
