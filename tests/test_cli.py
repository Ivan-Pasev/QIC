from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from qic.cli import EXIT_PASS, aggregate_verify, main
from qic.core.transition import ENABLED_FAMILIES, TransitionFamily


ROOT = Path(__file__).parents[1]


def test_aggregate_verification_passes_declared_g0_g8_scope() -> None:
    payload = aggregate_verify()
    assert payload["pass"] is True
    assert payload["scope"] == "G0-G8 structural verification"
    assert [check.get("check", check.get("scope")) for check in payload["checks"]] == [
        "canonical",
        "registries",
        "transition",
        "chrono",
        "kbi",
        "G8 adversarial constitutional qualification over G0-G7",
    ]
    assert all(check["pass"] is True for check in payload["checks"])
    assert "does not certify" in payload["claim_boundary"]


def test_cli_json_verify_is_deterministic_and_successful(capsys) -> None:
    assert main(["--json", "verify"]) == EXIT_PASS
    first = capsys.readouterr().out
    assert main(["--json", "verify"]) == EXIT_PASS
    second = capsys.readouterr().out
    assert first == second
    payload = json.loads(first)
    assert payload["pass"] is True


def test_cli_individual_verifiers_pass(capsys) -> None:
    for target in ("canonical", "registries", "transition", "chrono", "kbi", "qualification"):
        assert main(["--json", "verify", target]) == EXIT_PASS
        payload = json.loads(capsys.readouterr().out)
        if target == "qualification":
            assert payload["scope"] == "G8 adversarial constitutional qualification over G0-G7"
        else:
            assert payload["check"] == target
        assert payload["pass"] is True


def test_installed_console_entrypoint_executes_aggregate_verification() -> None:
    result = subprocess.run(
        ["qic", "--json", "verify"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["pass"] is True
    assert payload["scope"] == "G0-G8 structural verification"


def test_python_module_cli_matches_historical_internal_contract() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "qic.cli", "--json", "status"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["implemented_through"] == "G7"
    assert payload["active_implementation"] == "G8"
    assert payload["transition_families_not_enabled"] == ["T4", "T5"]


def test_release_console_status_reports_rc0() -> None:
    result = subprocess.run(
        ["qic", "--json", "status"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["implemented_through"] == "G8"
    assert payload["active_implementation"] == "RC0"
    assert payload["release_candidate"] == "1.0.0rc0"
    assert payload["transition_families_not_enabled"] == ["T4", "T5"]


def test_registry_and_constitution_commands_are_read_only_surfaces(capsys) -> None:
    assert main(["--json", "registry", "kbi"]) == EXIT_PASS
    registry = json.loads(capsys.readouterr().out)
    assert registry["authority_domain"] == "A_E"
    assert registry["resource"] == "state.kbi"

    assert main(["--json", "constitution"]) == EXIT_PASS
    constitution = json.loads(capsys.readouterr().out)
    assert len(constitution["prime_laws"]) >= 1


def test_manifest_matches_runtime_and_does_not_inflate_maturity() -> None:
    manifest = json.loads((ROOT / "QIC_MANIFEST.json").read_text(encoding="utf-8"))
    for slice_id in ("G6", "G7", "G8", "RC0", "G9", "G10", "G11", "G12", "G13"):
        assert manifest["implementation_sequence"][slice_id] == "MERGED"
    assert manifest["release"]["phase"] == "RC0_QUALIFIED_PUBLICATION_PENDING"
    assert manifest["transition_profile"]["enabled"] == [
        family.value for family in sorted(ENABLED_FAMILIES, key=lambda item: item.value)
    ]
    assert manifest["transition_profile"]["not_enabled"] == [
        family.value
        for family in TransitionFamily
        if family not in ENABLED_FAMILIES
    ]
    assert manifest["maturity"]["formal"] == "NONE"
    assert manifest["maturity"]["hardware"] == "NONE"
    assert manifest["maturity"]["deployment"] == "LOCAL"
    assert manifest["qualification"]["release_blocking_on_survivor"] is True
    assert "No formal-runtime verification claim" in manifest["explicit_nonclaims"]
    assert "No hardware-tested claim" in manifest["explicit_nonclaims"]
    assert "No universal durable crash-recovery guarantee" in manifest["explicit_nonclaims"]
    assert manifest["last_completed_engineering"]["slice"] == "G13"
    assert manifest["last_completed_engineering"]["merge_commit"] == "a826d51848a66825131406538429ed929a112ce5"
    assert manifest["performance_observatory"]["status"] == "MERGED"
    assert manifest["performance_observatory"]["qualified_run"] == "33720658546"
    assert manifest["algorithmic_optimization"]["status"] == "MERGED"
    assert manifest["algorithmic_optimization"]["qualified_run"] == "33799603266"
    assert manifest["residual_canonicalization"]["status"] == "MERGED"
    assert manifest["residual_canonicalization"]["full_ci_run"] == "33804645433"
    assert manifest["canonical_workload_generalization"]["status"] == "MERGED"
    assert manifest["canonical_workload_generalization"]["qualified_head"] == "9c7370a6ceacf77c846df5fc74c88a358297e107"
    assert manifest["canonical_workload_generalization"]["full_ci_run"] == "33860813177"
    assert manifest["canonical_workload_generalization"]["workload_atlas_run"] == "33860813207"
    claim_boundary = manifest["claim_boundary"]
    assert "certify semantic truth" in claim_boundary
    assert "universal durable crash recovery" in claim_boundary


def test_cli_surface_contains_no_mutating_authority_command() -> None:
    help_result = subprocess.run(
        ["qic", "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert help_result.returncode == 0
    for forbidden in ("grant", "promote", "mutate", "actuate", "delegate"):
        assert forbidden not in help_result.stdout.lower()
