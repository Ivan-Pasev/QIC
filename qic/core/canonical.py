"""Deterministic canonical serialization for QIC.

`QIC-CANONICAL/1.0` converts a deliberately small set of Python values into a
stable typed JSON representation, then encodes it as UTF-8 bytes. Unsupported
or ambiguous values fail closed.

Canonical byte identity is a structural property only; it does not grant truth,
authority, provenance, or execution rights.
"""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Final, Mapping


CANONICAL_VERSION: Final[str] = "QIC-CANONICAL/1.0"


class CanonicalizationError(TypeError):
    """Raised when a value has no declared QIC canonical representation."""


def _type_name(value: object) -> str:
    cls = type(value)
    return f"{cls.__module__}.{cls.__qualname__}"


def _normalize(value: Any) -> Any:
    if value is None:
        return {"$type": "null"}

    if isinstance(value, bool):
        return {"$type": "bool", "value": value}

    # bool is an int subclass, so this must follow the bool branch.
    if isinstance(value, int):
        return {"$type": "int", "value": str(value)}

    if isinstance(value, float):
        raise CanonicalizationError(
            "floats are not supported by QIC-CANONICAL/1.0; use an explicit "
            "future numeric policy rather than platform-dependent float text"
        )

    if isinstance(value, str):
        return {"$type": "str", "value": value}

    if isinstance(value, bytes):
        return {"$type": "bytes", "hex": value.hex()}

    if isinstance(value, Enum):
        return {
            "$type": "enum",
            "class": _type_name(value),
            "name": value.name,
            "value": _normalize(value.value),
        }

    if is_dataclass(value) and not isinstance(value, type):
        return {
            "$type": "dataclass",
            "class": _type_name(value),
            "fields": {
                field.name: _normalize(getattr(value, field.name))
                for field in fields(value)
            },
        }

    if isinstance(value, tuple):
        return {"$type": "tuple", "items": [_normalize(item) for item in value]}

    if isinstance(value, list):
        return {"$type": "list", "items": [_normalize(item) for item in value]}

    if isinstance(value, (set, frozenset)):
        normalized_items = [_normalize(item) for item in value]
        normalized_items.sort(key=_encode_normalized)
        return {
            "$type": "frozenset" if isinstance(value, frozenset) else "set",
            "items": normalized_items,
        }

    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise CanonicalizationError(
                "mapping keys must be strings in QIC-CANONICAL/1.0"
            )
        return {
            "$type": "mapping",
            "items": {
                key: _normalize(value[key])
                for key in sorted(value)
            },
        }

    raise CanonicalizationError(
        f"unsupported canonical type: {_type_name(value)}"
    )


def _encode_normalized(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_bytes(value: Any) -> bytes:
    """Return deterministic `QIC-CANONICAL/1.0` UTF-8 bytes for *value*."""

    envelope = {
        "$canonical": CANONICAL_VERSION,
        "value": _normalize(value),
    }
    return _encode_normalized(envelope)


def canonical_text(value: Any) -> str:
    """Return the canonical bytes decoded as UTF-8 text for inspection."""

    return canonical_bytes(value).decode("utf-8")
