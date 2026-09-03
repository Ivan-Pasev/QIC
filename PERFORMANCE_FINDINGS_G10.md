# QIC G10 — Performance Findings 01

Status: **OBSERVED SOFTWARE BOTTLENECK / NARROW SCOPE**

This finding is limited to the current Python `canonical.digest` workload over a 1000-integer tuple in GitHub-hosted Linux runners. It is not a QIC-wide bottleneck claim and not a hardware recommendation.

## Finding G10-BF-001

`BottleneckClass = SERIALIZATION_BOUND`

Target path:

`qic.core.digest.digest_hex -> qic.core.digest.digest_bytes -> qic.core.canonical.canonical_bytes -> SHA-256`

The digest implementation explicitly invokes `canonical_bytes(value)` before hashing. This allows a paired nested-path comparison using equal payloads from the same campaign policy.

### Evidence

GitHub Actions run: `33719689186`

Measured source head: `849c78fd4df5d5c0c0881ef7dfb2f5b20a75f61f`

Python 3.12 artifact:

- artifact ID `9879769833`
- artifact digest `sha256:0de255c8b52b74df4a5787799d738f698e0a38c415c7efea02fbc5552c812d39`
- environment digest `0a2e0024c2f2713d9c4cc9a596d6c23141626be896df93c50f491800c531b751`

Python 3.13 artifact:

- artifact ID `9879770182`
- artifact digest `sha256:58f985f5b620d7e6b3d4143631387b88d43b3e342d2adc5c9b6aa3d6271bef90`
- environment digest `099d83db13fd0d43828fd24eda537ecbd30f2e46d17832e79f4421c0da2a2ba9`

### Size-1000 paired medians

| Environment | `canonical.bytes` median ns | `canonical.digest` median ns | serialization / digest |
|---|---:|---:|---:|
| CPython 3.12.14 | 1,001,017 | 1,015,675 | 985,568 ppm / 98.5568% |
| CPython 3.13.15 | 906,517 | 914,310 | 991,476 ppm / 99.1476% |

Residual digest-wrapper time from independent medians:

- Python 3.12: 14,658 ns
- Python 3.13: 7,793 ns

The paired campaigns are separate measurements, so these values are estimates rather than instrumented nested-call accounting. The conclusion is accepted only because the dominant share is large and directionally consistent in both supported Python environments at the largest measured scale.

## Adjudication

Observed finding:

`G10-BF-001 = SERIALIZATION_BOUND`

Scope:

- workload: `canonical.digest`
- input: tuple of 1000 integers
- implementation: current CPython QIC canonicalizer/digest pipeline
- environments: the two environment digests above
- evidence class: measured software performance evidence

Not established:

- that serialization dominates every QIC workload;
- that hashing can be ignored at other payload types/scales;
- that this ratio transfers to different CPUs, operating systems, interpreters, or optimized implementations;
- that any hardware accelerator is justified.

## Decision

`AlgorithmicImprovementBeforeHardwareAcceleration` applies.

**No hardware accelerator candidate is admitted from G10-BF-001.**

The next optimization target should be the software canonicalization algorithm and representation strategy. Any optimized implementation must preserve `QIC-CANONICAL/1.0` byte identity and the complete G1/G8/G9 regression surface. Only after an optimized software baseline is measured should GPU/FPGA/ASIC/SIMD/multicore hypotheses be reconsidered.

## Amdahl interpretation

Because the measured serialization share of this one digest workload is approximately 0.986–0.991, accelerating only the non-serialization residual cannot materially improve the whole workload. This reinforces the algorithmic-first decision; it does not predict a realized speedup for a future canonicalizer.
