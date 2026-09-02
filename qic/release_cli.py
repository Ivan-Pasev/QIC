"""RC0 installed-artifact entry point.

The qualified G7/G8 runtime historically resolves public registries and claim
metadata relative to a repository checkout. RC0 redirects those read-only roots
to package resources so wheel/sdist installs verify outside a source tree.
"""

from __future__ import annotations

from . import cli as _cli
from . import qualification as _qualification
from .resources import resource_root


# Read-only root redirection only. No authority, transition, KBI, Chrono, or
# qualification semantics are changed by this release wrapper.
_cli._root = resource_root
_qualification._root = resource_root

main = _cli.main


if __name__ == "__main__":
    raise SystemExit(main())
