# QIC State

Last updated: 2026-09-04

## Canonical status

**Current state:** `QIC-G13 — CANONICAL WORKLOAD GENERALIZATION / ACTIVE CHARACTERIZATION`

**G13 issue:** #37 — OPEN  
**G13 draft PR:** #38  
**Branch:** `qic-g13/canonical-workload-atlas`  
**Frozen baseline:** G12 state-sealed `main` at `b966b9e3e5d2271612343276b32833d721a99128`  
**Initial G13 evidence head:** `4ed7641b96d2825fd678bf2aa34c648f9902b372`  
**G13 workload-atlas run:** `33860326769` — PASS on Python 3.12 and 3.13

**Public repository:** `Ivan-Pasev/QIC`  
**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`  
**Release candidate baseline:** `1.0.0rc0`

## Frozen completed baseline

- G0–G8: merged constitutional implementation/qualification stack.
- RC0: integrated release convergence merged/qualified; publication remains separately pending until directly verified.
- G9: local reference durable journal/recovery merged and sealed.
- G10: performance observatory merged and sealed.
- G11: direct canonical byte emitter merged and sealed.
- G12: residual canonicalization characterization + byte-identical homogeneous plain-int tuple specialization merged and post-merge sealed.
- G12 implementation merge: `2c558c0550c1f8d7db7591ad7b3fe523795bd2dc`.
- G12 state-seal merge: `b966b9e3e5d2271612343276b32833d721a99128`.
- G12 state-seal CI: `33859982342` — PASS.
- T4 Physical and T5 Evolutionary remain `NOT_ENABLED`.

Public maturity remains unchanged:

- semantic: `TESTED`
- evidence: `SUPPORTED`
- formal: `NONE`
- hardware: `NONE`
- deployment: `LOCAL`

## G13 reason

The G10 canonical benchmark used `tuple(range(size))` for canonical bytes/digest. G12 then optimized exactly that homogeneous plain-int tuple family. G13 tests whether conclusions from that benchmark generalize across the declared canonical type surface before any further specialization, native-extension hypothesis, or accelerator discussion.

Governing laws remain:

- `NoAcceleratorWithoutMeasuredBottleneck`;
- `MeasuredBottleneck != AutomaticSiliconCandidate`;
- `AlgorithmicImprovementBeforeHardwareAcceleration`;
- exact `QIC-CANONICAL/1.0` byte identity is release-blocking.

## G13 evidence

Run `33860326769` measured 10 deterministic payload families × sizes 10/100/1000 on Python 3.12 and 3.13. Timing excludes `tracemalloc`; allocation is measured in a separate traced channel. Every payload was compared against the frozen G1 byte oracle and preserved exact canonical bytes.

Artifacts:

- Python 3.12: `9931846180`, digest `sha256:d3e77bd8dcf5c67a1ac5da9e54d4b9fd80c2625b460750d4c1a5b93bb6ba7f68`;
- Python 3.13: `9931850907`, digest `sha256:6a545e96c66de91f0777eec4234596a3bac568cf8f636db7a12e0ea11cdd2637`.

At size 1000, canonical medians ranged from `266,512 ns` / `241,218 ns` for the optimized plain-int tuple to `8,887,552 ns` / `8,434,895 ns` for the dataclass tuple (Python 3.12 / 3.13). Dataclass traced peak allocation was `483,782 B`; optimized plain-int tuple peak was `60,544 B` in this G13 run.

The broad ordering also placed enum tuples (~3.6 ms), string-key mappings/string sets/string tuples (~1.37–1.64 ms), and mixed/nested generic structures above the optimized int-tuple control. These are environment- and payload-family-specific observations, not portable throughput guarantees.

See `PERFORMANCE_CHARACTERIZATION_G13.md` for the full bounded interpretation.

## Engineering decision so far

G13 makes **no production canonicalizer change**.

Evidence indicates:

1. further plain-int tuple micro-polishing is not the leading generalization problem;
2. canonicalization cost is strongly payload-family dependent;
3. dataclass-heavy canonicalization is the strongest next Python-level investigation target;
4. no native extension or hardware accelerator case is established.

The provisional next hypothesis is to characterize repeated dataclass metadata/type-name/field-name work versus recursive value emission, then test a byte-identical Python-level metadata-reuse candidate only if the decomposition supports it. That work should be a subsequent measured slice rather than an unmeasured G13 production change.

## Claim boundary

G13 adds environment- and payload-family-specific characterization only. It adds no new runtime semantics, maturity, formal proof, security certification, federation, distributed consensus, physical control, T4/T5 enablement, hardware qualification, accelerator readiness, broad deployment readiness, or semantic/scientific truth certification.

## Next admissible action

Complete G13 documentation/traceability and exact-head inherited CI. Close G13 as characterization-only if those gates pass. Then open the next software investigation around the measured dataclass-heavy path; do not jump to native code or hardware from family-level timing alone.
