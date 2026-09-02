from __future__ import annotations

from pathlib import Path

import pytest

from qic.core import JournalCorruptionError, JournalFileStore, JournalPhase, JournalRecord


def prepared(transaction_id: str) -> JournalRecord:
    return JournalRecord(
        transaction_id=transaction_id,
        sequence=0,
        phase=JournalPhase.PREPARED,
        proposal_digest="proposal",
        actor="operator",
        grant_digest="grant",
        before_state_digest="before",
    )


def test_torn_json_record_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "journal"
    directory = root / "tx-torn"
    directory.mkdir(parents=True)
    (directory / "00000000.json").write_text('{"schema":"qic.journal.record.v1"', encoding="utf-8")
    with pytest.raises(JournalCorruptionError, match="cannot decode"):
        JournalFileStore(root).load("tx-torn")


def test_cross_transaction_record_in_wrong_directory_fails_closed(tmp_path: Path) -> None:
    staging = JournalFileStore(tmp_path / "staging")
    foreign_path = staging.append(prepared("foreign"))

    root = tmp_path / "journal"
    wrong_dir = root / "local"
    wrong_dir.mkdir(parents=True)
    (wrong_dir / "00000000.json").write_bytes(foreign_path.read_bytes())

    with pytest.raises(JournalCorruptionError, match="transaction_id mismatch"):
        JournalFileStore(root).load("local")


def test_unknown_non_record_json_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "journal"
    directory = root / "tx-unknown"
    directory.mkdir(parents=True)
    (directory / "00000000.json").write_text('{"schema":"unknown"}', encoding="utf-8")
    with pytest.raises(JournalCorruptionError, match="unsupported journal record schema"):
        JournalFileStore(root).load("tx-unknown")
