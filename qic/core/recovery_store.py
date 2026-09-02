"""Immutable recovery evidence-bundle persistence for QIC G9.

A :class:`RecoveryEvidenceBundle` is a receipt envelope over digests of artifacts
that were loaded and verified by higher-level code. Persisting this envelope does
not make those artifacts authoritative and does not execute a recovery action.

Bundles are immutable and bound to one journal sequence/head digest. Repeating
an identical write is idempotent; a different bundle for an existing sequence
is a conflict and is never overwritten.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from .digest import digest_hex
from .journal import JournalRecord
from .journal_store import (
    JournalConflictError,
    JournalCorruptionError,
    _fsync_directory,
    _promote_no_replace,
    _unique_temp_path,
)
from .recovery import (
    DurableArtifactView,
    ReconciliationResult,
    reconcile_recovery,
)


def _text(value: object, *, name: str) -> str:
    if type(value) is not str or not value or "\x00" in value:
        raise ValueError(f"{name} must be a non-empty NUL-free string")
    return value


@dataclass(frozen=True, slots=True)
class RecoveryEvidenceBundle:
    """Immutable digest receipt bound to one durable journal head."""

    transaction_id: str
    journal_sequence: int
    journal_head_digest: str
    state_digest: str
    outcome_digest: str | None = None
    chrono_event_digest: str | None = None
    witness_digest: str | None = None

    def __post_init__(self) -> None:
        _text(self.transaction_id, name="transaction_id")
        if type(self.journal_sequence) is not int or self.journal_sequence < 0:
            raise ValueError("journal_sequence must be a non-negative int")
        for name, value in (
            ("journal_head_digest", self.journal_head_digest),
            ("state_digest", self.state_digest),
        ):
            _text(value, name=name)
        for name, value in (
            ("outcome_digest", self.outcome_digest),
            ("chrono_event_digest", self.chrono_event_digest),
            ("witness_digest", self.witness_digest),
        ):
            if value is not None:
                _text(value, name=name)

    @property
    def digest(self) -> str:
        return digest_hex(self, domain="recovery.evidence.bundle")

    @property
    def artifact_view(self) -> DurableArtifactView:
        return DurableArtifactView(
            state_digest=self.state_digest,
            outcome_digest=self.outcome_digest,
            chrono_event_digest=self.chrono_event_digest,
            witness_digest=self.witness_digest,
        )


def reconcile_evidence_bundle(
    records: tuple[JournalRecord, ...],
    bundle: RecoveryEvidenceBundle,
) -> ReconciliationResult:
    """Require exact journal binding before using a persisted evidence bundle."""

    if not records:
        raise ValueError("reconciliation requires at least one journal record")
    if not isinstance(bundle, RecoveryEvidenceBundle):
        raise TypeError("bundle must be RecoveryEvidenceBundle")
    head = records[-1]
    if bundle.transaction_id != head.transaction_id:
        raise JournalCorruptionError("recovery evidence transaction_id does not match journal")
    if bundle.journal_sequence != head.sequence:
        raise JournalCorruptionError("recovery evidence sequence does not match journal head")
    if bundle.journal_head_digest != head.digest:
        raise JournalCorruptionError("recovery evidence head digest does not match journal head")
    return reconcile_recovery(records, bundle.artifact_view)


def _payload(bundle: RecoveryEvidenceBundle) -> dict[str, object]:
    return {
        "schema": "qic.recovery.evidence_bundle.v1",
        "transaction_id": bundle.transaction_id,
        "journal_sequence": bundle.journal_sequence,
        "journal_head_digest": bundle.journal_head_digest,
        "state_digest": bundle.state_digest,
        "outcome_digest": bundle.outcome_digest,
        "chrono_event_digest": bundle.chrono_event_digest,
        "witness_digest": bundle.witness_digest,
        "bundle_digest": bundle.digest,
    }


def _decode(payload: object) -> RecoveryEvidenceBundle:
    if type(payload) is not dict:
        raise JournalCorruptionError("recovery evidence bundle must be an object")
    row = payload
    if row.get("schema") != "qic.recovery.evidence_bundle.v1":
        raise JournalCorruptionError("unsupported recovery evidence bundle schema")
    try:
        bundle = RecoveryEvidenceBundle(
            transaction_id=row["transaction_id"],
            journal_sequence=row["journal_sequence"],
            journal_head_digest=row["journal_head_digest"],
            state_digest=row["state_digest"],
            outcome_digest=row.get("outcome_digest"),
            chrono_event_digest=row.get("chrono_event_digest"),
            witness_digest=row.get("witness_digest"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise JournalCorruptionError(f"invalid recovery evidence bundle: {exc}") from exc
    if row.get("bundle_digest") != bundle.digest:
        raise JournalCorruptionError("recovery evidence bundle digest mismatch")
    return bundle


def _encoded(bundle: RecoveryEvidenceBundle) -> bytes:
    return (
        json.dumps(
            _payload(bundle),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


class RecoveryEvidenceStore:
    """Immutable local store for journal-bound recovery evidence bundles."""

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        _fsync_directory(self.root)

    def _transaction_dir(self, transaction_id: str) -> Path:
        _text(transaction_id, name="transaction_id")
        if transaction_id in {".", ".."} or any(
            token in transaction_id for token in ("/", "\\", "\x00")
        ):
            raise ValueError("transaction_id is not filesystem-safe")
        return self.root / transaction_id

    def _path(self, transaction_id: str, journal_sequence: int) -> Path:
        if type(journal_sequence) is not int or journal_sequence < 0:
            raise ValueError("journal_sequence must be a non-negative int")
        return self._transaction_dir(transaction_id) / f"{journal_sequence:08d}.json"

    def put(self, bundle: RecoveryEvidenceBundle) -> Path:
        if not isinstance(bundle, RecoveryEvidenceBundle):
            raise TypeError("bundle must be RecoveryEvidenceBundle")
        directory = self._transaction_dir(bundle.transaction_id)
        directory.mkdir(parents=True, exist_ok=True)
        _fsync_directory(self.root)
        target = self._path(bundle.transaction_id, bundle.journal_sequence)

        if target.exists():
            durable = self.load(bundle.transaction_id, bundle.journal_sequence)
            if durable == bundle:
                return target
            raise JournalConflictError(
                "recovery evidence already exists for journal sequence with different content"
            )

        temporary = _unique_temp_path(target)
        try:
            with temporary.open("xb") as handle:
                handle.write(_encoded(bundle))
                handle.flush()
                os.fsync(handle.fileno())
            try:
                _promote_no_replace(temporary, target)
            except FileExistsError:
                durable = self.load(bundle.transaction_id, bundle.journal_sequence)
                if durable == bundle:
                    temporary.unlink(missing_ok=True)
                    return target
                raise JournalConflictError(
                    "concurrent recovery evidence promotion created different content"
                )
            _fsync_directory(directory)
        except BaseException:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        return target

    def load(self, transaction_id: str, journal_sequence: int) -> RecoveryEvidenceBundle:
        path = self._path(transaction_id, journal_sequence)
        if not path.exists():
            raise FileNotFoundError(path)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise JournalCorruptionError(
                f"cannot decode recovery evidence bundle {path.name}: {exc}"
            ) from exc
        bundle = _decode(payload)
        if bundle.transaction_id != transaction_id or bundle.journal_sequence != journal_sequence:
            raise JournalCorruptionError("recovery evidence bundle path identity mismatch")
        return bundle

    def bundles(self, transaction_id: str) -> tuple[RecoveryEvidenceBundle, ...]:
        directory = self._transaction_dir(transaction_id)
        if not directory.exists():
            return ()
        result: list[RecoveryEvidenceBundle] = []
        for path in sorted(directory.glob("*.json")):
            try:
                sequence = int(path.stem)
            except ValueError as exc:
                raise JournalCorruptionError("invalid recovery evidence filename") from exc
            result.append(self.load(transaction_id, sequence))
        return tuple(result)
