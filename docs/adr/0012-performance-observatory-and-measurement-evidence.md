# ADR-0012 — Performance Observatory and Measurement Evidence

Status: Accepted for G10 qualification

Date: 2026-09-03

## Context

QIC reached a qualified local G0–G9 software baseline before any accelerator or federation implementation. Performance decisions therefore need measured evidence without introducing a benchmark-only execution path that bypasses authority, invariants, serialization, Chrono, witness, KBI, or recovery behavior.

## Decision

Introduce G10 as a read-only observability layer with three separation rules:

1. **measurement is not authority** — instrumentation observes unchanged callables and returns the original result;
2. **raw evidence is canonical, statistics are derived** — environment/workload/sample records use deterministic integer/string fields and semantic-result digests; floating means/standard deviations are derived views and do not define evidence identity;
3. **optimization follows measured bottlenecks** — accelerator/hardware hypotheses require measured runtime share, scaling evidence, transfer-cost assumptions, and a verification strategy. Algorithmic simplification is considered first.

Prime laws:

- `NoAcceleratorWithoutMeasuredBottleneck`
- `MeasuredBottleneck != AutomaticSiliconCandidate`
- `AlgorithmicImprovementBeforeHardwareAcceleration`

## Workload atlas

The atlas names only live G0–G9 callables and fails closed if a symbol disappears. It does not predeclare Holo/Topo/Knot/federation/accelerator workloads that have not been implemented.

Current atlas classes include canonical serialization/digest, constitutional transition execution, Chrono verification, KBI evidence queries, journal scan, recovery reconciliation, G8 qualification, and aggregate verification.

## Campaign evidence

`PerformanceCampaignStore` persists immutable raw campaign records keyed by campaign ID. Reusing an ID with identical bytes is idempotent; conflicting evidence is rejected. Persisted measurement evidence is not QIC state, authority, epistemic admission, or a bottleneck finding by itself.

CI emits environment-specific G10 raw artifacts. Timing values are not required to match across Python versions; only structural/semantic boundaries are shared.

## Canonical float boundary

The first G10 evidence implementation attempted to place floating statistical fields inside `QIC-CANONICAL/1.0`. CI rejected this because G1 intentionally forbids floats. G10 preserves that law: canonical evidence uses integer/fixed-point identity fields and raw sample digests, while statistical floats remain derived non-identity views.

## First finding

Run `33719689186` measured `canonical.bytes` and `canonical.digest` at sizes 10, 100, and 1000 on CPython 3.12 and 3.13. At size 1000, canonical serialization represented approximately 98.56% and 99.15% of the digest-path median respectively. This supports a narrowly scoped `SERIALIZATION_BOUND` software finding for the current 1000-integer Python digest workload.

The decision is **software canonicalizer optimization first**. No hardware accelerator candidate is admitted from this finding.

## Consequences

Positive:

- performance decisions become evidence-bound;
- semantic-result identity is checked during measurement;
- environment drift is explicit;
- raw evidence is replayable and tamper-detectable;
- benchmark mode does not create a privileged runtime path;
- the first measured result points toward algorithmic optimization rather than premature hardware.

Costs / limits:

- GitHub-hosted runner timings are environment-specific and noisy;
- current cost decomposition uses paired independent medians, not nested-call instrumentation;
- no QIC-wide bottleneck has been established;
- no hardware, federation, T4/T5, security, formal, or deployment maturity is increased.

## Rejected alternatives

- allowing floats into QIC-CANONICAL/1.0 for convenience;
- selecting GPU/FPGA/ASIC/QPU targets before measured runtime-share evidence;
- benchmarking stripped-down paths with assurance gates disabled;
- treating one environment's absolute timing as a portable performance guarantee.
