"""RC0 installed-artifact entry point.

The qualified G7/G8 runtime historically resolves public registries and claim
metadata relative to a repository checkout. RC0 redirects those read-only roots
to package resources so wheel/sdist installs verify outside a source tree.
"""

from __future__ import annotations

import sys

from . import cli as _cli
from . import qualification as _qualification
from .core.transition import ENABLED_FAMILIES, TransitionFamily
from .resources import resource_root


# Read-only root redirection only. No authority, transition, KBI, Chrono, or
# qualification semantics are changed by this release wrapper.
_cli._root = resource_root
_qualification._root = resource_root


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
