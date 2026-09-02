"""Local durable journal persistence and crash-recovery classification for QIC G9.

This module persists only immutable :class:`JournalRecord` objects. It does not
replay authority, execute transitions, synthesize state, append Chrono events,
or create witnesses. Recovery classification is descriptive: callers must
supply and separately verify any authoritative artifacts required to continue.

The reference store uses unique same-directory temp write -> flush/fsync ->
atomic no-replace hard-link promotion -> temp unlink -> directory fsync. This is
a local-filesystem durability policy, not a claim about every filesystem,
storage controller, VM, network filesystem, or power-failure mode.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

from .journal import JournalPhase, JournalRecord


class JournalStoreError(RuntimeError):
    """Base error for durable journal operations."""


class JournalCorruptionError(JournalStoreError):
    """Raised when persisted journal bytes do not form the declared record chain."""


class JournalConflictError(JournalStoreError):
    """Raised when append expectations disagree with durable state."""


class JournalFailpoint(str, Enum):
    AFTER_TEMP_WRITE = "AFTER_TEMP_WRITE"
    AFTER_FILE_FSYNC = "AFTER_FILE_FSYNC"
    AFTER_PROMOTE = "AFTER_PROMOTE"


class RecoveryClass(str, Enum):
    RESUME_VALIDATION = "RESUME_VALIDATION"
    RESUME_STATE_COMMIT = "RESUME_STATE_COMMIT"
    REQUIRE_CHRONO_EVIDENCE = "REQUIRE_CHRONO_EVIDENCE"
    REQUIRE_WITNESS_EVIDENCE = "REQUIRE_WITNESS_EVIDENCE"
    FINALIZE_COMPLETE = "FINALIZE_COMPLETE"
    COMPLETE = "COMPLETE"
    ABORTED = "ABORTED"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True, slots=True)
class RecoveryAssessment:
    transaction_id: str
    classification: RecoveryClass
    last_phase: JournalPhase
    last_record_digest: str
    required_references: tuple[str, ...] = ()


def _record_payload(record: JournalRecord) -> dict[str, object]:
    return {
        "schema": "qic.journal.record.v1",
        "transaction_id": record.transaction_id,
        "sequence": record.sequence,
        "phase": record.phase.value,
        "proposal_digest": record.proposal_digest,
        "actor": record.actor,
        "grant_digest": record.grant_digest,
        "before_state_digest": record.before_state_digest,
        "after_state_digest": record.after_state_digest,
        "outcome_digest": record.outcome_digest,
        "chrono_event_digest": record.chrono_event_digest,
        "witness_digest": record.witness_digest,
        "previous_record_digest": record.previous_record_digest,
        "reason": record.reason,
        "record_digest": record.digest,
    }


def _record_from_payload(payload: object) -> JournalRecord:
    if type(payload) is not dict:
        raise JournalCorruptionError("journal record payload must be an object")
    row = payload
    if row.get("schema") != "qic.journal.record.v1":
        raise JournalCorruptionError("unsupported journal record schema")
    try:
        record = JournalRecord(
            transaction_id=row["transaction_id"],
            sequence=row["sequence"],
            phase=JournalPhase(row["phase"]),
            proposal_digest=row["proposal_digest"],
            actor=row["actor"],
            grant_digest=row["grant_digest"],
            before_state_digest=row["before_state_digest"],
            after_state_digest=row.get("after_state_digest"),
            outcome_digest=row.get("outcome_digest"),
            chrono_event_digest=row.get("chrono_event_digest"),
            witness_digest=row.get("witness_digest"),
            previous_record_digest=row.get("previous_record_digest"),
            reason=row.get("reason"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise JournalCorruptionError(f"invalid journal record: {exc}") from exc
    if row.get("record_digest") != record.digest:
        raise JournalCorruptionError("journal record digest mismatch")
    return record


def _encoded_record(record: JournalRecord) -> bytes:
    return (
        json.dumps(
            _record_payload(record),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _unique_temp_path(target: Path) -> Path:
    return target.parent / f".{target.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}"


def _promote_no_replace(temporary: Path, target: Path) -> None:
    """Atomically publish *temporary* without replacing an existing target."""

    os.link(temporary, target)
    temporary.unlink()


def _read_record_path(path: Path, *, context: str) -> JournalRecord:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise JournalCorruptionError(f"cannot decode {context}: {exc}") from exc
    return _record_from_payload(payload)


class JournalFileStore:
    """Reference local-filesystem store for immutable per-transaction journals."""

    def __init__(
        self,
        root: str | os.PathLike[str],
        *,
        failpoint: Callable[[JournalFailpoint, Path], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self._failpoint = failpoint
        self.root.mkdir(parents=True, exist_ok=True)
        _fsync_directory(self.root)

    def _trip(self, point: JournalFailpoint, path: Path) -> None:
        if self._failpoint is not None:
            self._failpoint(point, path)

    def _transaction_dir(self, transaction_id: str) -> Path:
        if not transaction_id or transaction_id in {".", ".."}:
            raise ValueError("invalid transaction_id")
        if any(token in transaction_id for token in ("/", "\\", "\x00")):
            raise ValueError("transaction_id is not filesystem-safe")
        return self.root / transaction_id

    def _record_path(self, record: JournalRecord) -> Path:
        return self._transaction_dir(record.transaction_id) / f"{record.sequence:08d}.json"

    def append(self, record: JournalRecord) -> Path:
        if not isinstance(record, JournalRecord):
            raise TypeError("record must be JournalRecord")
        directory = self._transaction_dir(record.transaction_id)
        directory.mkdir(parents=True, exist_ok=True)
        _fsync_directory(self.root)

        target = self._record_path(record)
        if target.exists():
            durable = _read_record_path(target, context="durable retry target")
            if durable == record:
                return target
            raise JournalConflictError("journal sequence already exists with different content")

        existing = self.load(record.transaction_id)
        if not existing:
            if record.sequence != 0 or record.phase is not JournalPhase.PREPARED:
                raise JournalConflictError("new durable journal must begin with PREPARED sequence 0")
        else:
            previous = existing[-1]
            if previous.terminal:
                raise JournalConflictError("cannot append after terminal durable journal phase")
            if record.sequence != previous.sequence + 1:
                raise JournalConflictError("journal sequence is not the next durable sequence")
            if record.previous_record_digest != previous.digest:
                raise JournalConflictError("journal previous_record_digest does not match durable head")
            if not previous.may_advance_to(record.phase):
                raise JournalConflictError("illegal durable journal phase transition")

        temporary = _unique_temp_path(target)
        data = _encoded_record(record)
        try:
            with temporary.open("xb") as handle:
                handle.write(data)
                handle.flush()
                self._trip(JournalFailpoint.AFTER_TEMP_WRITE, temporary)
                os.fsync(handle.fileno())
                self._trip(JournalFailpoint.AFTER_FILE_FSYNC, temporary)
            try:
                _promote_no_replace(temporary, target)
            except FileExistsError:
                durable = _read_record_path(target, context="concurrent durable target")
                if durable == record:
                    temporary.unlink(missing_ok=True)
                    return target
                raise JournalConflictError(
                    "concurrent journal promotion created different content"
                )
            self._trip(JournalFailpoint.AFTER_PROMOTE, target)
            _fsync_directory(directory)
        except BaseException:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        return target

    def load(self, transaction_id: str) -> tuple[JournalRecord, ...]:
        directory = self._transaction_dir(transaction_id)
        if not directory.exists():
            return ()
        if not directory.is_dir():
            raise JournalCorruptionError("transaction journal path is not a directory")
        paths = sorted(directory.glob("*.json"))
        records: list[JournalRecord] = []
        for expected_sequence, path in enumerate(paths):
            record = _read_record_path(path, context=f"journal record {path.name}")
            if record.transaction_id != transaction_id:
                raise JournalCorruptionError("journal record transaction_id mismatch")
            if record.sequence != expected_sequence:
                raise JournalCorruptionError("journal sequence gap or duplicate")
            if records:
                previous = records[-1]
                if record.previous_record_digest != previous.digest:
                    raise JournalCorruptionError("journal hash link mismatch")
                if not previous.may_advance_to(record.phase):
                    raise JournalCorruptionError("illegal persisted journal phase transition")
            records.append(record)
        return tuple(records)

    def scan(self) -> dict[str, tuple[JournalRecord, ...] | JournalCorruptionError]:
        result: dict[str, tuple[JournalRecord, ...] | JournalCorruptionError] = {}
        for path in sorted(self.root.iterdir(), key=lambda item: item.name):
            if not path.is_dir():
                continue
            try:
                result[path.name] = self.load(path.name)
            except JournalCorruptionError as exc:
                result[path.name] = exc
        return result


def assess_recovery(records: tuple[JournalRecord, ...]) -> RecoveryAssessment:
    """Classify a verified journal head without executing any recovery side effect."""

    if not records:
        raise ValueError("recovery assessment requires at least one journal record")
    transaction_id = records[0].transaction_id
    for index, record in enumerate(records):
        if record.transaction_id != transaction_id or record.sequence != index:
            raise JournalCorruptionError("records are not one contiguous transaction journal")
        if index == 0:
            if record.phase is not JournalPhase.PREPARED or record.previous_record_digest is not None:
                raise JournalCorruptionError("invalid recovery journal genesis")
        else:
            previous = records[index - 1]
            if record.previous_record_digest != previous.digest:
                raise JournalCorruptionError("recovery journal hash link mismatch")
            if not previous.may_advance_to(record.phase):
                raise JournalCorruptionError("illegal recovery journal phase transition")

    head = records[-1]
    mapping: dict[JournalPhase, tuple[RecoveryClass, tuple[str, ...]]] = {
        JournalPhase.PREPARED: (RecoveryClass.RESUME_VALIDATION, ()),
        JournalPhase.VALIDATED: (RecoveryClass.RESUME_STATE_COMMIT, ("authoritative_transition_result",)),
        JournalPhase.STATE_COMMITTED: (RecoveryClass.REQUIRE_CHRONO_EVIDENCE, ("chrono_event",)),
        JournalPhase.CHRONO_COMMITTED: (RecoveryClass.REQUIRE_WITNESS_EVIDENCE, ("witness",)),
        JournalPhase.WITNESS_COMMITTED: (RecoveryClass.FINALIZE_COMPLETE, ()),
        JournalPhase.COMPLETE: (RecoveryClass.COMPLETE, ()),
        JournalPhase.ABORTED: (RecoveryClass.ABORTED, ()),
        JournalPhase.QUARANTINED: (RecoveryClass.QUARANTINED, ()),
    }
    classification, required = mapping[head.phase]
    return RecoveryAssessment(
        transaction_id=transaction_id,
        classification=classification,
        last_phase=head.phase,
        last_record_digest=head.digest,
        required_references=required,
    )
