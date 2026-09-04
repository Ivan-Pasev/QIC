# QIC G13 — Canonical Workload Generalization Atlas

Status: **ACTIVE / characterization evidence acquired / production code unchanged**

Issue: #37  
Draft PR: #38  
Frozen baseline: G12 state-sealed `main` at `b966b9e3e5d2271612343276b32833d721a99128`

## Mission

Determine whether the G10–G12 canonicalization findings generalize beyond the homogeneous plain-int tuple workload before admitting another specialization, native-extension hypothesis, or accelerator discussion.

The governing laws remain:

- `NoAcceleratorWithoutMeasuredBottleneck`;
- `MeasuredBottleneck != AutomaticSiliconCandidate`;
- `AlgorithmicImprovementBeforeHardwareAcceleration`;
- exact `QIC-CANONICAL/1.0` byte identity is release-blocking.

## Campaign

G13 workload-atlas run: `33860326769` on head `4ed7641b96d2825fd678bf2aa34c648f9902b372`.

Artifacts:

- Python 3.12: `9931846180`, `sha256:d3e77bd8dcf5c67a1ac5da9e54d4b9fd80c2625b460750d4c1a5b93bb6ba7f68`;
- Python 3.13: `9931850907`, `sha256:6a545e96c66de91f0777eec4234596a3bac568cf8f636db7a12e0ea11cdd2637`.

The matrix contains 10 deterministic payload families × 3 sizes = 30 records per environment. Timing uses `perf_counter_ns` with `tracemalloc` disabled. Allocation is measured independently with `tracemalloc`. Production bytes are compared directly with the frozen G1 `_canonical_bytes_reference` for every payload. All declared records preserved exact byte identity.

## Size-1000 results

| family | Py3.12 canonical median | Py3.13 canonical median | traced peak bytes | encoded bytes |
|---|---:|---:|---:|---:|
| plain-int tuple | 266,512 ns | 241,218 ns | 60,544 B | 29,960 |
| plain-int list | 515,748 ns | 378,902 ns | 180,820 B | 29,959 |
| int frozenset | 471,666 ns | 433,203 ns | 180,675 B | 29,964 |
| mixed scalar tuple | 687,521 ns | 616,195 ns | 168,196 B | 31,320 |
| nested structure | 640,546 ns | 632,219 ns | 63,019 B | 20,995 |
| string tuple | 1,491,532 ns | 1,370,285 ns | 198,602 B | 38,760 |
| string set | 1,636,672 ns | 1,470,043 ns | 196,889 B | 38,068 |
| string-key mapping | 1,640,255 ns | 1,583,371 ns | 200,612 B | 39,962 |
| enum tuple | 3,605,760 ns | 3,595,398 ns | 311,222 B | 95,070 |
| dataclass tuple | **8,887,552 ns** | **8,434,895 ns** | **483,782 B** | 181,350 |

Digest end-path medians are of the same order for these payloads. Because serializer and digest timings are independently sampled, their differences are not treated as exact nested attribution.

## Bounded findings

### G13-F1 — the G12 specialization is narrow by design and no longer the leading generalization problem

The homogeneous plain-int tuple is the fastest size-1000 family in both environments and has the lowest measured traced peak allocation among the declared large families. This is consistent with G12 having removed a material software cost for its intended payload class.

This does **not** imply the int-tuple path is globally optimal, nor does it justify additional micro-polishing from this campaign.

### G13-F2 — generic-path cost is strongly payload-family dependent

String-heavy tuples, string sets, mappings, enum tuples, and especially dataclass tuples are materially slower than the optimized int-tuple control. The spread is too large for the prior single-family benchmark to be treated as representative of canonicalization generally.

A simple derived median-nanoseconds / encoded-byte ratio also places the dataclass family at the high end (~49 ns/encoded-byte on Python 3.12 and ~47 ns/encoded-byte on Python 3.13), but this ratio is only a descriptive normalization. It is **not** a causal stage attribution or portable throughput claim.

### G13-F3 — dataclass-heavy canonicalization is the strongest next software investigation target

The size-1000 dataclass family is roughly 8.4–8.9 ms with ~484 KB traced peak allocation. The current direct emitter repeatedly resolves dataclass field metadata/type identity and emits field-name JSON for each object. Those implementation facts plus the measured family-level cost support a next characterization hypothesis around dataclass metadata and field emission.

This is a **SUPPORTED INVESTIGATION HYPOTHESIS**, not yet evidence that caching, specialization, native code, or hardware will improve the production path.

### G13-F4 — no native/hardware accelerator case is established

The campaign broadens the software evidence base but does not measure transfer cost, native-call boundary cost, SIMD suitability, parallel scaling, or Amdahl benefit for a candidate accelerator. Therefore G13 explicitly selects **no C/Rust/SIMD/GPU/FPGA/ASIC/QPU implementation**.

## Engineering decision

G13 should close as a characterization-only slice. It should not alter the production canonicalizer.

The next admissible software question is narrower:

> For dataclass-heavy canonicalization, what share of the family-level cost is associated with repeated metadata/type-name/field-name work versus recursive value emission, and can a byte-identical Python-level metadata reuse candidate improve latency and allocation without harming other canonical families?

That question belongs in a subsequent measured slice (provisionally G14), not as an unmeasured production change inside G13.

## Claim boundary

G13 is environment- and payload-family-specific software characterization only. It adds no new runtime semantics or maturity. It does not certify semantic truth, formal correctness, production security, physical safety, federation, distributed consensus, hardware suitability, accelerator readiness, deployment readiness, or universal performance. T4 Physical and T5 Evolutionary remain `NOT_ENABLED`.
