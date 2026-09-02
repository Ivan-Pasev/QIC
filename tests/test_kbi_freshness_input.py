import pytest

from qic.core.authority import AuthorityDomain, AuthorityGrant
from qic.core.kbi import ClaimRecord, KBIContext, KBIExecutor


def test_explicit_empty_expected_state_digest_does_not_fall_back_to_live_state() -> None:
    context = KBIContext.genesis()
    grant = AuthorityGrant(
        grant_id="grant-kbi",
        subject="curator",
        issuer="qic.root",
        domains=frozenset({AuthorityDomain.EPISTEMIC}),
        capabilities=frozenset({"kbi.claim.assert"}),
        resources=frozenset({"state.kbi"}),
    )
    claim = ClaimRecord(
        claim_id="claim-a",
        statement="statement for claim-a",
        origin_source_id="source.origin",
    )

    with pytest.raises(ValueError, match="expected_state_digest"):
        KBIExecutor().assert_claim(
            context,
            claim,
            actor="curator",
            grant=grant,
            proposal_id="explicit-empty-freshness",
            expected_state_digest="",
        )

    assert context.kbi.claim("claim-a") is None
    assert len(context.chrono.events) == 1
