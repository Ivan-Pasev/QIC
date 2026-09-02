"""Domain-separated SHA-256 digests over QIC canonical bytes."""

from __future__ import annotations

import hashlib
from typing import Any, Final

from .canonical import canonical_bytes


DIGEST_VERSION: Final[str] = "QIC-DIGEST/1.0"


class DigestDomainError(ValueError):
    """Raised when a digest domain is empty or structurally ambiguous."""


def _domain_prefix(domain: str) -> bytes:
    if not domain or "\x00" in domain:
        raise DigestDomainError("digest domain must be non-empty and contain no NUL")
    return (
        DIGEST_VERSION.encode("ascii")
        + b"\x00"
        + domain.encode("utf-8")
        + b"\x00"
    )


def digest_bytes(value: Any, *, domain: str) -> bytes:
    """Return a domain-separated SHA-256 digest of the canonical value."""

    hasher = hashlib.sha256()
    hasher.update(_domain_prefix(domain))
    hasher.update(canonical_bytes(value))
    return hasher.digest()


def digest_hex(value: Any, *, domain: str) -> str:
    """Return the lower-case hexadecimal QIC digest."""

    return digest_bytes(value, domain=domain).hex()
