# ADR-0014 — Residual Canonicalization Characterization and Plain-Integer Tuple Specialization

## Status

Proposed for G12 closure; implementation is subject to documentation-sealed exact-head CI and merge.

## Context

G11 removed the intermediate normalized Python object tree while preserving exact `QIC-CANONICAL/1.0` bytes. Its measured size-1000 integer-tuple path improved materially, but serialization remained a dominant portion of the independently timed digest path in the declared environments.

G12 was opened to characterize that residual cost before considering any accelerator or native implementation.

## Measurement discipline

The first G12 profiling revision enabled `tracemalloc` during timing and materially perturbed the serializer. Those timing results were rejected before any performance finding was admitted.

The accepted measurement design separates:

- an untraced timing channel;
- a separately traced allocation channel;
- exact production-path measurements;
- non-attributive proxy microkernels;
- byte-identical software reference candidates.

Independent proxy timings are not treated as nested stage shares.

## Finding

For the declared homogeneous integer-tuple workload, the evidence supports repeated per-element integer emission/dispatch and temporary-byte allocation as a stronger optimization target than the final comma-join operation alone.

This is a bounded workload finding, not a QIC-wide bottleneck theorem.

## Candidate decision

Two byte-identical software reference candidates were measured:

1. a growing `bytearray` emitter;
2. a flattened parts list followed by a final join.

The parts-join candidate was slightly faster in the reference campaign but used approximately 418,707 bytes of traced peak allocation at size 1000. The growing-buffer candidate used approximately 60,636 bytes and still delivered a large measured latency improvement.

G12 therefore selects the growing-buffer design as the balanced production specialization.

## Production design

The production fast path is deliberately narrow:

- it applies only to tuples whose elements satisfy `type(item) is int`;
- membership validation and emission occur in one pass;
- on the first non-plain-int element the attempted buffer is rolled back and the generic G11 emitter is used;
- `bool`, `IntEnum`, mixed tuples and other subtype cases therefore do not silently enter the specialization;
- nested/generic canonical semantics remain governed by the existing G11 implementation;
- the frozen G1 implementation remains the byte-for-byte differential qualification oracle.

No canonical wire/byte format changes.

## Evidence

Closure-candidate production head: `e1bacf31afa3fc76107d394da2aa95c41fee7d53`.

G12 characterization run `33803524078` passed on Python 3.12 and 3.13. At size 1000 the production median was approximately 319,507 ns / 268,463 ns with traced peak allocation of 60,608 bytes in both environments.

Inherited full CI `33803524089` passed. Its same-job counterbalanced frozen-G1 comparison measured size-1000 improvement of approximately 66.09% on Python 3.12 and 63.23% on Python 3.13 with exact byte identity.

The Python 3.13 independent digest measurement was slightly below the independent serialization median, so no serialization-share estimate was admitted for that environment.

## Consequences

Positive:

- removes most per-leaf temporary byte-object construction for the declared hot path;
- reduces traced peak allocation from approximately 180,884 bytes to approximately 60,608 bytes at size 1000;
- materially improves the declared measured path while preserving exact canonical bytes;
- retains the generic path for all nonmatching canonical values;
- follows the software-first performance law.

Costs and limitations:

- the canonicalizer now contains a workload-specific specialization that must remain covered by differential tests;
- performance evidence is environment-bound and does not imply a portable speed guarantee;
- the specialization does not establish algorithmic complexity optimality;
- remaining serialization cost does not by itself establish an accelerator target.

## Non-decisions

ADR-0014 does not select or authorize C, Rust, SIMD, multicore, GPU, FPGA, ASIC, photonic, or QPU acceleration. It does not enable T4/T5, add federation, change authority, or increase formal, hardware, or deployment maturity.
