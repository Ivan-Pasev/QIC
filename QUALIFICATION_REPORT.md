# QIC G8 Qualification Report

**Status:** qualification branch active; final CI evidence pending

**Scope:** adversarial constitutional qualification over the implemented G0–G7 local genesis stack.

## Qualification boundary

A PASS in this report establishes only the declared local structural properties exercised by the test campaign on the tested source/environment. It does not certify semantic truth, production security, formal correctness, physical safety, legal compliance, deployment readiness, cryptographic identity, federation, distributed consensus, hardware qualification, or durable crash recovery.

## Release-blocking campaign

G8 defines nine structural qualification checks:

1. canonical fail-closed behavior and digest-domain separation;
2. maturity-vector partial-order independence;
3. authority non-amplification and revocation containment;
4. transition stale/unauthorized atomicity plus T4/T5 denial;
5. Chrono tamper detection and externally anchored suffix-truncation boundary;
6. KBI evidence-echo resistance and contradiction preservation;
7. registry/runtime parity;
8. public claim/maturity surface audit;
9. modeled constitutional mutation campaign.

## Modeled constitutional mutants

Five declared critical defect models must be killed:

- `scalar_maturity_collapse`
- `authority_any_of`
- `enable_t4`
- `ignore_chrono_anchor`
- `count_echo_bindings`

These are deterministic modeled defects, not a claim of exhaustive source-code mutation coverage. A mutant is killed only when the real runtime contains/rejects the adversarial case while the permissive modeled defect would accept it.

## Failure atlas

The normative failure/containment map is `docs/qualification/FAILURE_ATLAS.yaml`. It includes canonical ambiguity, maturity collapse, authority amplification, stale/unauthorized transitions, physical/evolutionary bypass, Chrono tamper/truncation, evidence echo, contradiction suppression, and public claim inflation.

## Chrono residual boundary

An internally valid historical prefix may verify as a valid prefix. Completeness/recency cannot be inferred from that prefix alone. G8 therefore requires an independently retained expected length/head event/head witness anchor to detect valid-prefix suffix truncation. This is a retained limitation, not a defect hidden by the qualification result.

## Current evidence state

The branch provides:

- `qic/qualification.py`
- `tests/adversarial/test_qualification.py`
- `qic verify qualification`
- aggregate `qic verify` including G8
- `docs/qualification/FAILURE_ATLAS.yaml`
- ADR-0009
- G8 manifest/traceability updates

Final PASS status, exact reviewed head, and Python 3.12/3.13 CI evidence are recorded only after the complete branch passes review and CI. Until then, G8 remains **ACTIVE**, not qualified or released.

## RC0 gate

`QIC-v1 RC0` is admissible only after:

- all G8 checks pass on Python 3.12 and 3.13;
- all five declared critical modeled mutants are killed;
- no discovered constitutional defect remains uncorrected;
- public claim/maturity surfaces remain conservative;
- T4/T5 remain non-executable everywhere in the reference runtime;
- the final reviewed branch head is merged.
