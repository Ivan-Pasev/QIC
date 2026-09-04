# QIC State

Last updated: 2026-09-04

## Canonical status

**Current state:** `QIC-G13 — MERGED / post-merge state seal`

**G13 issue:** #37 — CLOSED / COMPLETED  
**G13 implementation PR:** #38 — MERGED  
**G13 merge commit:** `a826d51848a66825131406538429ed929a112ce5`  
**G13 state-seal issue:** #39 — OPEN  
**State-seal branch:** `qic-g13/state-seal`

**Public repository:** `Ivan-Pasev/QIC`  
**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`  
**Release candidate baseline:** `1.0.0rc0`

## Frozen completed baseline

- G0–G8: merged constitutional implementation/qualification stack.
- RC0: integrated release convergence merged/qualified; publication remains separately pending until directly verified.
- G9: local reference durable journal/recovery merged and sealed.
- G10: performance observatory merged and sealed.
- G11: direct canonical byte emitter merged and sealed.
- G12: residual canonicalization characterization + byte-identical homogeneous plain-int tuple specialization merged and sealed.
- G13: canonical workload generalization characterization merged as a measurement-only slice; production canonicalizer semantics unchanged.
- T4 Physical and T5 Evolutionary remain `NOT_ENABLED`.

Public maturity remains unchanged:

- semantic: `TESTED`
- evidence: `SUPPORTED`
- formal: `NONE`
- hardware: `NONE`
- deployment: `LOCAL`

## G13 closure evidence

Final qualified PR head: `9c7370a6ceacf77c846df5fc74c88a358297e107`.

- dedicated G13 workload-atlas run `33860813207` — PASS on Python 3.12/3.13;
- inherited full CI run `33860813177` — PASS, including source suites, G10 observatory, G11 frozen-reference comparisons, RC0 wheel/sdist clean-install verification, and cross-Python reproducibility;
- implementation merge `a826d51848a66825131406538429ed929a112ce5`.

Final exact-head G13 artifacts:

- Python 3.12: `9932031167`, `sha256:95cc24cc9d0b6ae20bbad8a3e5e08e729f28b28c1245069ebe475240e41ef5a4`;
- Python 3.13: `9932032188`, `sha256:a752263cc163d2eced72a535a1e880a02e8bf313de7f1ee05ea1fe6b991ceb7f`.

The declared matrix covers 10 deterministic payload families × sizes 10/100/1000 with timing and allocation in separate channels. Every declared payload preserved exact frozen-G1 `QIC-CANONICAL/1.0` bytes.

Reference characterization at size 1000 measured the optimized plain-int tuple at `266,512 ns` / `241,218 ns` and the dataclass tuple at `8,887,552 ns` / `8,434,895 ns` on Python 3.12 / 3.13, with dataclass traced peak allocation `483,782 B`. These are environment- and payload-family-specific observations, not portable throughput guarantees.

## Engineering decision

G13 closes with **no production canonicalizer change**.

It establishes that the prior integer-tuple benchmark is not representative of canonicalization generally and that the strongest next measured Python-level investigation target is dataclass-heavy canonicalization, especially repeated metadata/type-name/field-name work versus recursive value emission.

G13 selects no C/Rust/native extension, SIMD, GPU, FPGA, ASIC, QPU, or hardware accelerator.

## Claim boundary

G13 adds payload-family-specific software characterization only. It does not add runtime semantics, formal proof, security certification, physical-control readiness, federation, distributed consensus, T4/T5 enablement, hardware qualification, accelerator readiness, deployment promotion, maturity promotion, or semantic/scientific truth certification.

## Next admissible action

Complete post-merge state-seal PR for G13 and require exact-head inherited CI. If green, merge the seal and select G14 from sealed G13 main. The admissible G14 candidate is dataclass-path decomposition and byte-identical Python-level metadata reuse **only after measured decomposition evidence**; do not jump to native code or hardware.
