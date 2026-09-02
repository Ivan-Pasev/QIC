"""Explicit, non-cumulative public maturity labels for QIC claims."""

from __future__ import annotations

from enum import Enum


class Maturity(str, Enum):
    """Evidence/maturity labels used by public QIC claims.

    These labels are intentionally *not* ordered. For example, SIMULATED does
    not imply FORMALLY_MODELED, and FORMALLY_MODELED does not imply TESTED or
    HARDWARE_TESTED. A future evidence profile may carry multiple labels when
    independently supported.
    """

    CONCEPTUAL = "CONCEPTUAL"
    IMPLEMENTED = "IMPLEMENTED"
    TESTED = "TESTED"
    FORMALLY_MODELED = "FORMALLY_MODELED"
    SIMULATED = "SIMULATED"
    HARDWARE_TESTED = "HARDWARE_TESTED"
    DEPLOYED = "DEPLOYED"
    INDEPENDENTLY_REPLICATED = "INDEPENDENTLY_REPLICATED"

    def supports(self, requested: "Maturity") -> bool:
        """Conservatively support only the exact evidenced label.

        Cross-label implication is deliberately forbidden at G0. Later evidence
        profiles may explicitly carry several supported labels.
        """

        return self is requested
