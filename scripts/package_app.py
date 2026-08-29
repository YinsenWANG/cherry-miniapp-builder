#!/usr/bin/env python3
"""Validate and create a deterministic .miniapp zip archive."""

from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
import zipfile
from pathlib import Path

from validate_app import MAX_ARCHIVE, validate


def package_archive(root: Path, output: Path, max_archive: int = MAX_ARCHIVE) -> tuple[int, str]:
    """Create a deterministic archive, replacing output only after all checks pass."""
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent, delete=False) as handle:
            temporary = Path(handle.name)
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(root.rglob("*")):
                if not path.is_file() or path.is_symlink():
                    continue
                relative = path.relative_to(root)
                if any(part.startswith(".") for part in relative.parts) or path.suffix == ".miniapp":
                    continue
                info = zipfile.ZipInfo(relative.as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes())
        size = temporary.stat().st_size
        if size > max_archive:
            raise ValueError(f"Archive would exceed 50 MB ({size} bytes).")
        digest = hashlib.sha256(temporary.read_bytes()).hexdigest()
        temporary.replace(output)
        temporary = None
        return size, digest
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.app.resolve()
    output = (args.output or root.with_suffix(".miniapp")).resolve()
    try:
        output.relative_to(root)
    except ValueError:
        pass
    else:
        parser.error("output archive must be outside the app directory")

    findings = validate(root)
    for item in findings:
        if item.level == "warning":
            print(f"WARNING: {item.message}")
    errors = [item for item in findings if item.level == "error"]
    if errors:
        for item in errors:
            print(f"ERROR: {item.message}")
        print("Refusing to package an invalid app.")
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        size, digest = package_archive(root, output)
    except ValueError as error:
        print(error)
        return 1
    print(output)
    print(f"size={size}")
    print(f"sha256={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
