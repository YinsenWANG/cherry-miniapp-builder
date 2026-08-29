#!/usr/bin/env python3
"""Validate and create a deterministic .miniapp zip archive."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from validate_app import MAX_ARCHIVE, validate


INSTALL_STEPS = (
    "1. Copy the absolute archive path printed above.",
    "2. Locate the archive in your file manager.",
    "3. In Cherry Studio, choose Mini Apps → + → Package → Choose file → review permissions → Install.",
)


def print_install_steps() -> None:
    print("Manual install:")
    for step in INSTALL_STEPS:
        print(step)


def handoff_archive(archive: Path, *, platform: str = sys.platform, runner=subprocess.run) -> None:
    """Best-effort macOS handoff; packaging success never depends on these helpers."""
    if platform != "darwin":
        print("HANDOFF: unsupported on this platform; use the manual steps above.")
        return
    actions = (
        ("copied archive path to clipboard", ["pbcopy"], {"input": str(archive), "text": True}),
        ("revealed archive in Finder", ["open", "-R", str(archive)], {}),
        ("opened the Cherry Studio Mini Apps list", ["open", "cherrystudio://navigate/app/mini-app/"], {}),
    )
    for success, command, options in actions:
        try:
            runner(command, check=True, **options)
        except (OSError, subprocess.CalledProcessError) as error:
            print(f"HANDOFF FAILED: {success}: {error}")
        else:
            print(f"HANDOFF OK: {success}")


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


def main(argv: list[str] | None = None, *, runner=subprocess.run, platform: str = sys.platform) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--handoff", action="store_true", help="On macOS, copy and reveal the archive and open the Mini Apps list")
    args = parser.parse_args(argv)
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
    print_install_steps()
    if args.handoff:
        handoff_archive(output, platform=platform, runner=runner)
    return 0


if __name__ == "__main__":
    sys.exit(main())
