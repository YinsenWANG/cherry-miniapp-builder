#!/usr/bin/env python3
"""Search the Cherry mini-app idea catalog."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def load_catalog(root: Path) -> list[dict]:
    items: list[dict] = []
    for path in sorted((root / "references" / "domains").glob("*.jsonl")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise SystemExit(f"{path}:{number}: {error}") from error
    return items


def terms(text: str) -> set[str]:
    lowered = text.casefold()
    chunks = set(re.findall(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|[\u3400-\u9fff]+", lowered))
    for chunk in list(chunks):
        if re.fullmatch(r"[\u3400-\u9fff]+", chunk):
            chunks.update(chunk[index:index + 2] for index in range(len(chunk) - 1))
    return chunks


def score(item: dict, query: str) -> int:
    title = item["title"].casefold()
    keyword_values = [keyword.casefold() for keyword in item["keywords"]]
    keywords = " ".join(keyword_values)
    category = item["category"].casefold()
    product = " ".join([item["audience"], item["outcome"], item["flow"]]).casefold()
    query_lower = query.casefold().strip()
    value = 0
    if query_lower:
        if query_lower == title or query_lower in keyword_values:
            value += 80
        elif query_lower in title:
            value += 45
        elif query_lower in category:
            value += 30
        elif query_lower in product:
            value += 15
    for term in terms(query):
        weight = 1 if len(term) == 1 and term.isascii() else 3
        def contains(value: str) -> bool:
            if len(term) == 1 and term.isascii():
                return bool(re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", value))
            return term in value
        if term == title or term in keyword_values:
            value += 30 * weight
        elif contains(title) or contains(keywords):
            value += 20 * weight
        elif contains(category):
            value += 11 * weight
        elif contains(product):
            value += 4 * weight
    return value


def rank(items: list[dict], query: str) -> list[tuple[int, dict]]:
    """Return the single deterministic ranking used by both CLI and tests."""
    return sorted(((score(item, query), item) for item in items), key=lambda pair: (-pair[0], pair[1]["id"]))


def render(item: dict) -> str:
    capabilities = ", ".join(item["capabilities"]) if item["capabilities"] else "none"
    return "\n".join(
        [
            f"## {item['id']} · {item['title']}",
            f"- Category: `{item['category']}`",
            f"- Audience: {item['audience']}",
            f"- Outcome: {item['outcome']}",
            f"- Core flow: {item['flow']}",
            f"- 可能涉及的能力（须按实际调用重推最小 leaf）: {capabilities}",
            f"- AI role: {item['ai']}",
            f"- Guardrail: {item['guardrail']}",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default="")
    parser.add_argument("--category")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    items = load_catalog(root)
    if args.category:
        items = [item for item in items if item["category"] == args.category]
    ranked = rank(items, args.query)
    if args.query:
        best = ranked[0][0] if ranked else 0
        ranked = [pair for pair in ranked if pair[0] >= max(2, int(best * 0.4))]
    selected = [item for _, item in ranked[: max(1, min(args.limit, 20))]]
    if args.json:
        print(json.dumps(selected, ensure_ascii=False, indent=2))
    elif selected:
        print("\n\n".join(render(item) for item in selected))
    else:
        print("No matching template. Try a broader term or inspect references/domain-index.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
