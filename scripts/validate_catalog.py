#!/usr/bin/env python3
"""Validate the domain catalog's uniqueness, schema, and searchability."""

from __future__ import annotations

import collections
from pathlib import Path

from search_templates import load_catalog


REQUIRED = {"id", "category", "title", "audience", "outcome", "flow", "capabilities", "ai", "guardrail", "keywords"}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    items = load_catalog(root)
    errors: list[str] = []
    ids = [item.get("id") for item in items]
    duplicates = [value for value, count in collections.Counter(ids).items() if count > 1]
    if duplicates:
        errors.append(f"duplicate ids: {', '.join(map(str, duplicates))}")
    categories = {item.get("category") for item in items}
    for index, item in enumerate(items, 1):
        missing = REQUIRED - set(item)
        if missing:
            errors.append(f"item {index} missing {sorted(missing)}")
            continue
        if not all(isinstance(item.get(field), str) and item[field].strip() for field in REQUIRED - {"capabilities", "keywords"}):
            errors.append(f"item {index} text fields must be non-empty strings")
        if not isinstance(item.get("capabilities"), list) or not isinstance(item.get("keywords"), list):
            errors.append(f"item {index} capabilities and keywords must be arrays")
        elif not item["keywords"] or not all(isinstance(value, str) and value.strip() for value in [*item["capabilities"], *item["keywords"]]):
            errors.append(f"item {index} capabilities and keywords must contain searchable strings")
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print(f"PASS: {len(items)} unique templates across {len(categories)} categories with valid searchable schema")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
