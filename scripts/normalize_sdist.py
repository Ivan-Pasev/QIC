"""Normalize a QIC .tar.gz source distribution for reproducible RC0 builds.

This script changes archive container metadata only. File bytes, names, modes,
link targets, and tar member types are preserved. Members are sorted by name;
mtime/uid/gid/uname/gname/PAX metadata and gzip mtime are normalized.
"""

from __future__ import annotations

import copy
import gzip
import io
import os
from pathlib import Path
import sys
import tarfile


DEFAULT_EPOCH = 315532800  # 1980-01-01T00:00:00Z; ZIP-compatible minimum.


def normalize_sdist(path: Path, *, epoch: int) -> None:
    file_payloads: dict[str, bytes] = {}
    with tarfile.open(path, "r:gz") as source:
        members = source.getmembers()
        for member in members:
            if member.isfile():
                extracted = source.extractfile(member)
                if extracted is None:
                    raise RuntimeError(f"unable to read sdist member: {member.name}")
                file_payloads[member.name] = extracted.read()

    temporary = path.with_name(path.name + ".normalized")
    with temporary.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=epoch) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as target:
                for member in sorted(members, key=lambda item: item.name):
                    normalized = copy.copy(member)
                    normalized.mtime = epoch
                    normalized.uid = 0
                    normalized.gid = 0
                    normalized.uname = ""
                    normalized.gname = ""
                    normalized.pax_headers = {}
                    if normalized.isfile():
                        target.addfile(normalized, io.BytesIO(file_payloads[normalized.name]))
                    else:
                        target.addfile(normalized)
    temporary.replace(path)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("usage: normalize_sdist.py PATH_TO_TAR_GZ", file=sys.stderr)
        return 2
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", str(DEFAULT_EPOCH)))
    normalize_sdist(Path(args[0]), epoch=epoch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
