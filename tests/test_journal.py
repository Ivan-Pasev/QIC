from __future__ import annotations

import pytest

from qic.core.journal import JournalPhase, JournalRecord, journal_phase_successors


def prepared() -> JournalRecord:
    return JournalRecord(
        transaction_id="tx-001",
        sequence=0,
        phase=JournalPhase.PREPARED,
        proposal_digest="proposal-001",
        actor="worker",
        grant_digest="grant-001",
        before_state_digest="state-before",
    )


def test_happy_path_is_hash_linked_and_requires_persistence_references() -> None:
    p0 = prepared()
    p1 = p0.successor(JournalPhase.VALIDATED)
    p2 = p1.successor(
        JournalPhase.STATE_COMMITTED,
        after_state_digest="state-after",
        outcome_digest="outcome-001",
    )
    p3 = p2.successor(JournalPhase.CHRONO_COMMITTED, chrono_event_digest="chrono-001")
    p4 = p3.successor(JournalPhase.WITNESS_COMMITTED, witness_digest="witness-001")
    p5 = p4.successor(JournalPhase.COMPLETE)

    records = (p0, p1, p2, p3, p4, p5)
    assert [record.sequence for record in records] == list(range(6))
    assert p0.previous_record_digest is None
    for previous, current in zip(records, records[1:]):
        assert current.previous_record_digest == previous.digest
    assert p5.terminal is True


def test_abort_and_quarantine_are_terminal_and_require_reason() -> None:
    aborted = prepared().successor(JournalPhase.ABORTED, reason="validation rejected")
    quarantined = prepared().successor(JournalPhase.QUARANTINED, reason="corrupt durable set")
    assert aborted.terminal and quarantined.terminal
    with pytest.raises(ValueError):
        prepared().successor(JournalPhase.ABORTED)
    with pytest.raises(ValueError):
        aborted.successor(JournalPhase.COMPLETE)


def test_illegal_phase_skips_fail_closed() -> None:
    p0 = prepared()
    for illegal in (
        JournalPhase.STATE_COMMITTED,
        JournalPhase.CHRONO_COMMITTED,
        JournalPhase.WITNESS_COMMITTED,
        JournalPhase.COMPLETE,
    ):
        with pytest.raises(ValueError):
            p0.successor(illegal)


def test_state_chrono_and_witness_boundaries_require_exact_references() -> None:
    validated = prepared().successor(JournalPhase.VALIDATED)
    with pytest.raises(ValueError):
        validated.successor(JournalPhase.STATE_COMMITTED)

    state = validated.successor(
        JournalPhase.STATE_COMMITTED,
        after_state_digest="state-after",
        outcome_digest="outcome-001",
    )
    with pytest.raises(ValueError):
        state.successor(JournalPhase.CHRONO_COMMITTED)

    chrono = state.successor(JournalPhase.CHRONO_COMMITTED, chrono_event_digest="chrono-001")
    with pytest.raises(ValueError):
        chrono.successor(JournalPhase.WITNESS_COMMITTED)


def test_successor_cannot_rebind_transaction_or_chain_identity() -> None:
    record = prepared()
    for field, value in (
        ("transaction_id", "tx-other"),
        ("sequence", 99),
        ("phase", JournalPhase.COMPLETE),
        ("previous_record_digest", "forged"),
    ):
        with pytest.raises(ValueError):
            record.successor(JournalPhase.VALIDATED, **{field: value})


def test_phase_graph_is_explicit_and_terminal_phases_have_no_successors() -> None:
    assert journal_phase_successors(JournalPhase.PREPARED) == frozenset(
        {JournalPhase.VALIDATED, JournalPhase.ABORTED, JournalPhase.QUARANTINED}
    )
    for phase in (JournalPhase.COMPLETE, JournalPhase.ABORTED, JournalPhase.QUARANTINED):
        assert journal_phase_successors(phase) == frozenset()


def test_digest_is_deterministic_and_phase_sensitive() -> None:
    first = prepared()
    second = prepared()
    validated = first.successor(JournalPhase.VALIDATED)
    assert first.digest == second.digest
    assert validated.digest != first.digest
