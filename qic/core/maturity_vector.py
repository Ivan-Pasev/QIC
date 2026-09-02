"""Independent maturity dimensions for QIC artifacts and releases.

Each dimension has a local ordering used only inside that dimension. There is
no cross-dimension promotion: simulation does not imply formality, deployment
does not imply replication, and formal work does not imply hardware evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class SemanticMaturity(IntEnum):
    CONCEPTUAL = 0
    IMPLEMENTED = 1
    TESTED = 2


class EvidenceMaturity(IntEnum):
    NONE = 0
    ASSERTED = 1
    SUPPORTED = 2
    CORROBORATED = 3
    INDEPENDENTLY_REPLICATED = 4


class FormalMaturity(IntEnum):
    NONE = 0
    MODELED = 1
    MACHINE_CHECKED = 2


class HardwareMaturity(IntEnum):
    NONE = 0
    SIMULATED = 1
    PROTOTYPE = 2
    HARDWARE_TESTED = 3


class DeploymentMaturity(IntEnum):
    NONE = 0
    LOCAL = 1
    PILOT = 2
    DEPLOYED = 3


@dataclass(frozen=True, slots=True)
class MaturityVector:
    """Five-dimensional QIC maturity state.

    `satisfies()` performs a component-wise comparison. It intentionally does
    not collapse the vector to a single scalar rank.
    """

    semantic: SemanticMaturity = SemanticMaturity.CONCEPTUAL
    evidence: EvidenceMaturity = EvidenceMaturity.NONE
    formal: FormalMaturity = FormalMaturity.NONE
    hardware: HardwareMaturity = HardwareMaturity.NONE
    deployment: DeploymentMaturity = DeploymentMaturity.NONE

    def satisfies(self, required: "MaturityVector") -> bool:
        """Return true only when every requested dimension is satisfied."""

        return (
            self.semantic >= required.semantic
            and self.evidence >= required.evidence
            and self.formal >= required.formal
            and self.hardware >= required.hardware
            and self.deployment >= required.deployment
        )

    def shortfall(self, required: "MaturityVector") -> tuple[str, ...]:
        """Return the dimension names that do not meet a requirement."""

        missing: list[str] = []
        if self.semantic < required.semantic:
            missing.append("semantic")
        if self.evidence < required.evidence:
            missing.append("evidence")
        if self.formal < required.formal:
            missing.append("formal")
        if self.hardware < required.hardware:
            missing.append("hardware")
        if self.deployment < required.deployment:
            missing.append("deployment")
        return tuple(missing)

    def dominates(self, other: "MaturityVector") -> bool:
        """Component-wise partial-order dominance, including equality."""

        return self.satisfies(other)

    def strictly_dominates(self, other: "MaturityVector") -> bool:
        """Return true when this vector dominates and differs in >=1 dimension."""

        return self.dominates(other) and self != other
