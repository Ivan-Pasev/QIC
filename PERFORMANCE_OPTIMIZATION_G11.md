# QIC G11 — Canonicalizer Algorithmic Optimization Evidence

Status: **MEASURED IMPROVEMENT / BYTE IDENTITY PRESERVED / HARDWARE NOT SELECTED**

## Evidence binding

Qualified measurement head before report sealing: `e3d0f2b612be1861dd66a87e345d35695466c595`

GitHub Actions run: `33798799289` — PASS across Python 3.12/3.13 source tests, G10 observatory regressions, G11 comparison jobs, RC0 wheel/sdist clean-install verification, installed qualification, and cross-Python reproducibility.

Counterbalanced comparison artifacts:

- Python 3.12: artifact `9910239274`, digest `sha256:8b28b32bfbc3a9034ba768ca9a74b1168cad5ca366ab7f4e082af7ea5f12f6b7`
- Python 3.13: artifact `9910240220`, digest `sha256:4d698005945f35e63990c19fd0a20a40f9bcd62823c3819af7bc0829509b49e8`

Each order block used 3 warmups and 15 measured repetitions. The campaign measured both `reference -> candidate` and `candidate -> reference` orderings to reduce systematic ordering bias.

## Optimization

The production `canonical_bytes` path now emits the already-declared `QIC-CANONICAL/1.0` typed JSON bytes directly rather than first allocating the full normalized Python object tree and then serializing that tree with `json.dumps`.

The frozen G1 object-tree implementation remains available only as `_canonical_bytes_reference` for differential qualification.

No canonical format, type policy, digest policy, authority rule, transition rule, durability rule, or maturity dimension changed.

## Byte-identity qualification

The candidate is byte-for-byte identical to the frozen G1 reference across:

- existing G1 golden-compatible scalar/container behavior;
- Enum and IntEnum identity;
- dataclasses;
- mappings and deterministic key ordering;
- sets/frozensets and canonical encoded-item ordering;
- Unicode and escaped strings;
- bytes;
- fail-closed floats, unsupported values, and non-string mapping keys;
- more than 200 deterministic generated nested values;
- the measured tuple-of-1000-integers hot path.

Any byte divergence remains a release blocker.

## Counterbalanced measured result

### CPython 3.12.14

| Size | Frozen reference median | Direct emitter median | Improvement |
|---:|---:|---:|---:|
| 10 | 15,366 ns | 6,729 ns | 56.21% |
| 100 | 96,658 ns | 52,106.5 ns | 46.09% |
| 1000 | 892,979 ns | 497,965.5 ns | 44.24% |

At size 1000 the order-specific medians were:

- reference-first: reference 897,445 ns; candidate 504,384 ns
- candidate-first: candidate 491,547 ns; reference 888,513 ns

### CPython 3.13.15

| Size | Frozen reference median | Direct emitter median | Improvement |
|---:|---:|---:|---:|
| 10 | 15,434.5 ns | 6,926.5 ns | 55.12% |
| 100 | 96,022.5 ns | 55,888.5 ns | 41.80% |
| 1000 | 895,359 ns | 495,893.5 ns | 44.62% |

At size 1000 the order-specific medians were:

- reference-first: reference 896,936 ns; candidate 496,194 ns
- candidate-first: candidate 495,593 ns; reference 893,782 ns

The direction and magnitude of the size-1000 improvement are therefore stable under reversed measurement order in both supported Python environments.

## Residual digest-path observation

The same G11 job separately measured the optimized `digest_hex` path, which calls `canonical_bytes` before SHA-256 hashing. Because serialization and digest were independently timed rather than instrumented inside one invocation, the following is a bounded decomposition estimate rather than exact attribution.

At size 1000:

- Python 3.12 optimized canonical median: 497,965.5 ns
- Python 3.12 digest median: 524,011 ns
- estimated serialization share: 950,296 ppm / 95.0296%

- Python 3.13 optimized canonical median: 495,893.5 ns
- Python 3.13 digest median: 523,153 ns
- estimated serialization share: 947,894 ppm / 94.7894%

Thus G10-BF-001 is materially reduced in absolute cost but remains directionally serialization-dominant for this exact size-1000 CPython tuple workload.

## Engineering decision

`AlgorithmicImprovementBeforeHardwareAcceleration` remains satisfied.

The software optimization is admitted because it preserves exact canonical bytes and demonstrates a large same-environment measured improvement. No hardware accelerator is selected by G11. The residual finding is still narrow and does not establish a QIC-wide bottleneck.

A later optimization or accelerator hypothesis may be considered only from the optimized baseline and only with explicit transfer-cost and verification evidence.

## Claim boundary

G11 demonstrates measured software improvement for the declared canonicalization workload in the two GitHub-hosted CPython environments and preserves the tested canonical byte identity surface. It is not an algorithmic complexity proof, cross-platform performance guarantee, formal verification, hardware qualification, accelerator recommendation, production benchmark certification, federation result, T4/T5 capability, or semantic/scientific truth claim.
