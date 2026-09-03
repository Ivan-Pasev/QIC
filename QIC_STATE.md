# QIC State

Last updated: 2026-09-03

## Canonical status

**Active slice:** `QIC-G12 — Residual Canonicalization Cost Characterization + Integer-Tuple Specialization`

**Status:** ACTIVE / closure candidate qualified / documentation seal in progress

**G12 issue:** #33

**G12 PR:** #34 — DRAFT

**Branch:** `qic-g12/residual-canonicalization`

**Frozen baseline:** G11 state-sealed `main` at `36ce69368ad4282c1d546211ade5cc4c8c3ca828`

**Current measured closure-candidate implementation head:** `e1bacf31afa3fc76107d394da2aa95c41fee7d53`

**G12 profile run:** `33803524078` — PASS

**Inherited full CI on implementation head:** `33803524089` — PASS

**Release candidate baseline:** `1.0.0rc0`

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Frozen completed baseline

- G0–G8: merged constitutional implementation/qualification stack.
- RC0: integrated release convergence merged; GitHub tag/release publication remains separately publication-pending until directly verified.
- G9: durable journal/recovery merged and post-merge sealed.
- G10: performance observatory merged and post-merge sealed.
- G11: direct canonical byte emitter merged and post-merge sealed.
- T4 Physical and T5 Evolutionary remain `NOT_ENABLED`.

Public maturity remains:

- semantic: `TESTED`
- evidence: `SUPPORTED`
- formal: `NONE`
- hardware: `NONE`
- deployment: `LOCAL`

## G12 origin

G10 measured a narrowly scoped serialization-dominant `canonical.digest` workload. G11 removed the intermediate normalized object tree and improved the declared path while preserving exact canonical bytes. G11 still left a substantial residual serialization cost, so G12 was opened to characterize software cost before considering acceleration.

Prime engineering laws remain:

- `NoAcceleratorWithoutMeasuredBottleneck`;
- `MeasuredBottleneck != AutomaticSiliconCandidate`;
- `AlgorithmicImprovementBeforeHardwareAcceleration`.

## Measurement correction

The first G12 profiling revision enabled `tracemalloc` during timing and materially changed the serializer path. Those timing values were rejected before any finding was admitted.

The accepted G12 measurement contract uses:

- untraced timing runs;
- separately traced allocation runs;
- semantic-result identity equality across timing and allocation channels;
- exact production-path measurements separated from proxy microkernels;
- proxies explicitly treated as non-attributive.

The rejected first run is retained only as a methodological negative result.

## G12 residual characterization

Corrected characterization run: `33802554652` on head `7b9ef7b49421e448f3cd7b2cfafbcc951c16e933`.

At size 1000 before the G12 specialization:

- Python 3.12 `canonical_bytes`: `554,250 ns` median;
- Python 3.13 `canonical_bytes`: `560,508 ns` median;
- traced peak allocation: `180,884 B` in both environments;
- independent integer-leaf proxy: `536,061 ns` / `481,356 ns`;
- integer-text proxy: `133,895 ns` / `135,300 ns`;
- pre-encoded join proxy: `11,881 ns` / `12,768 ns`.

Bounded finding G12-F1: for this homogeneous integer-tuple workload, repeated per-element integer emission/dispatch and temporary-byte allocation are stronger optimization targets than the final join alone. This is a supported hypothesis, not exact nested time attribution.

## Reference candidate adjudication

G12 measured two byte-identical software-only candidates under run `33802909806`:

1. growing `bytearray` emitter;
2. flattened-parts + final join.

At size 1000 the growing-buffer candidate improved latency by about `43.23%` / `40.91%` with traced peak allocation of `60,636 B`.

The parts-join candidate was slightly faster but used approximately `418,707 B` traced peak allocation. It was therefore rejected as the balanced production choice.

No native or hardware accelerator was selected.

## G12 production specialization

The evidence-selected production specialization applies only to homogeneous tuples satisfying `type(item) is int`.

It:

- emits the canonical envelope and tuple representation into one growing buffer;
- validates tuple membership during the same emission pass;
- rolls back the attempted buffer and delegates to the generic G11 path on the first non-plain-int element;
- excludes `bool`, `IntEnum`, mixed tuples and other subtype cases from the specialization;
- leaves every other declared canonical type on the generic path;
- preserves the frozen G1 implementation as the exact differential oracle.

No canonical byte format changed.

## Current closure-candidate measurement

Implementation head `e1bacf31afa3fc76107d394da2aa95c41fee7d53` passed G12 profile run `33803524078`.

Artifacts:

- Python 3.12: `9911983142`, digest `sha256:fe5d2a5601fee1860b711fcd9fa1cafe87d809704d4d30a70fa35cfdc35bfb07`;
- Python 3.13: `9911984318`, digest `sha256:6a7e35902d6aeff397545f6adb46be554d0776bb1bbb19017432a0917a835124`.

At size 1000:

- Python 3.12 production median: `319,507 ns`;
- Python 3.13 production median: `268,463 ns`;
- traced peak allocation: `60,608 B` in both environments.

The balanced standalone bytearray reference measured `320,538 ns` / `259,759 ns`. The production/reference difference is within about ±3.3%, so further micro-polishing of this design is not justified by these runner-bound measurements.

## Frozen-G1 same-job differential

Inherited full CI `33803524089` measured the current production implementation against the frozen G1 reference under the same counterbalanced job design.

Artifacts:

- Python 3.12: `9911991159`, digest `sha256:5b5696f53725ae457e97e47ea7b0224f009a74e03872cc430a726a7a928dd4d1`;
- Python 3.13: `9911995303`, digest `sha256:7033a0bcfd516f7df0e2806629bf32af748c7269cdd43e2a6adeaddb3b8f363b`.

Size-1000 counterbalanced medians:

- Python 3.12 frozen G1: `921,496 ns`; G12 current: `312,493 ns`; improvement: `66.09%`;
- Python 3.13 frozen G1: `893,526.5 ns`; G12 current: `328,540.5 ns`; improvement: `63.23%`.

Exact result bytes matched in every measured pair.

Python 3.12 independently timed digest median was `336,468 ns`, yielding a bounded serialization-share estimate of `928,745 ppm` / `92.87%`.

Python 3.13 independently timed digest median (`325,571 ns`) was slightly below the independently timed serializer median, so the campaign correctly emitted no serialization-share estimate rather than inventing a negative remainder.

## Full inherited qualification

Exact implementation head `e1bacf31afa3fc76107d394da2aa95c41fee7d53` passed CI run `33803524089` across:

- source tests on Python 3.12 and 3.13;
- canonical differential/golden tests;
- G10 observatory regressions;
- G11 frozen-reference comparison regressions;
- RC0 wheel and normalized-sdist clean installs on both Python versions;
- installed aggregate/qualification checks;
- cross-Python release reproducibility.

## Engineering decision

The one-pass growing-buffer homogeneous plain-int tuple specialization is the G12 closure candidate.

The evidence rejects:

- proxy ratios as exact nested attribution;
- timing under `tracemalloc` as performance evidence;
- the high-allocation parts-join candidate as the balanced production choice;
- premature C/Rust/SIMD/GPU/FPGA/ASIC/QPU work.

Residual serialization remains material for the declared workload, but timing share alone is not sufficient to select acceleration.

## Claim boundary

G12 adds a narrowly scoped byte-identical software specialization and environment-specific performance/allocation evidence only. It does not add federation, distributed consensus, physical control, T4/T5, formal proof, production-security certification, hardware qualification, accelerator readiness, broad deployment readiness, or semantic/scientific truth certification.

## Next admissible action

Complete ADR/traceability/manifest/state sealing for PR #34, then require a new exact-head full CI plus G12 profile because documentation changes move the head. Only after that may PR #34 leave draft and merge. Post-merge, perform a metadata truth seal before selecting G13 from the measured optimized baseline.
