# QIC Governance

## Purpose

QIC governance exists to keep implementation, evidence, authority, and public claims synchronized as the system evolves.

## Canonical surfaces

- **Public executable surface:** this GitHub repository.
- **Canonical manuscript/continuity surface:** the maintained QIC Google Drive working tree.
- **Public releases:** tagged GitHub releases and frozen release artifacts derived from canonical state.

Where prose and code diverge, neither silently overrides the other: the discrepancy must be resolved explicitly and the affected state documents updated.

## Change classes

### Documentation-only

May update explanatory material without changing runtime semantics.

### Architectural decision

Requires an ADR when it changes a public interface, constitutional boundary, authority rule, state model, or implementation direction.

### Runtime change

Requires tests appropriate to the affected layer and an explicit claim-boundary review.

### Formal/qualification change

Requires evidence identifying the exact modeled/tested scope.

### Cyber-physical or engineering change

Requires separate physical/engineering authority, qualification, commissioning, and evidence. A Git merge alone never authorizes a physical effect.

## Pull request discipline

PR descriptions should answer:

1. What changes?
2. Which invariant/requirement does it implement or affect?
3. What authority boundary is involved?
4. What tests/evidence support the change?
5. Does the public maturity claim change?
6. Which documentation/state files need synchronization?

## Claim discipline

The repository follows `CLAIM_BOUNDARY.md`. A contributor must not promote a capability from conceptual to implemented/tested/formal/hardware/deployed status without corresponding evidence in the repository or linked release artifact.

## Architecture decisions

Material architectural changes should be captured under `docs/adr/` using monotonically numbered ADRs. Superseded ADRs remain in history and point to their successor.

## Security and private material

Secrets, credentials, private partner information, sensitive infrastructure configuration, and confidential experimental data must not be committed. Private development may use the canonical internal-development Drive surface or a future private Git repository when Git-native private collaboration becomes necessary.

## Release authority

A release is a public statement of what the project can substantiate at that point in time. Release notes must include scope, evidence, limitations, and known unresolved issues.
