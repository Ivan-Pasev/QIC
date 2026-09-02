"""RC0 installed-artifact entry point.

The qualified G7/G8 runtime historically resolves public registries and claim
metadata relative to a repository checkout. RC0 redirects those read-only roots
to package resources so wheel/sdist installs verify outside a source tree.
"""

from __future__ import annotations

import sys
from pathlib import Path

from . import cli as _cli
from . import qualification as _qualification
from .core.transition import ENABLED_FAMILIES, TransitionFamily
from .resources import resource_json, resource_root, resource_text


# Read-only root redirection only. No authority, transition, KBI, Chrono, or
# qualification semantics are changed by this release wrapper.
_cli._root = resource_root
_qualification._root = resource_root


def _release_public_claim_surface() -> dict[str, object]:
    """Run G8's public-claim audit against the installed artifact layout."""

    try:
        manifest = resource_json("QIC_MANIFEST.json")
        cli_text = Path(_cli.__file__).read_text(encoding="utf-8") + Path(__file__).read_text(
            encoding="utf-8"
        )
        claim_boundary = resource_text("CLAIM_BOUNDARY.md")
    except (OSError, ValueError) as exc:
        return _qualification._check("public_claim_surface", False, f"read_failure={exc}")

    maturity = manifest.get("maturity", {})
    maturity_ok = (
        maturity.get("formal") == "NONE"
        and maturity.get("hardware") == "NONE"
        and maturity.get("deployment") == "LOCAL"
    )
    transition_profile = manifest.get("transition_profile", {})
    disabled_ok = transition_profile.get("not_enabled") == ["T4", "T5"]
    nonclaims = " ".join(manifest.get("explicit_nonclaims", [])).lower()
    nonclaims_ok = all(
        token in nonclaims
        for token in ("formal", "hardware", "physical", "federation", "durable", "truth")
    )
    mutation_surface_absent = all(
        token not in cli_text
        for token in (
            "mint_grant(",
            "bypass_authority",
            "enable_physical",
            "enable_evolutionary",
        )
    )
    boundary_ok = "does not" in claim_boundary.lower() or "not" in claim_boundary.lower()
    return _qualification._check(
        "public_claim_surface",
        maturity_ok and disabled_ok and nonclaims_ok and mutation_surface_absent and boundary_ok,
        f"maturity={maturity_ok},disabled={disabled_ok},nonclaims={nonclaims_ok},cli_no_bypass={mutation_surface_absent},boundary={boundary_ok}",
    )


_qualification.check_public_claim_surface = _release_public_claim_surface
_qualification._CHECKS = tuple(
    _release_public_claim_surface if check.__name__ == "check_public_claim_surface" else check
    for check in _qualification._CHECKS
)


def main(argv: list[str] | None = None) -> int:
    resolved = list(sys.argv[1:] if argv is None else argv)
    parsed = _cli.build_parser().parse_args(resolved)
    if parsed.command == "status":
        payload = {
            "active_implementation": "RC0",
            "claim_boundary": _cli._CLAIM_BOUNDARY,
            "implemented_through": "G8",
            "release_candidate": "1.0.0rc0",
            "transition_families_enabled": [
                item.value for item in sorted(ENABLED_FAMILIES, key=lambda item: item.value)
            ],
            "transition_families_not_enabled": [
                item.value for item in TransitionFamily if item not in ENABLED_FAMILIES
            ],
        }
        _cli._emit(payload, json_mode=bool(parsed.json_mode))
        return _cli.EXIT_PASS
    return _cli.main(resolved)


if __name__ == "__main__":
    raise SystemExit(main())
