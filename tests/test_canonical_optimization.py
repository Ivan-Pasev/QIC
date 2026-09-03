from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum

import pytest

from qic.core.canonical import (
    CanonicalizationError,
    _canonical_bytes_reference,
    canonical_bytes,
)


class Color(Enum):
    RED = "red"
    BLUE = "blue"


class Number(IntEnum):
    ONE = 1
    TWO = 2


@dataclass(frozen=True)
class Record:
    zeta: int
    alpha: str
    nested: tuple[int, str]


VALID_VALUES = (
    None,
    True,
    False,
    0,
    1,
    -1,
    2**63,
    -(2**63),
    "",
    "ascii",
    "quote\"slash\\newline\n",
    "Ω / България / 日本語 / 🚀",
    b"",
    b"\x00\xff\x10",
    Color.RED,
    Number.TWO,
    (),
    (1, 2, 3),
    [],
    [1, "two", None, False],
    set(),
    {3, 1, 2},
    frozenset({"z", "a", "m"}),
    {},
    {"z": 1, "a": 2},
    {"nested": [1, (2, 3), {"x": True}]},
    Record(zeta=7, alpha="x", nested=(8, "y")),
)


@pytest.mark.parametrize("value", VALID_VALUES)
def test_direct_encoder_matches_frozen_g1_reference(value: object) -> None:
    assert canonical_bytes(value) == _canonical_bytes_reference(value)


def _generated_values() -> list[object]:
    leaves: list[object] = [None, False, True, -7, 0, 19, "a", "Ω", b"x"]
    values: list[object] = list(leaves)
    for left in leaves:
        for right in leaves:
            values.append((left, right))
            values.append([left, right])
            values.append({"a": left, "b": right})
    # Add deeper combinations without relying on randomized test order.
    shallow = values[:60]
    for index, item in enumerate(shallow):
        values.append((index, item, {"payload": item}))
    return values


def test_generated_nested_corpus_matches_reference_exactly() -> None:
    values = _generated_values()
    assert len(values) >= 200
    for value in values:
        assert canonical_bytes(value) == _canonical_bytes_reference(value)


@pytest.mark.parametrize(
    "value",
    (
        1.25,
        {1: "not-a-string-key"},
        object(),
        complex(1, 2),
    ),
)
def test_direct_encoder_preserves_fail_closed_behavior(value: object) -> None:
    with pytest.raises(CanonicalizationError) as direct:
        canonical_bytes(value)
    with pytest.raises(CanonicalizationError) as reference:
        _canonical_bytes_reference(value)
    assert str(direct.value) == str(reference.value)


def test_set_sorting_matches_reference_for_nested_hashable_values() -> None:
    value = frozenset({(2, "b"), (1, "z"), (1, "a")})
    assert canonical_bytes(value) == _canonical_bytes_reference(value)


def test_large_measured_hot_path_is_byte_identical() -> None:
    value = tuple(range(1000))
    assert canonical_bytes(value) == _canonical_bytes_reference(value)
