#!/usr/bin/env python3
"""Validate the domain catalog's count, uniqueness, and template schema."""

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
    if len(items) != 200:
        errors.append(f"expected 200 templates, found {len(items)}")
    if duplicates:
        errors.append(f"duplicate ids: {', '.join(map(str, duplicates))}")
    categories = collections.Counter(item.get("category") for item in items)
    if len(categories) != 25:
        errors.append(f"expected 25 categories, found {len(categories)}")
    for category, count in categories.items():
        if count != 8:
            errors.append(f"category {category!r} has {count} templates, expected 8")
    for index, item in enumerate(items, 1):
        missing = REQUIRED - set(item)
        if missing:
            errors.append(f"item {index} missing {sorted(missing)}")
        if not isinstance(item.get("capabilities"), list) or not isinstance(item.get("keywords"), list):
            errors.append(f"item {index} capabilities and keywords must be arrays")
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print(f"PASS: {len(items)} unique templates, {len(categories)} categories, 8 templates each")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
