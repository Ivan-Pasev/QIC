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
    """Frozen G1 object-tree normalization retained as the G11 reference path."""

    if value is None:
        return {"$type": "null"}

    # Enum must precede scalar subtype checks because IntEnum/StrEnum members
    # are also instances of int/str. QIC preserves their declared enum identity.
    if isinstance(value, Enum):
        return {
            "$type": "enum",
            "class": _type_name(value),
            "name": value.name,
            "value": _normalize(value.value),
        }

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


def _canonical_bytes_reference(value: Any) -> bytes:
    """Frozen pre-G11 implementation used only for differential qualification."""

    envelope = {
        "$canonical": CANONICAL_VERSION,
        "value": _normalize(value),
    }
    return _encode_normalized(envelope)


def _json_string(value: str) -> bytes:
    """Encode one JSON string with the exact G1 escaping policy."""

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _encode_value(value: Any) -> bytes:
    """Emit the G1 normalized JSON bytes directly, avoiding the object tree."""

    if value is None:
        return b'{"$type":"null"}'

    if isinstance(value, Enum):
        return b''.join(
            (
                b'{"$type":"enum","class":',
                _json_string(_type_name(value)),
                b',"name":',
                _json_string(value.name),
                b',"value":',
                _encode_value(value.value),
                b'}',
            )
        )

    if isinstance(value, bool):
        return b'{"$type":"bool","value":true}' if value else b'{"$type":"bool","value":false}'

    if isinstance(value, int):
        # Plain integers dominate the measured G10 hot path. The canonical G1
        # representation stores the decimal form as a JSON string.
        if type(value) is int:
            return b'{"$type":"int","value":"' + str(value).encode("ascii") + b'"}'
        return b'{"$type":"int","value":' + _json_string(str(value)) + b'}'

    if isinstance(value, float):
        raise CanonicalizationError(
            "floats are not supported by QIC-CANONICAL/1.0; use an explicit "
            "future numeric policy rather than platform-dependent float text"
        )

    if isinstance(value, str):
        return b'{"$type":"str","value":' + _json_string(value) + b'}'

    if isinstance(value, bytes):
        return b'{"$type":"bytes","hex":"' + value.hex().encode("ascii") + b'"}'

    if is_dataclass(value) and not isinstance(value, type):
        encoded_fields: list[bytes] = []
        for field in sorted(fields(value), key=lambda item: item.name):
            encoded_fields.append(_json_string(field.name) + b':' + _encode_value(getattr(value, field.name)))
        return b''.join(
            (
                b'{"$type":"dataclass","class":',
                _json_string(_type_name(value)),
                b',"fields":{',
                b','.join(encoded_fields),
                b'}}',
            )
        )

    if isinstance(value, tuple):
        return b'{"$type":"tuple","items":[' + b','.join(_encode_value(item) for item in value) + b']}'

    if isinstance(value, list):
        return b'{"$type":"list","items":[' + b','.join(_encode_value(item) for item in value) + b']}'

    if isinstance(value, (set, frozenset)):
        encoded_items = sorted(_encode_value(item) for item in value)
        kind = b'frozenset' if isinstance(value, frozenset) else b'set'
        return b'{"$type":"' + kind + b'","items":[' + b','.join(encoded_items) + b']}'

    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise CanonicalizationError(
                "mapping keys must be strings in QIC-CANONICAL/1.0"
            )
        encoded_items = [
            _json_string(key) + b':' + _encode_value(value[key])
            for key in sorted(value)
        ]
        return b'{"$type":"mapping","items":{' + b','.join(encoded_items) + b'}}'

    raise CanonicalizationError(
        f"unsupported canonical type: {_type_name(value)}"
    )


def canonical_bytes(value: Any) -> bytes:
    """Return deterministic `QIC-CANONICAL/1.0` UTF-8 bytes for *value*.

    G11 emits the already-declared typed JSON representation directly. The
    frozen `_canonical_bytes_reference` remains available for byte-for-byte
    differential qualification but is not used by the production path.
    """

    return b'{"$canonical":"QIC-CANONICAL/1.0","value":' + _encode_value(value) + b'}'


def canonical_text(value: Any) -> str:
    """Return the canonical bytes decoded as UTF-8 text for inspection."""

    return canonical_bytes(value).decode("utf-8")
