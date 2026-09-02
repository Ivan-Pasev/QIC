"""G8 qualification-fixture correction discovered by the first CI campaign.

The initial scalar-maturity modeled mutant did not actually produce a false
positive: its scalar score remained below the required score, so the mutant was
not meaningfully exercised. This module replaces only that synthetic mutant
fixture. Production maturity semantics are untouched.

Imported from qic.__init__ so all CLI/module entry paths use the corrected G8
qualification campaign consistently.
"""

from __future__ import annotations

from . import qualification as _qualification
from .core import MaturityVector
from .core.maturity_vector import (
    EvidenceMaturity,
    HardwareMaturity,
    SemanticMaturity,
)


def _corrected_scalar_maturity_mutant() -> bool:
    # A scalar-prestige defect can let strong semantic/evidence scores compensate
    # for zero hardware evidence. The production component-wise partial order must
    # still reject the hardware requirement.
    actual = MaturityVector(
        semantic=SemanticMaturity.TESTED,
        evidence=EvidenceMaturity.CORROBORATED,
        hardware=HardwareMaturity.NONE,
    )
    required = MaturityVector(
        semantic=SemanticMaturity.CONCEPTUAL,
        evidence=EvidenceMaturity.NONE,
        hardware=HardwareMaturity.HARDWARE_TESTED,
    )
    production_accepts = actual.satisfies(required)
    mutant_accepts = (
        int(actual.semantic) + int(actual.evidence) + int(actual.hardware)
        >= int(required.semantic) + int(required.evidence) + int(required.hardware)
    )
    return (not production_accepts) and mutant_accepts


_qualification._MUTANTS = (
    ("scalar_maturity_collapse", _corrected_scalar_maturity_mutant),
    *_qualification._MUTANTS[1:],
)
