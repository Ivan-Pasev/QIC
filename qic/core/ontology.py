"""Stable root ontology for QIC constitutional objects."""

from __future__ import annotations

from enum import Enum
from typing import Final


class RootOntology(str, Enum):
    """The seven irreducible QIC ontology classes.

    Values are stable public identifiers. Renaming a Python member may be a
    source-level change; changing a value is a wire-level compatibility change.
    """

    STATE = "qic:ontology:STATE"
    ACTOR = "qic:ontology:ACTOR"
    OPERATION = "qic:ontology:OPERATION"
    CONSTRAINT = "qic:ontology:CONSTRAINT"
    EVIDENCE = "qic:ontology:EVIDENCE"
    RESOURCE = "qic:ontology:RESOURCE"
    WITNESS = "qic:ontology:WITNESS"


ROOT_ONTOLOGY: Final[tuple[RootOntology, ...]] = tuple(RootOntology)


def ontology_from_id(identifier: str) -> RootOntology:
    """Resolve a stable ontology identifier or fail closed."""

    try:
        return RootOntology(identifier)
    except ValueError as exc:
        raise ValueError(f"unknown QIC root ontology identifier: {identifier!r}") from exc
