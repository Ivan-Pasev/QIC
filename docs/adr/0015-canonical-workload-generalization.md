# ADR-0015 — Characterize Canonical Workload Families Before Further Optimization

- **Status:** Accepted for G13 characterization
- **Date:** 2026-09-04

## Context

G10 identified a serialization-dominant `canonical.digest` path using a homogeneous integer tuple. G11 replaced the normalized-object tree with direct byte emission. G12 then specialized homogeneous plain-integer tuples and materially improved that same workload while preserving exact `QIC-CANONICAL/1.0` bytes.

The declared canonical surface is broader than that benchmark: lists, mappings, sets/frozensets, strings/bytes, dataclasses, enums, booleans, tuples and nested combinations are supported. Continuing to optimize the same integer-tuple workload would risk benchmark overfitting and would not establish a general accelerator case.

## Decision

G13 is a **characterization-only** slice.

It introduces a deterministic payload-family matrix across Python 3.12/3.13 and measures production `canonical_bytes`/`digest_hex` with:

- timing and allocation in separate channels;
- frozen-G1 exact-byte differential checks for every payload;
- bounded deterministic sizes;
- raw artifact preservation;
- no production canonicalizer modification.

The first matrix shows that the G12 integer-tuple path is now the fastest/lowest-allocation large family in the declared G13 set, while dataclass-heavy canonicalization is the dominant measured family cost. G13 therefore does not add another fast path. It nominates dataclass metadata/type-name/field-name work for a subsequent measured Python-level investigation.

## Consequences

Positive:

- avoids treating one optimized benchmark as representative of canonicalization generally;
- supplies family-specific evidence before another software specialization;
- keeps native/hardware acceleration behind an evidence gate;
- preserves canonical byte identity and existing maturity boundaries.

Costs:

- G13 deliberately produces no runtime speedup;
- timings remain environment-specific;
- payload families are representative test constructions, not a workload-frequency distribution for real deployments.

## Rejected alternatives

### Continue integer-tuple micro-optimization
Rejected because G13 shows that family is no longer the largest generalization cost in the declared matrix.

### Move directly to C/Rust/SIMD/GPU/FPGA/ASIC/QPU
Rejected because G13 does not measure transfer/call-boundary cost, parallel scaling, Amdahl benefit, hardware suitability or real workload prevalence.

### Treat median nanoseconds / encoded byte as causal attribution
Rejected. It is at most a descriptive normalization and does not identify where time is spent inside the serializer.

## Claim boundary

This ADR authorizes measurement and characterization only. It does not authorize a new production fast path, native implementation, accelerator/hardware work, T4/T5 enablement, federation, security certification, formal proof, deployment promotion, or semantic/scientific truth claim.
