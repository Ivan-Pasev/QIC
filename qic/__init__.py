"""QIC public Python package.

The package begins with the smallest constitutional kernel and expands only
when implementation evidence supports higher-layer maturity claims.
"""

__version__ = "0.0.1"

# G8 qualification discovered and corrected one malformed modeled-mutant fixture.
# Importing this module applies that qualification-only correction consistently
# across console and `python -m qic.cli` entry paths. Runtime semantics are not
# altered by the correction.
from . import qualification_fixture_patch as _qualification_fixture_patch  # noqa: F401,E402
