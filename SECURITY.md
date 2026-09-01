# Security Policy

## Scope

QIC is in early implementation convergence. Security claims are therefore limited to specific implemented and tested controls; the architecture document alone is not a security certification.

## Reporting vulnerabilities

Please report potential vulnerabilities privately to the repository owner rather than publishing exploit details in a public issue before a fix or mitigation can be evaluated.

## Sensitive material

Do not commit:

- credentials, API keys, tokens, private keys, recovery codes;
- private partner/customer information;
- internal infrastructure addresses or secrets;
- unreleased safety-critical plant configuration;
- confidential experimental datasets;
- personal data without an explicit lawful/publication basis.

## Security architecture principles

QIC's constitutional separation rules are intended to reduce classes of hidden authority escalation, but they are not by themselves proof of security. Relevant runtime controls must be independently implemented and tested.

Important boundaries include:

- capability/authority non-amplification;
- receive != admit for federation;
- proposal != canonical-state mutation;
- bounded registered operations rather than unrestricted execution in the core;
- explicit physical authorization for cyber-physical effects;
- append-only witness/causal history where implemented.

## Supported versions

Until the first tagged stable release, only the current `main` branch and explicitly named release candidates should be treated as maintained.

## Physical safety

Security reports involving cyber-physical operation must distinguish software behavior from real-world safety. Reference physical work should remain low consequence unless separately engineered and commissioned.
