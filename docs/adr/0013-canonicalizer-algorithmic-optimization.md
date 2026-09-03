# ADR-0013 — Canonicalizer Algorithmic Optimization

## Status

Accepted and merged in G11 via PR #31 (`554e8f0ea6c2a5a187a5cb675a9d25e8fd8da70b`) after exact-head CI run `33799603266` passed.

## Context

G10 measured `G10-BF-001`, a narrowly scoped serialization-dominant `canonical.digest` path for a tuple of 1000 integers under two GitHub-hosted CPython environments. G10 explicitly required algorithmic improvement before any hardware acceleration hypothesis.

The G1 canonicalizer first constructed a fully normalized Python object tree and then serialized that tree with `json.dumps`. The measured hot path therefore incurred both normalization-object allocation and JSON serialization work.

## Decision

The production G11 canonicalizer emits the already-declared `QIC-CANONICAL/1.0` typed JSON bytes directly.

The frozen G1 object-tree implementation remains available as `_canonical_bytes_reference` solely for differential testing and measurement. It is not the production path.

## Compatibility requirements

The optimization is admissible only if:

1. `canonical_bytes(value) == _canonical_bytes_reference(value)` across the declared compatibility corpus;
2. existing G1 golden vectors remain unchanged;
3. fail-closed behavior for floats, unsupported values, and invalid mapping keys remains equivalent;
4. enum/dataclass/container/set/mapping ordering semantics remain identical;
5. G8 qualification, G9 recovery, G10 observability, RC0 packaging, installed verification, and T4/T5 disablement remain green;
6. measured performance shows non-regression or improvement under equal semantic work.

Any canonical-byte divergence rejects the candidate regardless of performance.

## Measurement decision

Counterbalanced same-environment measurements on Python 3.12 and 3.13 show approximately 44% median improvement at the size-1000 tuple hot path after reversing reference/candidate measurement order. The optimized serializer still represents about 95% of the independently timed same-job digest-path median at that scale.

These measurements are environment-specific evidence, not portable benchmark guarantees or algorithmic complexity proofs.

## Consequences

Positive:

- removes an intermediate normalized object tree from the measured production path;
- materially reduces measured serialization latency on the declared workload;
- preserves canonical byte identity;
- follows the G10 decision to optimize software before considering hardware.

Costs/risks:

- direct byte emission is more implementation-sensitive than delegating final structure serialization to one `json.dumps` call;
- future canonical-format changes must update both direct-emission logic and the frozen-reference qualification strategy deliberately;
- the residual serialization bottleneck remains material for the measured workload.

## Non-decisions

This ADR does not select SIMD, multicore, GPU, FPGA, ASIC, QPU, C-extension, Rust, or other acceleration. It does not change QIC maturity, enable T4/T5, add federation, or establish a QIC-wide performance bottleneck.
