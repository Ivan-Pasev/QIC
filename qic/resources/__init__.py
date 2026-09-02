"""Packaged release resources for QIC.

These files mirror the public root manifest/claim boundary and runtime registries
so installed wheels/sdists can execute structural verification without relying
on a repository checkout layout.
"""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any


def resource_root() -> Path:
    return Path(str(files(__package__)))


def resource_text(name: str) -> str:
    return files(__package__).joinpath(name).read_text(encoding="utf-8")


def resource_json(name: str) -> Any:
    return json.loads(resource_text(name))
