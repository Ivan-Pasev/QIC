# ADR-0010 — RC0 Prerelease Publication Boundary

- **Status:** Accepted for publication preparation
- **Date:** 2026-09-02

## Context

QIC `1.0.0rc0` has passed the integrated RC0 build/install/reproducibility gate and merged to `main`. The remaining publication action is creation of a GitHub tag/prerelease. Publication must preserve the exact qualified source/artifact relationship and must not silently substitute rebuilt or differently qualified artifacts.

## Decision

The public prerelease identifier is `v1.0.0rc0` and must target merge commit `588694dda816c6cb712d1812c6bbe23ca5092198`.

The qualified source head is `7a3234cb433e3b61bc9f858e8de9b0645378a845`, validated by GitHub Actions run `33675547670` on Python 3.12 and 3.13 including clean wheel/sdist installs and cross-Python reproducibility.

The release evidence package hashes are:

- wheel `4b6c7af7113db82fbdd55b42e94cbb6a960b35a54eb0ee88876ffa3f3b60b1a6`
- normalized sdist `4d248bb4aef7ae8892eecdc711e6ef7e82661d8e63f39edb2b2903b85d6a221d`

Publication must not increase maturity or enable T4/T5. If an artifact is rebuilt and differs from the qualified digest, it is a new release candidate input and must be requalified before publication under a qualified release identifier.

## Consequence

`RC0_PUBLICATION.md` becomes the human-readable publication record. GitHub release/tag creation is an external publication mutation separate from constitutional/runtime implementation. The currently connected GitHub action surface does not expose release/tag creation, so publication readiness and publication completion are tracked separately.
