# QIC G14 — Dataclass Canonicalization Decomposition

Status: **ACTIVE / Phase A acquired / Phase B non-production candidate admitted**

Issue: #41  
Draft PR: #42  
Frozen baseline: sealed G13 `main` at `d380976ea327f95ae8e0ad333ffb6c0e1bd96d18`

## Mission

Characterize the G13-measured dataclass-heavy canonicalization path before any production change, then test a byte-identical Python-level metadata-reuse candidate only if the decomposition evidence supports it.

## Phase A campaign

Initial Phase-A head: `f4e0ff1fa453226abf5e95601a54141aab8c4f17`.

G14 decomposition run: `33861660809` — PASS on Python 3.12 and 3.13.

Artifacts:

- Python 3.12: `9932351980`, `sha256:77dbfe4f91c777e5b28e3d1107a554ce0b395bc9d9091ed5a0074c83e77e35dc`;
- Python 3.13: `9932350599`, `sha256:47ab7b279b283481ec0837361c5b1c4e50a38572dea8cb29637b18d418d188f4`.

The campaign uses four representative dataclass shapes (small frozen 3-field, wide frozen 8-field, slotted frozen 4-field, mixed frozen 5-field) across sizes 10/100/1000. Timing and traced allocation are separate channels. Every full payload is compared with the frozen G1 byte oracle.

Independent proxy microkernels are **non-additive and non-attributive**. Their timings are not summed or subtracted to claim exact internal stage shares.

## Size-1000 Phase-A reference medians

| shape | full tuple Py3.12 | full tuple Py3.13 | repeated metadata prep Py3.12 | repeated metadata prep Py3.13 | metadata-reuse proxy Py3.12 | metadata-reuse proxy Py3.13 |
|---|---:|---:|---:|---:|---:|---:|
| small frozen 3 | 11.02 ms | 8.54 ms | 7.98 ms | 6.34 ms | 62 µs | 54 µs |
| wide frozen 8 | 20.50 ms | 16.31 ms | 14.91 ms | 12.05 ms | 68 µs | 55 µs |
| slotted frozen 4 | 13.36 ms | 10.35 ms | 9.27 ms | 7.44 ms | 63 µs | 50 µs |
| mixed frozen 5 | 17.72 ms | 13.84 ms | 10.86 ms | 8.72 ms | 64 µs | 53 µs |

Field-name JSON proxy medians at size 1000 ranged from about 5.51–12.52 ms on Python 3.12 and 4.59–10.50 ms on Python 3.13. Recursive field-value encoding proxies remained material as well, especially for the mixed-value shape.

These independently timed proxies cannot be interpreted as percentages of the full serializer. They do establish that repeated metadata preparation/field-name encoding is sufficiently expensive relative to a prepared-descriptor reuse proxy to justify testing a scoped metadata-reuse candidate.

## Phase-A adjudication

**Phase B is admitted as a non-production experiment.**

The candidate should reuse immutable descriptor material only within one canonicalization call:

- exact dataclass type identity;
- qualified type-name JSON bytes;
- sorted field names/descriptors;
- pre-encoded field-name JSON prefixes.

It must still read every actual field value and recursively encode it with existing canonical semantics.

The candidate is deliberately **per-call scoped**, not a persistent global cache. This avoids turning dynamic Python class metadata mutation across calls into an unmeasured semantic assumption.

## Phase-B gate

Before any production code is touched, the candidate must:

1. equal both production and frozen-G1 bytes for every declared payload;
2. be measured counterbalanced against the current production path in the same job;
3. use separate timing/allocation channels;
4. show stable benefit across multiple dataclass shapes on Python 3.12 and 3.13;
5. retain direct non-dataclass regression checks if production adoption is later considered.

## Claim boundary

G14 Phase A is environment-specific decomposition evidence. It does not prove exact nested attribution, algorithmic optimality, portable speedup, workload prevalence, formal correctness, security, federation, T4/T5 readiness, hardware suitability, accelerator readiness, deployment readiness, or semantic truth. No native extension or hardware accelerator is selected.
