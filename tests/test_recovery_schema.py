from __future__ import annotations

import json
from pathlib import Path

from qic.core import JournalPhase


ROOT = Path(__file__).parents[1]


def test_recovery_schema_phase_enum_matches_runtime() -> None:
    schema = json.loads((ROOT / "schemas" / "recovery.schema.json").read_text(encoding="utf-8"))
    declared = schema["$defs"]["journalPhase"]["enum"]
    assert declared == [phase.value for phase in JournalPhase]


def test_recovery_schema_declares_exact_persisted_wire_schemas() -> None:
    schema = json.loads((ROOT / "schemas" / "recovery.schema.json").read_text(encoding="utf-8"))
    journal = schema["$defs"]["journalRecord"]
    bundle = schema["$defs"]["recoveryEvidenceBundle"]
    assert journal["properties"]["schema"]["const"] == "qic.journal.record.v1"
    assert bundle["properties"]["schema"]["const"] == "qic.recovery.evidence_bundle.v1"
    assert journal["additionalProperties"] is False
    assert bundle["additionalProperties"] is False
