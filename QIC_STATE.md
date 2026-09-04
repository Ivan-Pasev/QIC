# QIC State

Last updated: 2026-09-04

## Canonical status

**Current state:** `QIC-G12 — MERGED / post-merge state seal`

**G12 issue:** #33 — CLOSED / COMPLETED  
**G12 implementation PR:** #34 — MERGED  
**G12 merge commit:** `2c558c0550c1f8d7db7591ad7b3fe523795bd2dc`  
**G12 state-seal issue:** #35  
**State-seal branch:** `qic-g12/state-seal`

**Public repository:** `Ivan-Pasev/QIC`  
**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`  
**Release candidate baseline:** `1.0.0rc0`

## Frozen completed baseline

- G0–G8: merged constitutional implementation/qualification stack.
- RC0: integrated release convergence merged and qualified; GitHub tag/release publication remains separately publication-pending until directly verified.
- G9: local reference durable journal/recovery merged and post-merge sealed.
- G10: performance observatory merged and post-merge sealed.
- G11: direct canonical byte emitter merged and post-merge sealed.
- G12: residual canonicalization characterization plus byte-identical homogeneous plain-int tuple specialization merged by PR #34.
- T4 Physical and T5 Evolutionary remain `NOT_ENABLED`.

Public maturity remains unchanged:

- semantic: `TESTED`
- evidence: `SUPPORTED`
- formal: `NONE`
- hardware: `NONE`
- deployment: `LOCAL`

## G12 evidence chain

G12 began from sealed G11 main `36ce69368ad4282c1d546211ade5cc4c8c3ca828` under the engineering laws:

- `NoAcceleratorWithoutMeasuredBottleneck`;
- `MeasuredBottleneck != AutomaticSiliconCandidate`;
- `AlgorithmicImprovementBeforeHardwareAcceleration`.

The first G12 timing revision used `tracemalloc` during timing and materially perturbed the serializer. Those timings were rejected before admitting a finding. The accepted campaign separates untraced timing from separately traced allocation measurement and treats proxy microkernels as non-attributive.

Corrected residual characterization run `33802554652` showed, for the declared homogeneous integer-tuple workload, that repeated integer emission/dispatch and temporary-byte allocation were stronger software targets than final joining alone. This remained a supported hypothesis rather than exact nested attribution.

Reference-candidate run `33802909806` compared two byte-identical software designs. The flattened-parts candidate was slightly faster but had substantially higher traced peak allocation; the one-pass growing `bytearray` design was selected as the balanced production candidate. No native extension or hardware accelerator was selected.

The production specialization applies only to homogeneous tuples satisfying `type(item) is int`. It validates and emits into one growing buffer, falls back to the G11 generic path at the first non-plain-int element, and therefore excludes `bool`, `IntEnum`, mixed tuples, and other subtype cases from the fast path. The frozen G1 implementation remains the exact differential oracle. `QIC-CANONICAL/1.0` bytes did not change.

## Exact-head qualification before merge

Final PR head: `e44a2ac56b4ca53b6babe5d05e532a1743f66520`.

- inherited full CI run `33804645433` — PASS;
- dedicated G12 residual-profile run `33804645371` — PASS.

The inherited suite includes Python 3.12/3.13 source tests, canonical differential/golden tests, observatory regressions, frozen-reference comparisons, RC0 wheel/sdist clean-install verification, installed qualification surfaces, and cross-Python release reproducibility.

PR #34 was merged only after both exact-head workflows were green.

## Measured bounded result

For the declared size-1000 workload, the earlier closure-candidate campaign measured production around `319,507 ns` on Python 3.12 and `268,463 ns` on Python 3.13 with traced peak allocation `60,608 B`. Same-job frozen-G1 comparison measured about `66.09%` improvement on Python 3.12 and `63.23%` on Python 3.13, with exact byte identity preserved in every measured pair.

These are environment- and workload-specific software measurements. They do not establish a general QIC speedup, native-extension need, accelerator suitability, or hardware advantage.

## Engineering decision

G12 admits the one-pass growing-buffer homogeneous plain-int tuple specialization as a tested local software optimization and rejects:

- proxy ratios as exact nested attribution;
- timing contaminated by `tracemalloc`;
- the high-allocation flattened-parts design as the balanced production choice;
- C/Rust/SIMD/GPU/FPGA/ASIC/QPU work without a new evidence-selected hypothesis.

## Claim boundary

G12 adds byte-identical software specialization plus environment-specific timing/allocation evidence only. It does **not** add federation, distributed consensus, physical-control readiness, T4/T5 enablement, formal proof, production-security certification, hardware qualification, accelerator readiness, broad deployment readiness, or semantic/scientific truth certification.

## Next admissible action

Complete post-merge state-seal PR from `qic-g12/state-seal`, require exact-head inherited CI, merge only if green, then select G13 from the sealed G12 baseline. G13 must be evidence-driven; residual timing share alone is insufficient to justify native code or hardware acceleration.
