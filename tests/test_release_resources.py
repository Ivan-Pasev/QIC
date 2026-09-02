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
    assert manifest["implementation_sequence"]["G8"] == "MERGED"
    assert manifest["implementation_sequence"]["RC0"] == "MERGED"
    assert manifest["implementation_sequence"]["G9"] == "MERGED"
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
    assert manifest["last_completed_engineering"]["slice"] == "G9"
