# ADR-0009 — Adversarial Constitutional Qualification

- **Status:** Accepted for G8 implementation
- **Date:** 2026-09-02

## Context

G0–G7 now provide an installable local constitutional kernel with canonicalization/digests, independent maturity dimensions, scoped authority, deterministic transitions, Chrono/witness, Minimal KBI, and a public verification CLI. Before any RC0 release claim, QIC needs a negative qualification campaign that asks not only whether expected paths work, but whether declared constitutional boundaries fail closed under adversarial inputs and modeled gate-removal defects.

## Decision

G8 adds no new authority or runtime capability. It adds a qualification layer composed of:

1. centralized adversarial checks over G1–G7;
2. a failure atlas with expected containment behavior;
3. five deterministic modeled constitutional mutants;
4. a release-blocking aggregate qualification result;
5. `qic verify qualification` plus inclusion in aggregate `qic verify`;
6. a qualification report and claim-surface audit.

The modeled mutants represent plausible constitutional defects rather than source-code mutation tooling. Each mutant is designed so the production runtime must distinguish itself from the permissive defect:

- `scalar_maturity_collapse` — collapses independent maturity dimensions to a scalar score;
- `authority_any_of` — treats partial authority overlap as authorization;
- `enable_t4` — treats matching physical authority as sufficient despite T4 being disabled;
- `ignore_chrono_anchor` — treats an internally valid historical prefix as current despite a supplied external head/length anchor;
- `count_echo_bindings` — counts repeated bindings/evidence records from one source as independent corroboration.

A mutant is considered killed only when the real runtime rejects/contains the adversarial case while the modeled permissive mutant would accept it.

## Release rule

G8 is fail closed:

`failed qualification check OR surviving declared critical mutant => G8 not qualified`

Expected rejection is a successful qualification result when rejection is the constitutional requirement.

## Qualification scope

The G8 campaign checks:

- unsupported/ambiguous canonical forms and digest domain separation;
- maturity-vector partial-order semantics;
- authority non-amplification and revocation;
- stale/unauthorized transition atomicity;
- global T4/T5 non-executability;
- Chrono tamper detection and the externally anchored suffix-truncation boundary;
- KBI evidence-echo resistance and contradiction preservation;
- registry/runtime parity;
- public claim/maturity surfaces;
- modeled mutant detection.

## Claim boundary

A G8 PASS is evidence only for the declared local structural cases exercised by the qualification suite on the tested source/environment. It is not:

- a formal proof of runtime correctness;
- a security certification or penetration test;
- a physical safety case;
- hardware qualification;
- federation or distributed-consensus evidence;
- a durable crash-recovery guarantee;
- legal/compliance certification;
- semantic or scientific truth certification.

The Chrono boundary remains explicit: an internally valid prefix cannot prove its own completeness or recency. Suffix truncation is detectable only against an independently retained expected length/head anchor.

## Consequences

Positive:

- release qualification becomes explicitly adversarial and fail closed;
- earlier constitutional boundaries are tested together rather than only slice-by-slice;
- modeled gate-removal failures become executable release blockers;
- public maturity/claim language is part of qualification, not merely documentation review;
- RC0 has a concrete precondition rather than being a version-label decision.

Limitations:

- modeled mutants are deterministic defect models, not full source mutation coverage;
- no fuzz engine, coverage-guided mutation framework, cryptographic identity, durable journal, federation, hardware, or physical I/O is introduced;
- passing local tests does not establish behavior under unmodeled production failures.

## Next

After G8 closes on a reviewed green head, the next step is `QIC-v1 RC0 — integrated genesis release convergence`, not feature expansion.
