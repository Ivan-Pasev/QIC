# QIC G12 — Residual Canonicalization Cost Characterization + Integer-Tuple Specialization

Status: **ACTIVE / closure candidate qualified; pending documentation-sealed exact-head CI and merge**

Issue: #33  
Draft PR: #34  
Frozen baseline: G11 state-sealed `main` at `36ce69368ad4282c1d546211ade5cc4c8c3ca828`

## Mission

Characterize the residual G11 canonicalization cost before considering acceleration, then admit only a byte-identical software optimization directly supported by measured evidence.

The governing laws remain:

- `NoAcceleratorWithoutMeasuredBottleneck`;
- `MeasuredBottleneck != AutomaticSiliconCandidate`;
- `AlgorithmicImprovementBeforeHardwareAcceleration`;
- exact `QIC-CANONICAL/1.0` byte identity is release-blocking.

## Measurement correction

The first G12 campaign revision enabled `tracemalloc` during timing and materially perturbed the serializer path. Those timings were rejected before any finding was admitted.

The qualified campaign separates channels:

- timing: `trace_memory=False`;
- allocation: independent `trace_memory=True` run;
- semantic result identity must match between channels;
- proxy timings are never interpreted as exact nested attribution.

The contaminated first timing run remains a methodological negative result.

## G12-F1 — residual-cost characterization

Qualified corrected characterization: run `33802554652`, head `7b9ef7b49421e448f3cd7b2cfafbcc951c16e933`.

Artifacts:

- Python 3.12: `9911616821`, `sha256:9d8f787450dc77e31bf6afd45e182ec6aae3c9a68487ff7d36df543bed7fb731`;
- Python 3.13: `9911621528`, `sha256:195741564378485b2726b1f8375eec57b05ed0994ba2f7ca7b732c9c110c5870`.

At size 1000 before the G12 production specialization:

| measurement | Python 3.12 | Python 3.13 |
|---|---:|---:|
| production `canonical_bytes` | 554,250 ns | 560,508 ns |
| `digest_hex` end path | 574,107 ns | 583,800 ns |
| production traced peak allocation | 180,884 B | 180,884 B |
| integer-leaf batch proxy | 536,061 ns | 481,356 ns |
| integer text proxy | 133,895 ns | 135,300 ns |
| pre-encoded comma join proxy | 11,881 ns | 12,768 ns |

Finding: the declared integer-tuple workload is far more consistent with repeated per-element integer emission/dispatch and temporary-byte allocation than with the final comma join alone.

Evidence class: **SUPPORTED HYPOTHESIS**, because independent proxies are not nested stage attribution.

## G12-F2 — byte-identical software reference candidates

Run `33802909806`, head `b06cab566230a74b93a08854c5bca0dc3a256f96` tested two software-only reference candidates. Both were byte-identical to production for declared sizes 10/100/1000.

At size 1000:

| candidate | Py3.12 improvement | Py3.13 improvement | traced peak allocation |
|---|---:|---:|---:|
| growing `bytearray` emitter | 43.23% | 40.91% | 60,636 B |
| flattened parts + final join | 45.43% | 44.09% | 418,707 B |

The parts-join experiment was not selected despite slightly lower latency because its measured peak allocation exceeded the balanced bytearray candidate by more than 6×.

Decision: select the growing-buffer design for a guarded production experiment; select no native or hardware accelerator.

## Production specialization

G12 adds a narrow specialization for homogeneous tuples satisfying `type(item) is int`.

The specialization:

- emits the canonical envelope and tuple representation into one growing `bytearray`;
- validates plain-int membership during the same emission pass;
- rolls back and uses the generic G11 path if a non-plain-int element is encountered;
- therefore excludes `bool`, `IntEnum`, mixed tuples, and other subtype cases from the fast path;
- keeps every other declared canonical type on the G11 generic emitter;
- preserves the frozen G1 reference as the differential byte oracle.

No canonical format changed.

## Final production characterization

Current closure-candidate head: `e1bacf31afa3fc76107d394da2aa95c41fee7d53`.

G12 profile run `33803524078` — PASS on Python 3.12 and 3.13.

Artifacts:

- Python 3.12: `9911983142`, `sha256:fe5d2a5601fee1860b711fcd9fa1cafe87d809704d4d30a70fa35cfdc35bfb07`;
- Python 3.13: `9911984318`, `sha256:6a7e35902d6aeff397545f6adb46be554d0776bb1bbb19017432a0917a835124`.

Size-1000 production result:

| environment | production median | traced peak allocation | bytearray reference median |
|---|---:|---:|---:|
| Python 3.12 | 319,507 ns | 60,608 B | 320,538 ns |
| Python 3.13 | 268,463 ns | 60,608 B | 259,759 ns |

The production and balanced reference candidate are within approximately ±3.3%. Further micro-polishing of this design is not justified from these runner-bound measurements.

The faster flattened-parts reference remains rejected as the production choice because its size-1000 traced peak allocation is approximately `418,707 B`.

## Final frozen-G1 differential qualification

Inherited counterbalanced comparison on the same closure-candidate head ran under full CI `33803524089`.

Artifacts:

- Python 3.12 G11/G1 comparison artifact `9911991159`, digest `sha256:5b5696f53725ae457e97e47ea7b0224f009a74e03872cc430a726a7a928dd4d1`;
- Python 3.13 G11/G1 comparison artifact `9911995303`, digest `sha256:7033a0bcfd516f7df0e2806629bf32af748c7269cdd43e2a6adeaddb3b8f363b`.

At size 1000:

| environment | frozen G1 median | current G12 median | improvement | digest median | serialization-share estimate |
|---|---:|---:|---:|---:|---:|
| Python 3.12 | 921,496 ns | 312,493 ns | **66.09%** | 336,468 ns | 928,745 ppm / 92.87% |
| Python 3.13 | 893,526.5 ns | 328,540.5 ns | **63.23%** | 325,571 ns | not emitted |

Exact bytes matched the frozen reference in every measured pair.

For Python 3.13 the independently timed digest median was slightly below the independently timed serializer median, so the campaign correctly emitted no serialization-share estimate rather than manufacturing a negative/nonphysical remainder. This is an evidence-quality feature, not missing data to be filled by inference.

## Full inherited qualification

Exact head `e1bacf31afa3fc76107d394da2aa95c41fee7d53` passed full CI run `33803524089` across:

- source tests on Python 3.12 and 3.13;
- exact canonical differential/golden tests;
- G10 observatory regressions on both Python versions;
- G11 counterbalanced frozen-reference comparisons on both Python versions;
- RC0 wheel and normalized-sdist clean-install verification on both Python versions;
- installed aggregate/qualification checks;
- cross-Python release reproducibility.

## Engineering decision

G12 selects the **one-pass growing-buffer homogeneous plain-int tuple specialization** as the closure candidate.

G12 rejects:

- treating proxy ratios as nested attribution;
- timings contaminated by `tracemalloc`;
- the parts-join candidate as the balanced production choice because of its allocation cost;
- any C/Rust/SIMD/GPU/FPGA/ASIC/QPU implementation at this stage.

The residual serializer remains substantial for the declared workload, but the next action must again be evidence-selected. A remaining timing share by itself is not sufficient to justify hardware.

## Claim boundary

G12 is a byte-identical software specialization plus environment-specific measurement evidence. Public maturity remains:

- semantic: `TESTED`;
- evidence: `SUPPORTED`;
- formal: `NONE`;
- hardware: `NONE`;
- deployment: `LOCAL`.

T4 Physical and T5 Evolutionary remain `NOT_ENABLED`. G12 adds no federation, physical-control readiness, formal proof, production-security certification, accelerator readiness, hardware qualification, or semantic/scientific truth certification.
