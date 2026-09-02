# QIC v1.0.0rc0 — Prerelease Publication Record

## Publication target

Tag/release name: `v1.0.0rc0`

Target commit: `588694dda816c6cb712d1812c6bbe23ca5092198`

Qualified RC0 source head: `7a3234cb433e3b61bc9f858e8de9b0645378a845`

Final RC0 CI run: `33675547670`

## Verified release evidence

The final RC0 gate completed successfully on Python 3.12 and Python 3.13. The workflow verified:

- full source test suite;
- wheel and normalized sdist build;
- required packaged release resources;
- clean wheel install outside the source checkout;
- clean normalized-sdist install outside the source checkout;
- `qic --json verify` from installed artifacts;
- `qic --json verify qualification` from installed artifacts;
- runtime/package version equality at `1.0.0rc0`;
- independent cross-Python artifact/evidence reproducibility.

Reproducible package SHA-256 values recorded by RC0:

- wheel: `4b6c7af7113db82fbdd55b42e94cbb6a960b35a54eb0ee88876ffa3f3b60b1a6`
- normalized sdist: `4d248bb4aef7ae8892eecdc711e6ef7e82661d8e63f39edb2b2903b85d6a221d`

GitHub Actions evidence bundles from final run:

- `qic-rc0-py3.12` — artifact ID `9864248673`
- `qic-rc0-py3.13` — artifact ID `9864247983`

## Claim boundary

`v1.0.0rc0` is a qualified local structural release candidate. Publication does not upgrade QIC maturity or enable new constitutional capability. Public maturity remains semantic `TESTED`, evidence `SUPPORTED`, formal `NONE`, hardware `NONE`, deployment `LOCAL`.

It is not formal verification, production-security certification, hardware qualification, physical-control readiness, federation or distributed-consensus evidence, durable crash-recovery proof, legal/compliance certification, or semantic/scientific truth certification.

T4 Physical and T5 Evolutionary remain `NOT_ENABLED`.

## Publication rule

Create the GitHub prerelease/tag only against target commit `588694dda816c6cb712d1812c6bbe23ca5092198`. Attach or otherwise preserve the qualified wheel/sdist and SHA-256 evidence when the publication surface supports it. Do not rebuild unqualified replacement artifacts under the same tag.

The current connected GitHub action surface can inspect releases but does not expose tag/release creation. This record therefore defines the exact publication payload and prevents ambiguity at the remaining external publication step.
