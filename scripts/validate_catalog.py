#!/usr/bin/env python3
"""Validate the domain catalog's uniqueness, schema, and searchability."""

from __future__ import annotations

import collections
from pathlib import Path

from search_templates import CATEGORY_ALIASES, load_catalog, rank


REQUIRED = {
    "id", "category", "title", "audience", "outcome", "flow", "archetype",
    "requiredCapabilities", "optionalCapabilities", "aiMode", "ai", "guardrail", "keywords"
}
ARCHETYPES = {
    "calculator", "analyzer", "dashboard", "tracker", "planner", "checklist",
    "studio", "coach", "simulator", "game", "comparator", "coordinator"
}
CAPABILITIES = {
    "ai.chat", "storage.get", "storage.set", "storage.delete", "storage.keys",
    "file.save", "file.load", "file.list", "file.delete", "file.export",
    "notification.show", "clipboard.read", "clipboard.write", "network.fetch"
}


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
        extra = set(item) - REQUIRED
        if extra:
            errors.append(f"item {index} has unsupported fields {sorted(extra)}")
        for field in ("id", "category", "title", "audience", "outcome", "flow", "ai", "guardrail"):
            if not isinstance(item[field], str) or not item[field].strip():
                errors.append(f"item {index} {field} must be a non-empty string")
        if item["category"] not in CATEGORY_ALIASES:
            errors.append(f"item {index} has unknown category {item['category']!r}")
        if item["archetype"] not in ARCHETYPES:
            errors.append(f"item {index} has unknown archetype {item['archetype']!r}")
        if item["aiMode"] not in {"core", "enhancement", "none"}:
            errors.append(f"item {index} has invalid aiMode {item['aiMode']!r}")
        arrays_are_valid = True
        for field in ("requiredCapabilities", "optionalCapabilities", "keywords"):
            value = item[field]
            if not isinstance(value, list) or not all(isinstance(entry, str) for entry in value):
                errors.append(f"item {index} {field} must be an array of strings")
                arrays_are_valid = False
            elif len(value) != len(set(value)):
                errors.append(f"item {index} {field} must be a unique array")
                arrays_are_valid = False
        if not arrays_are_valid:
            continue
        required_caps = set(item["requiredCapabilities"])
        optional_caps = set(item["optionalCapabilities"])
        unknown = (required_caps | optional_caps) - CAPABILITIES
        if unknown:
            errors.append(f"item {index} has unknown capabilities {sorted(unknown)}")
        if required_caps & optional_caps:
            errors.append(f"item {index} repeats capabilities across required and optional")
        if any(cap.endswith(".*") for cap in required_caps | optional_caps):
            errors.append(f"item {index} uses a broad capability wildcard")
        has_ai = "ai.chat" in required_caps | optional_caps
        if has_ai != (item["aiMode"] != "none"):
            errors.append(f"item {index} aiMode does not match ai.chat capability")
        if ("ai.chat" in required_caps) != (item["aiMode"] == "core"):
            errors.append(f"item {index} core AI must be required and enhancement AI must be optional")
        if item["aiMode"] == "none" and not item["ai"].startswith("不使用 AI"):
            errors.append(f"item {index} with aiMode none must describe a deterministic no-AI implementation")
        if not item["keywords"]:
            errors.append(f"item {index} needs searchable keywords")

    benchmark_path = root / "references" / "search-benchmarks.json"
    if benchmark_path.is_file():
        import json

        for case in json.loads(benchmark_path.read_text(encoding="utf-8")):
            ranked = rank(items, case["query"])
            top = [item["id"] for _, item in ranked[: case.get("top", 3)]]
            if case["expected"] not in top:
                errors.append(f"search {case['query']!r} expected {case['expected']} in top {len(top)}, got {top}")
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print(f"PASS: {len(items)} unique templates across {len(categories)} categories with valid searchable schema (counts are descriptive, not hard constraints)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
