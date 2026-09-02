from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import pytest

from qic.core import (
    CanonicalizationError,
    DigestDomainError,
    canonical_text,
    digest_hex,
)


class ExampleEnum(Enum):
    ALPHA = 1


@dataclass(frozen=True)
class ExampleRecord:
    name: str
    count: int


VECTOR_INPUTS = {
    "null": None,
    "bool_true": True,
    "int_42": 42,
    "string_qic": "QIC",
    "nested_mapping": {"b": 2, "a": [1, True, None]},
    "unordered_set": {"beta", "alpha"},
    "typed_tuple": (1, "x"),
}


def test_golden_vectors() -> None:
    vector_path = Path(__file__).parent / "vectors" / "canonical_v1.json"
    payload = json.loads(vector_path.read_text(encoding="utf-8"))
    domain = payload["digest_domain"]

    for vector in payload["vectors"]:
        value = VECTOR_INPUTS[vector["input_kind"]]
        assert canonical_text(value) == vector["canonical"]
        assert digest_hex(value, domain=domain) == vector["sha256"]


def test_mapping_order_does_not_change_bytes() -> None:
    left = {"z": 3, "a": 1, "m": 2}
    right = {"a": 1, "m": 2, "z": 3}
    assert canonical_text(left) == canonical_text(right)


def test_set_iteration_order_does_not_change_bytes() -> None:
    assert canonical_text({"gamma", "alpha", "beta"}) == canonical_text(
        {"beta", "gamma", "alpha"}
    )


def test_sequence_types_remain_distinct() -> None:
    assert canonical_text([1, 2]) != canonical_text((1, 2))


def test_scalar_types_remain_distinct() -> None:
    assert canonical_text(True) != canonical_text(1)
    assert canonical_text("1") != canonical_text(1)


def test_dataclass_and_enum_have_declared_representation() -> None:
    record = ExampleRecord(name="sensor", count=2)
    assert '"$type":"dataclass"' in canonical_text(record)
    assert '"$type":"enum"' in canonical_text(ExampleEnum.ALPHA)


def test_floats_fail_closed() -> None:
    with pytest.raises(CanonicalizationError):
        canonical_text(1.25)


def test_non_string_mapping_keys_fail_closed() -> None:
    with pytest.raises(CanonicalizationError):
        canonical_text({1: "ambiguous"})


def test_unknown_objects_fail_closed() -> None:
    class Unknown:
        pass

    with pytest.raises(CanonicalizationError):
        canonical_text(Unknown())


def test_digest_is_domain_separated() -> None:
    value = {"claim": "same bytes"}
    assert digest_hex(value, domain="qic.claim") != digest_hex(
        value, domain="qic.witness"
    )


def test_invalid_digest_domains_fail_closed() -> None:
    with pytest.raises(DigestDomainError):
        digest_hex("x", domain="")
    with pytest.raises(DigestDomainError):
        digest_hex("x", domain="bad\x00domain")


def test_repeatability_within_process() -> None:
    value = {
        "name": "Ω-QIC",
        "items": [3, 2, 1],
        "tags": {"formal", "tested", "implemented"},
    }
    outputs = {canonical_text(value) for _ in range(100)}
    digests = {digest_hex(value, domain="qic.repeatability") for _ in range(100)}
    assert len(outputs) == 1
    assert len(digests) == 1
