import json
from pathlib import Path

from qic.core.kbi import (
    ClaimRecord,
    EvidenceBinding,
    EvidenceClass,
    EvidenceRecord,
    EvidenceRelation,
    KBIState,
)


def test_kbi_golden_vector() -> None:
    payload = json.loads((Path(__file__).parent / "vectors" / "kbi_v1.json").read_text(encoding="utf-8"))
    claim = ClaimRecord(
        claim_id="claim-a",
        statement="statement for claim-a",
        origin_source_id="source.origin",
    )
    evidence = EvidenceRecord(
        evidence_id="e1",
        evidence_class=EvidenceClass.OBSERVED,
        source_id="source.a",
        artifact_digest="artifact-e1",
    )
    binding = EvidenceBinding(
        binding_id="bind-e1",
        claim_id="claim-a",
        evidence_id="e1",
        relation=EvidenceRelation.SUPPORTS,
    )
    state = KBIState(claims=(claim,), evidence=(evidence,), bindings=(binding,))
    assert claim.digest == payload["claim_digest"]
    assert evidence.digest == payload["evidence_digest"]
    assert binding.digest == payload["binding_digest"]
    assert state.digest == payload["state_digest"]
