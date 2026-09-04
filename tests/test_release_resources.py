from __future__ import annotations

import json
import tomllib
from pathlib import Path

import qic
from qic.resources import resource_json, resource_text


ROOT = Path(__file__).parents[1]


def test_packaged_registries_match_public_source_files() -> None:
    for name in ("transitions.json", "root_ontology.json", "authority_domains.json", "kbi.json"):
        source = json.loads((ROOT / "registry" / name).read_text(encoding="utf-8"))
        packaged = resource_json(f"registry/{name}")
        assert packaged == source


def test_packaged_manifest_and_claim_boundary_match_public_source_files() -> None:
    assert resource_json("QIC_MANIFEST.json") == json.loads(
        (ROOT / "QIC_MANIFEST.json").read_text(encoding="utf-8")
    )
    assert resource_text("CLAIM_BOUNDARY.md") == (ROOT / "CLAIM_BOUNDARY.md").read_text(
        encoding="utf-8"
    )


def test_package_version_matches_project_metadata_and_release_manifest() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    manifest = resource_json("QIC_MANIFEST.json")
    assert qic.__version__ == project["version"] == manifest["release"]["candidate"] == "1.0.0rc0"


def test_release_manifest_keeps_constitutional_nonclaims() -> None:
    manifest = resource_json("QIC_MANIFEST.json")
    for slice_id in ("G8", "RC0", "G9", "G10", "G11", "G12", "G13"):
        assert manifest["implementation_sequence"][slice_id] == "MERGED"
    assert manifest["release"]["phase"] == "RC0_QUALIFIED_PUBLICATION_PENDING"
    assert manifest["transition_profile"]["not_enabled"] == ["T4", "T5"]
    assert manifest["maturity"] == {
        "semantic": "TESTED",
        "evidence": "SUPPORTED",
        "formal": "NONE",
        "hardware": "NONE",
        "deployment": "LOCAL",
    }
    assert "No universal durable crash-recovery guarantee" in manifest["explicit_nonclaims"]
    assert "No accelerator implementation or hardware recommendation claim" in manifest["explicit_nonclaims"]
    assert manifest["last_completed_engineering"]["slice"] == "G13"
    assert manifest["last_completed_engineering"]["merge_commit"] == "a826d51848a66825131406538429ed929a112ce5"
    assert manifest["canonical_workload_generalization"]["status"] == "MERGED"
    assert manifest["canonical_workload_generalization"]["qualified_head"] == "9c7370a6ceacf77c846df5fc74c88a358297e107"
    assert manifest["canonical_workload_generalization"]["full_ci_run"] == "33860813177"
    assert manifest["canonical_workload_generalization"]["workload_atlas_run"] == "33860813207"
    assert manifest["residual_canonicalization"]["status"] == "MERGED"
    assert manifest["residual_canonicalization"]["full_ci_run"] == "33804645433"
    assert manifest["algorithmic_optimization"]["status"] == "MERGED"
    assert manifest["algorithmic_optimization"]["qualified_run"] == "33799603266"
    assert manifest["performance_observatory"]["status"] == "MERGED"
