# QIC G12 — Residual Canonicalization Cost Characterization

Status: **ACTIVE / first characterization campaign qualified; optimization decision not yet closed**

Issue: #33  
Draft PR: #34  
Frozen baseline: G11 state-sealed `main` at `36ce69368ad4282c1d546211ade5cc4c8c3ca828`

## Question

After G11 removed the intermediate normalized object tree and improved the declared size-1000 canonicalization hot path by about 44%, what operation families plausibly dominate the remaining optimized cost?

G12 does not infer a hardware target from timing share. It first characterizes the current software path.

## Measurement correction discovered during G12

The first G12 campaign revision enabled `tracemalloc` during timing. That changed the observed size-1000 `canonical_bytes` median into the multi-microsecond range and therefore made those timings unsuitable for comparison with G11.

The campaign was corrected before any bottleneck finding was admitted:

- timing channel: `trace_memory=False`;
- allocation channel: separate run with `trace_memory=True`;
- result identity must match across timing and allocation channels;
- proxy measurements remain explicitly non-attributive.

The contaminated timing run is retained as a methodological negative result, not as performance evidence.

## Qualified campaign

Workflow run: `33802554652`  
Measured head: `7b9ef7b49421e448f3cd7b2cfafbcc951c16e933`

Artifacts:

- CPython 3.12 artifact `9911616821`, artifact digest `sha256:9d8f787450dc77e31bf6afd45e182ec6aae3c9a68487ff7d36df543bed7fb731`
- CPython 3.13 artifact `9911621528`, artifact digest `sha256:195741564378485b2726b1f8375eec57b05ed0994ba2f7ca7b732c9c110c5870`

Inherited full CI on the same head: run `33802554500` — PASS across Python 3.12/3.13 source tests, G10 observatory regressions, G11 comparison regressions, RC0 wheel/sdist clean-install verification, installed qualification, and cross-Python reproducibility.

## Exact production-path observations

Median wall time, nanoseconds:

| size | CPython 3.12 `canonical_bytes` | CPython 3.12 `digest_hex` | CPython 3.13 `canonical_bytes` | CPython 3.13 `digest_hex` |
|---:|---:|---:|---:|---:|
| 10 | 17,823 | 9,487 | 7,531 | 9,164 |
| 100 | 56,615 | 60,583 | 61,321 | 62,863 |
| 1000 | 554,250 | 574,107 | 560,508 | 583,800 |

The size-10 point is overhead-sensitive and is not used for bottleneck attribution. At sizes 100 and 1000, the production path scales approximately with item count for this integer-tuple family.

## Separate allocation channel

Median traced peak bytes for `canonical_bytes`:

| size | traced peak bytes |
|---:|---:|
| 10 | 1,312 |
| 100 | 18,148 |
| 1000 | 180,884 |

The traced allocation result is identical in the two measured Python environments for these payloads. This is a `tracemalloc` observation for the declared run, not a complete allocator/RSS model.

## Proxy signals — not nested time shares

For the size-1000 integer tuple:

| operation proxy | CPython 3.12 median | CPython 3.13 median | interpretation |
|---|---:|---:|---|
| independent integer-leaf `_encode_value` batch | 536,061 ns | 481,356 ns | strong per-element emission/dispatch signal |
| decimal `str(int).encode('ascii')` batch | 133,895 ns | 135,300 ns | integer text conversion is material but not the whole leaf path |
| comma join of pre-encoded leaves | 11,881 ns | 12,768 ns | join itself is small relative to the full tuple path in this proxy |
| JSON-string batch over decimal text | 1,196,412 ns | 1,246,671 ns | not representative of plain-int fast path; retained as another payload operation family |
| mapping encode, reversed input order | 2,030,060 ns | 2,053,704 ns | mapping sorting/key emission is a distinct, more expensive family |
| set encode/order | 580,154 ns | 527,030 ns | set ordering adds a separate family cost; not the tuple bottleneck |

The integer-leaf proxy is numerically close to full tuple canonicalization at size 1000, but **this ratio is not interpreted as an exact percentage time share**. The proxy creates a tuple of independently encoded leaf byte strings and therefore has a different allocation/composition pattern from recursive tuple emission.

## G12-F1 — first bounded finding

**Finding:** for the declared tuple-of-integers workload, the remaining cost is much more consistent with repeated per-element integer encoding / recursive dispatch / emitted-byte allocation than with the final comma-join operation alone.

Evidence strength: **SUPPORTED HYPOTHESIS**, not causal closure.

Why this is admissible:

1. the production path and integer-leaf proxy scale together at sizes 100 and 1000;
2. pre-encoded joining remains only about 12 microseconds at size 1000 in both environments;
3. integer decimal text conversion is itself about 134–135 microseconds at size 1000;
4. traced peak allocation grows from 18,148 bytes at size 100 to 180,884 bytes at size 1000;
5. the direction appears in both Python environments.

Why it is not yet causal closure:

- independent proxy workloads are not nested instrumentation;
- ratios between proxy and production timings cannot be treated as exact stage shares;
- `tracemalloc` peak bytes are not allocation-count or lifetime attribution;
- no allocator/native profiler evidence has yet identified exact call-site contribution.

## Next admissible experiment

Before changing production code, G12 should test a **buffer-oriented integer-tuple reference candidate** against the current G11 production path under exact byte identity.

The candidate should target the measured hypothesis directly:

- reduce per-leaf temporary byte-object construction and recursive dispatch for the homogeneous plain-int tuple case;
- preserve the generic G11 path for all other declared canonical types;
- remain a software algorithmic candidate only;
- be rejected on any canonical-byte divergence;
- be admitted only on same-environment measured evidence.

This is not permission for a C extension, Rust, SIMD, GPU, FPGA, ASIC, or QPU implementation. Those remain unselected.

## Claim boundary

G12 currently adds characterization evidence only. Public maturity remains semantic `TESTED`, evidence `SUPPORTED`, formal `NONE`, hardware `NONE`, deployment `LOCAL`. T4 and T5 remain `NOT_ENABLED`.
