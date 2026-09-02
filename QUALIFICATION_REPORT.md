# QIC G8 Qualification Report

**Status:** qualification PASS candidate; merge is permitted only if the exact report-sealed PR head is green on Python 3.12 and 3.13.

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

## Qualification history

### First G8 CI campaign — blocked as designed

PR #19 initial qualification head: `f524d5905d787e4f1ce59680c828596510351856`

GitHub Actions run: `33656722959`

Result on Python 3.12: **85 passed, 11 failed**. The failure was not a production constitutional bypass. The scalar-maturity modeled-mutant fixture was malformed: the synthetic scalar score still failed the requirement, so only 4/5 modeled mutants were killed. The older G7 CLI tests also correctly failed because their expected active/merged state had not yet been advanced to G8.

Containment response:

- no production maturity, authority, transition, Chrono, or KBI gate was weakened;
- the scalar mutant fixture was corrected so semantic/evidence prestige can falsely compensate for missing hardware only in the modeled defective path;
- legacy CLI tests were advanced to merged G7 / active G8 expectations;
- the corrected qualification fixture is isolated in `qic/qualification_fixture_patch.py` and explicitly documented as a G8 harness correction.

### Corrected G8 CI campaign — PASS

Reviewed qualification head: `a1a27d378812b277c1e230d1beb5018e7469acba`

GitHub Actions run: `33656980528`

- Python 3.12: **96 passed**
- Python 3.13: **full suite passed**
- workflow conclusion: **success**
- all nine qualification checks passed;
- all five declared critical modeled mutants were killed;
- T4/T5 remained `FAMILY_NOT_ENABLED` under matching A_P/A_X authority;
- public maturity remained `formal=NONE`, `hardware=NONE`, `deployment=LOCAL`;
- aggregate `qic --json verify` and targeted `qic --json verify qualification` passed.

### Documentation-sealed pre-merge recheck — PASS

Report-predecessor head: `3c9f668c3723864e8fac79416144538d005a01d0`

GitHub Actions run: `33657163256`

- Python 3.12: full suite passed
- Python 3.13: full suite passed
- workflow conclusion: **success**

This report normalization itself changes only documentation. The exact head containing this normalized report must receive one additional green Python 3.12/3.13 CI run before PR #19 is merged. The GitHub PR/merge record is the authoritative evidence that this final exact-head condition was satisfied; no further repository-content change is admissible before merge without restarting the exact-head qualification gate.

## Failure atlas

The normative failure/containment map is `docs/qualification/FAILURE_ATLAS.yaml`. It includes canonical ambiguity, maturity collapse, authority amplification, stale/unauthorized transitions, physical/evolutionary bypass, Chrono tamper/truncation, evidence echo, contradiction suppression, and public claim inflation.

## Chrono residual boundary

An internally valid historical prefix may verify as a valid prefix. Completeness/recency cannot be inferred from that prefix alone. G8 therefore requires an independently retained expected length/head event/head witness anchor to detect valid-prefix suffix truncation. This is a retained limitation, not a defect hidden by the qualification result.

## Residual limitations

G8 does not establish or implement:

- formal-runtime verification;
- cryptographic identity/nonrepudiation;
- durable transaction journaling or crash recovery;
- federation/distributed consensus;
- hardware qualification;
- physical actuation or physical safety qualification;
- coverage-guided fuzzing or exhaustive source mutation analysis;
- semantic/scientific/legal truth certification.

The five modeled mutants are targeted constitutional defect models, not exhaustive mutation coverage.

## RC0 gate

`QIC-v1 RC0` becomes admissible only after the exact report-sealed PR head passes Python 3.12/3.13 CI and PR #19 is merged without further repository-content changes.
