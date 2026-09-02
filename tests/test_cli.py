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


def test_python_module_cli_matches_console_contract() -> None:
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
    assert manifest["implementation_sequence"]["G6"] == "MERGED"
    assert manifest["implementation_sequence"]["G7"] == "MERGED"
    assert manifest["implementation_sequence"]["G8"] == "ACTIVE"
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
    assert "do not certify" in manifest["claim_boundary"]


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
