from __future__ import annotations

import json
from pathlib import Path

from qic.core import (
    DeploymentMaturity,
    EvidenceMaturity,
    FormalMaturity,
    HardwareMaturity,
    MaturityVector,
    ROOT_ONTOLOGY,
    RootOntology,
    SemanticMaturity,
    canonical_text,
    digest_hex,
    ontology_from_id,
)


def test_root_ontology_is_exactly_seven_stable_classes() -> None:
    assert tuple(item.name for item in ROOT_ONTOLOGY) == (
        "STATE",
        "ACTOR",
        "OPERATION",
        "CONSTRAINT",
        "EVIDENCE",
        "RESOURCE",
        "WITNESS",
    )
    assert ontology_from_id("qic:ontology:STATE") is RootOntology.STATE


def test_simulated_hardware_does_not_imply_formal_maturity() -> None:
    vector = MaturityVector(hardware=HardwareMaturity.SIMULATED)
    required = MaturityVector(formal=FormalMaturity.MODELED)
    assert not vector.satisfies(required)
    assert vector.shortfall(required) == ("formal",)


def test_formal_maturity_does_not_imply_hardware_tested() -> None:
    vector = MaturityVector(formal=FormalMaturity.MACHINE_CHECKED)
    required = MaturityVector(hardware=HardwareMaturity.HARDWARE_TESTED)
    assert not vector.satisfies(required)
    assert vector.shortfall(required) == ("hardware",)


def test_deployment_does_not_imply_independent_replication() -> None:
    vector = MaturityVector(deployment=DeploymentMaturity.DEPLOYED)
    required = MaturityVector(evidence=EvidenceMaturity.INDEPENDENTLY_REPLICATED)
    assert not vector.satisfies(required)
    assert vector.shortfall(required) == ("evidence",)


def test_componentwise_requirements_can_be_satisfied() -> None:
    vector = MaturityVector(
        semantic=SemanticMaturity.TESTED,
        evidence=EvidenceMaturity.CORROBORATED,
        formal=FormalMaturity.MODELED,
        hardware=HardwareMaturity.PROTOTYPE,
        deployment=DeploymentMaturity.LOCAL,
    )
    required = MaturityVector(
        semantic=SemanticMaturity.IMPLEMENTED,
        evidence=EvidenceMaturity.SUPPORTED,
        formal=FormalMaturity.MODELED,
        hardware=HardwareMaturity.SIMULATED,
        deployment=DeploymentMaturity.NONE,
    )
    assert vector.satisfies(required)
    assert vector.shortfall(required) == ()


def test_partial_order_can_express_incomparable_vectors() -> None:
    formal = MaturityVector(formal=FormalMaturity.MACHINE_CHECKED)
    hardware = MaturityVector(hardware=HardwareMaturity.HARDWARE_TESTED)
    assert not formal.dominates(hardware)
    assert not hardware.dominates(formal)


def test_maturity_vector_golden_vector() -> None:
    vector_path = Path(__file__).parent / "vectors" / "maturity_vector_v1.json"
    payload = json.loads(vector_path.read_text(encoding="utf-8"))
    spec = payload["vector"]
    vector = MaturityVector(
        semantic=SemanticMaturity[spec["semantic"]],
        evidence=EvidenceMaturity[spec["evidence"]],
        formal=FormalMaturity[spec["formal"]],
        hardware=HardwareMaturity[spec["hardware"]],
        deployment=DeploymentMaturity[spec["deployment"]],
    )
    assert canonical_text(vector) == payload["canonical"]
    assert digest_hex(vector, domain=payload["digest_domain"]) == payload["sha256"]
