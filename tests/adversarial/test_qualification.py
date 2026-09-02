from __future__ import annotations

import json
import subprocess
import sys

from qic.cli import EXIT_PASS, main
from qic.qualification import (
    check_authority_nonamplification,
    check_canonical_fail_closed,
    check_chrono_tamper_and_anchor_boundary,
    check_kbi_echo_and_contradiction_containment,
    check_maturity_partial_order,
    check_modeled_mutants_killed,
    check_public_claim_surface,
    check_registry_runtime_parity,
    check_transition_atomicity_and_disabled_families,
    qualification_verify,
)


CHECKS = (
    check_canonical_fail_closed,
    check_maturity_partial_order,
    check_authority_nonamplification,
    check_transition_atomicity_and_disabled_families,
    check_chrono_tamper_and_anchor_boundary,
    check_kbi_echo_and_contradiction_containment,
    check_registry_runtime_parity,
    check_public_claim_surface,
    check_modeled_mutants_killed,
)


def test_each_adversarial_qualification_check_passes_independently() -> None:
    for check in CHECKS:
        result = check()
        assert result["pass"], f"{check.__name__}: {result['detail']}"


def test_aggregate_qualification_is_release_blocking() -> None:
    result = qualification_verify()
    assert result["pass"]
    assert result["scope"] == "G8 adversarial constitutional qualification over G0-G7"
    assert len(result["checks"]) == len(CHECKS)
    assert all(check["pass"] for check in result["checks"])


def test_modeled_mutation_campaign_kills_every_declared_mutant() -> None:
    result = check_modeled_mutants_killed()
    assert result["pass"]
    assert "killed=5/5" in result["detail"]


def test_cli_qualification_target_returns_pass(capsys) -> None:
    code = main(["--json", "verify", "qualification"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert code == EXIT_PASS
    assert payload["pass"] is True
    assert payload["scope"] == "G8 adversarial constitutional qualification over G0-G7"


def test_cli_aggregate_includes_g8_qualification(capsys) -> None:
    code = main(["--json", "verify"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert code == EXIT_PASS
    assert payload["pass"] is True
    assert payload["scope"] == "G0-G8 structural verification"
    qualification_rows = [
        row for row in payload["checks"] if row.get("scope") == "G8 adversarial constitutional qualification over G0-G7"
    ]
    assert len(qualification_rows) == 1
    assert qualification_rows[0]["pass"] is True


def test_installed_module_qualification_is_machine_readable() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "qic.cli", "--json", "verify", "qualification"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["pass"] is True
    assert "certification" in payload["claim_boundary"].lower()
