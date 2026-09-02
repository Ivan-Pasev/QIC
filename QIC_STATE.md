# QIC State

Last updated: 2026-09-02

## Canonical status

**Phase:** Release Convergence

**Active slice:** `QIC-v1 RC0 — Integrated genesis release convergence`

**Release candidate:** `1.0.0rc0`

**Public repository:** `Ivan-Pasev/QIC`

**Canonical continuity root:** Google Drive `QIC_CANONICAL_WORKING_TREE`

## Established

- G0–G7 are merged and remain the qualified local constitutional implementation base.
- G8 Adversarial Constitutional Qualification merged via PR #19 as `b0c4f446dce21317cbd4cfc943633ee57507a8c8`.
- The exact G8 report-sealed head `d0416802c58590e67d580826c2868ee14bf74477` passed final Python 3.12/3.13 CI run `33657284850` before merge.
- G8 exercises nine structural qualification checks and five declared modeled constitutional mutants.
- T4 Physical and T5 Evolutionary remain explicitly `NOT_ENABLED`.
- RC0 Issue is `#20`; branch `qic-v1/rc0-convergence` is active from the qualified G8 merge.

## RC0 implementation boundary

RC0 adds release engineering only, not constitutional capability:

- package version normalized to PEP 440 prerelease `1.0.0rc0`;
- public root manifest updated to G8=MERGED / RC0=ACTIVE without maturity inflation;
- immutable release resources packaged under `qic.resources`;
- public registries, release manifest, and claim boundary are available from installed wheel/sdist context;
- `qic.release_cli` redirects only read-only metadata roots from repository layout to packaged resources;
- installed `qic --json status` reports G8 implemented and RC0 active;
- source↔packaged registry/manifest/claim-boundary parity tests added;
- CI extended with a clean artifact gate on Python 3.12 and 3.13;
- artifact gate builds wheel+sdist, inspects required package resources, installs the wheel into a clean venv outside the checkout, runs `qic --json verify` and `qic --json verify qualification`, checks package/metadata version agreement, generates SHA-256 inventories, and uploads evidence artifacts.

## Release defect discovered during RC0

Editable source verification depended on repository-relative `registry/`, `QIC_MANIFEST.json`, and `CLAIM_BOUNDARY.md` paths. A wheel installed outside the repository could therefore build successfully while its verification surface lacked those files.

RC0 contains this as a packaging defect rather than weakening verification: the canonical public metadata are copied into tested package resources and the release entry point redirects read-only lookup to those resources. Authority, transition, KBI, Chrono, and G8 qualification semantics remain unchanged.

## Claim boundary

RC0 packaging and clean-install verification are release-engineering evidence only. They do not upgrade formal, hardware, deployment, security, physical-control, federation, distributed-consensus, or semantic-truth maturity.

Current public maturity remains:

- semantic: TESTED
- evidence: SUPPORTED
- formal: NONE
- hardware: NONE
- deployment: LOCAL

## Current RC0 exit gate

- create `RELEASE_NOTES_RC0.md` and release traceability/evidence description;
- open RC0 PR from `qic-v1/rc0-convergence`;
- require source suite green on Python 3.12/3.13;
- require built wheel/sdist and clean installed-artifact verification green on Python 3.12/3.13;
- inspect uploaded artifact SHA-256 inventories and clean-install evidence;
- review complete diff for accidental runtime-semantic or maturity expansion;
- fix any discovered release defect and rerun exact-head qualification;
- merge only the reviewed exact green head;
- create a GitHub prerelease/tag only after the merged RC0 source/artifact evidence is consistent.

## Next admissible action

Finish RC0 release notes/traceability, open the RC0 PR, qualify source and built artifacts, inspect evidence artifacts and diff, then merge or block based on the exact evidence.

## Continuation rule

Every substantial implementation/release change should update this file if phase, maturity, blockers, or next action change. Public claims must remain consistent with `CLAIM_BOUNDARY.md`, `QIC_MANIFEST.json`, and the G8 qualification boundary.
