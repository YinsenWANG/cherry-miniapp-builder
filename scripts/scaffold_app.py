#!/usr/bin/env python3
"""Create a dependency-free Cherry mini-app source tree."""

from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path


TOKENS = {
    "manifest.json.tmpl": "manifest.json",
    "index.html.tmpl": "index.html",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True, dest="app_id")
    parser.add_argument("--name", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    starter = root / "assets" / "starter"
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error(f"output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    replacements = {
        "__APP_ID_JSON__": json.dumps(args.app_id, ensure_ascii=False),
        "__APP_NAME_JSON__": json.dumps(args.name, ensure_ascii=False),
        "__APP_DESCRIPTION_JSON__": json.dumps(args.description, ensure_ascii=False),
        "__APP_NAME_HTML__": html.escape(args.name),
    }
    for source in sorted(starter.iterdir()):
        target = output / TOKENS.get(source.name, source.name)
        if source.suffix == ".tmpl":
            text = source.read_text(encoding="utf-8")
            for token, value in replacements.items():
                text = text.replace(token, value)
            target.write_text(text, encoding="utf-8")
        else:
            shutil.copy2(source, target)

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
