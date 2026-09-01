"""Explicit public maturity labels for QIC artifacts and claims."""

from __future__ import annotations

from enum import IntEnum


class Maturity(IntEnum):
    """Ordered evidence maturity used for public capability claims.

    Ordering is conservative and only supports comparisons. Moving an artifact
    upward still requires explicit evidence; the enum itself does not grant it.
    """

    CONCEPTUAL = 0
    IMPLEMENTED = 1
    TESTED = 2
    FORMALLY_MODELED = 3
    SIMULATED = 4
    HARDWARE_TESTED = 5
    DEPLOYED = 6
    INDEPENDENTLY_REPLICATED = 7

    def can_claim(self, requested: "Maturity") -> bool:
        """Return whether this evidence level is at least the requested level."""

        return self >= requested
