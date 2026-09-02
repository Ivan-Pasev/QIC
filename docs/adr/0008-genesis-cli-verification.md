# ADR-0008 — Genesis CLI and Structural Verification

- **Status:** Accepted for G7 implementation
- **Date:** 2026-09-02

## Context

G0–G6 provide a tested local constitutional kernel, but use is primarily through Python APIs and tests. QIC needs a compact public command surface that lets humans, CI systems, and other LLM/developer environments inspect the same implemented state without creating a privileged administration path.

## Decision

G7 adds a dependency-free `qic` console entry point implemented with Python `argparse`.

The command surface is intentionally read/verify oriented:

- `qic version`
- `qic status`
- `qic constitution`
- `qic registry <name>`
- `qic verify [canonical|registries|transition|chrono|kbi]`

`qic verify` without a target runs the aggregate G0–G7 structural verification campaign. JSON mode is available with `--json` and uses sorted compact JSON for deterministic automation output.

The CLI invokes the same public G1–G6 Python objects used by the test suite. It does not have a hidden superuser, grant-minting, KBI promotion, transition-bypass, network, or physical-I/O path.

## Verification scope

The reference aggregate verifies:

1. a frozen G1 state digest vector;
2. runtime/registry parity for transitions, root ontology, authority domains, and KBI enums;
3. a deterministic accepted G4 computational transition and continued T4 denial even when a matching physical grant is supplied;
4. a G5 accepted transition chain plus the externally anchored valid-prefix truncation boundary;
5. a G6 claim/evidence/binding/promotion campaign plus an unauthorized promotion that is rejected without KBI/runtime commit and remains represented in Chrono.

This is a structural self-test, not a certification regime.

## Manifest

`QIC_MANIFEST.json` publishes the implemented slice state, enabled transition families, authority domains, root ontology, a deliberately conservative maturity vector, explicit nonclaims, and the public claim boundary.

`TRACEABILITY.yaml` maps G0–G7 implementation surfaces to tests and ADRs.

The G7 maturity vector remains intentionally conservative. In particular:

- formal = `NONE` because the Lean/formal-runtime layer is not implemented;
- hardware = `NONE` because no hardware qualification exists;
- deployment = `LOCAL` only;
- T4/T5 remain `NOT_ENABLED`.

## Claim boundary

A passing `qic verify` run establishes only that the declared local structural checks pass for the installed source state and environment. It does not certify semantic truth, production security, formal correctness, physical safety, legal compliance, deployment readiness, cryptographic identity, distributed consensus, or durable crash recovery.

CLI visibility also does not create authority. Reading a registry, displaying an authority domain, or running a reference transition does not mint a grant or authorize an external operation.

## Consequences

Positive:

- QIC has a portable human/automation inspection surface;
- public repo state can be checked without writing custom Python;
- JSON output supports external CI and LLM tooling;
- manifest and traceability claims become machine-inspectable;
- structural self-tests preserve the constitutional claim boundary.

Limitations:

- registry commands currently read repository registry files and are intended for source/editable-install operation;
- G7 is not a daemon or remote API;
- G7 does not add durable storage, signatures, federation, hardware, or physical control.

## Deferred

G8 will adversarially qualify the complete genesis stack and harden release/negative-test gates. Broader CLI mutation workflows, if ever introduced, must use the same explicit authority/transition paths and require their own constitutional review.
