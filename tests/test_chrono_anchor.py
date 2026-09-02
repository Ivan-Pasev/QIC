from qic.core.chrono import ChronoChain, ChronoEvent, ChronoEventType, WitnessRecord, WitnessSubject


def _event(sequence: int, previous: str | None, before: str, after: str) -> ChronoEvent:
    if sequence == 0:
        return ChronoEvent(
            sequence=0,
            previous_event_digest=None,
            event_type=ChronoEventType.GENESIS,
            proposal_digest=None,
            outcome_digest=None,
            before_state_digest=before,
            after_state_digest=after,
            accepted=None,
            failure=None,
        )
    return ChronoEvent(
        sequence=sequence,
        previous_event_digest=previous,
        event_type=ChronoEventType.TRANSITION,
        proposal_digest=f"proposal-{sequence}",
        outcome_digest=f"outcome-{sequence}",
        before_state_digest=before,
        after_state_digest=after,
        accepted=True,
        failure=None,
    )


def test_valid_prefix_requires_external_anchor_to_detect_tail_truncation() -> None:
    e0 = _event(0, None, "state-0", "state-0")
    w0 = WitnessRecord(0, None, e0.digest, WitnessSubject.GENESIS_STATE, "state-0")
    e1 = _event(1, e0.digest, "state-0", "state-1")
    w1 = WitnessRecord(1, w0.digest, e1.digest, WitnessSubject.TRANSITION_OUTCOME, "outcome-1")
    e2 = _event(2, e1.digest, "state-1", "state-2")
    w2 = WitnessRecord(2, w1.digest, e2.digest, WitnessSubject.TRANSITION_OUTCOME, "outcome-2")

    full = ChronoChain(events=(e0, e1, e2), witnesses=(w0, w1, w2))
    prefix = ChronoChain(events=(e0, e1), witnesses=(w0, w1))

    assert full.verify() == (True, None)
    # A retained prefix is internally valid; linkage alone cannot prove recency/completeness.
    assert prefix.verify() == (True, None)
    assert prefix.verify(expected_length=3) == (False, "CHAIN_LENGTH_MISMATCH")
    assert prefix.verify(expected_head_event_digest=e2.digest) == (False, "HEAD_EVENT_DIGEST_MISMATCH")
    assert prefix.verify(expected_head_witness_digest=w2.digest) == (False, "HEAD_WITNESS_DIGEST_MISMATCH")
