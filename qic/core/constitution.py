"""Genesis constitutional state for QIC.

This module is intentionally small. It exposes immutable constitutional laws
and a snapshot object that can be hashed/serialized by later G1 work.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


PRIME_LAWS: Final[tuple[str, ...]] = (
    "Generation != Authority",
    "Proposal != Canonical Knowledge",
    "Remote State != Local Authority",
    "Decision != Physical Actuation",
    "Learning != Safety-Law Rewrite",
    "Design Generation != Physical Mutation",
    "No Accelerator Without Measured Bottleneck",
    "No Plane May Claim Operational Maturity Beyond Its Actual Evidence",
)


@dataclass(frozen=True, slots=True)
class ConstitutionSnapshot:
    """Immutable genesis constitutional snapshot.

    Deterministic canonical serialization is deliberately deferred to QIC-G1.
    """

    version: str = "QIC-CONSTITUTION/0.0.1"
    prime_laws: tuple[str, ...] = PRIME_LAWS

    def contains(self, law: str) -> bool:
        return law in self.prime_laws
