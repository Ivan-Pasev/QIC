# QIC G10 — Measured Performance Baseline 01

Status: **MEASURED / NARROW BOTTLENECK ADJUDICATED**

This record summarizes the first bounded G10 performance campaign. It is environment-specific measurement evidence, not a portable speed guarantee, not a hardware/accelerator result, and not a maturity promotion.

## Evidence binding

GitHub Actions run: `33719689186`

Measured source head: `849c78fd4df5d5c0c0881ef7dfb2f5b20a75f61f`

Artifacts:

- Python 3.12: `qic-g10-observatory-py3.12`, artifact ID `9879769833`, artifact digest `sha256:0de255c8b52b74df4a5787799d738f698e0a38c415c7efea02fbc5552c812d39`
- Python 3.13: `qic-g10-observatory-py3.13`, artifact ID `9879770182`, artifact digest `sha256:58f985f5b620d7e6b3d4143631387b88d43b3e342d2adc5c9b6aa3d6271bef90`

Campaign policy: 2 warmups, 7 measured repetitions per scale point, `FULL_DECLARED_PATH`.

No timing value is a cross-environment reproducibility target. Raw per-repetition integer evidence and semantic-result digests are contained in the uploaded artifacts; floating summaries below are derived views only.

## Environments

### Python 3.12

- CPython `3.12.14`
- Linux `6.17.0-1022-azure`
- machine `x86_64`
- logical CPUs `4`
- environment digest `0a2e0024c2f2713d9c4cc9a596d6c23141626be896df93c50f491800c531b751`

### Python 3.13

- CPython `3.13.15`
- Linux `6.17.0-1022-azure`
- machine `x86_64`
- logical CPUs `4`
- environment digest `099d83db13fd0d43828fd24eda537ecbd30f2e46d17832e79f4421c0da2a2ba9`

Both environments used configuration digest:

`068fb7659f9868dac866bc946dc1f3cb5effbd12f5e7b58e6e0ab667c944a3c7`

## Median wall-time observations

| Workload | Size | Python 3.12 median ns | Python 3.13 median ns |
|---|---:|---:|---:|
| `canonical.bytes` | 10 | 17,784 | 15,713 |
| `canonical.bytes` | 100 | 125,866 | 103,196 |
| `canonical.bytes` | 1000 | 1,001,017 | 906,517 |
| `canonical.digest` | 10 | 21,591 | 16,605 |
| `canonical.digest` | 100 | 108,694 | 99,851 |
| `canonical.digest` | 1000 | 1,015,675 | 914,310 |

## Scaling observations

The measured medians increase monotonically with corpus size in both environments.

Approximate 10→100 / 100→1000 median ratios:

- Python 3.12 `canonical.bytes`: `7.08×` / `7.95×`
- Python 3.13 `canonical.bytes`: `6.57×` / `8.78×`
- Python 3.12 `canonical.digest`: `5.03×` / `9.34×`
- Python 3.13 `canonical.digest`: `6.01×` / `9.16×`

These observations are consistent with work increasing materially with input size and becoming closer to linear-in-size behavior at the larger measured interval.

## Paired nested-path decomposition

The digest path explicitly calls `canonical_bytes(value)` before SHA-256 hashing. At size 1000, equal-payload paired medians therefore provide a bounded estimate of the serialization share of the total digest path:

- Python 3.12: `1,001,017 / 1,015,675 = 985,568 ppm = 98.5568%`
- Python 3.13: `906,517 / 914,310 = 991,476 ppm = 99.1476%`

Residual digest-wrapper medians:

- Python 3.12: `14,658 ns`
- Python 3.13: `7,793 ns`

This comparison uses independent medians rather than nested instrumentation, so it is an estimate. The share is nevertheless large and directionally consistent in both supported Python environments.

## Bottleneck adjudication

`G10-BF-001 = SERIALIZATION_BOUND`

Scope: current CPython `canonical.digest` path for a tuple of 1000 integers in the two measured GitHub-hosted Linux environments only.

This does not establish a QIC-wide bottleneck and does not imply the same share for other payload types, scales, interpreters, CPUs, or future implementations.

## Decision

`AlgorithmicImprovementBeforeHardwareAcceleration`.

No `AcceleratorCandidate` is admitted from this campaign. The next optimization target is the software canonicalization algorithm/representation while preserving exact `QIC-CANONICAL/1.0` bytes and the complete G1/G8/G9 regression surface.

## Constitutional measurement boundary

G10 includes an explicit measured unauthorized-transition test. When `TransitionEngine.execute` is observed with an insufficient grant, every measured repetition must remain `AUTHORITY_DENIED` and preserve the exact original state object. Benchmark instrumentation therefore does not create a tested authority-bypass mode.
