#!/usr/bin/env python3
"""Validate and create a deterministic .miniapp zip archive."""

from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

from validate_app import MAX_ARCHIVE, validate


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
    errors = [item for item in findings if item.level == "error"]
    if errors:
        for item in errors:
            print(f"ERROR: {item.message}")
        print("Refusing to package an invalid app.")
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
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

    size = output.stat().st_size
    if size > MAX_ARCHIVE:
        output.unlink()
        print(f"Archive would exceed 50 MB ({size} bytes).")
        return 1
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(output)
    print(f"size={size}")
    print(f"sha256={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
