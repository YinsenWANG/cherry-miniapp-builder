#!/usr/bin/env python3
"""Create a dependency-free Cherry mini-app source tree."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path

from search_templates import load_catalog
from validate_app import GRANTS


TOKENS = {
    "manifest.json.tmpl": "manifest.json",
    "index.html.tmpl": "index.html",
    "app.js.tmpl": "app.js",
}

ARCHETYPE_COPY = {
    "calculator": ("Inputs and assumptions", "Calculate a trustworthy result", "Calculate", "Inputs", "Saved scenarios"),
    "analyzer": ("Evidence to insight", "Inspect data, surface findings, and act", "Analyze", "Source", "Findings"),
    "dashboard": ("Signals at a glance", "See what changed and what needs attention", "Open overview", "Signals", "Details"),
    "tracker": ("Progress over time", "Capture the next update and keep momentum visible", "Add update", "New update", "Timeline"),
    "planner": ("Constraints to a plan", "Build a workable plan and compare tradeoffs", "Create plan", "Constraints", "Plan"),
    "checklist": ("Ready for the real task", "Work through the critical steps without losing context", "Start checklist", "Preparation", "Checklist"),
    "studio": ("Source to artifact", "Shape an idea into a reviewable result", "Create draft", "Source", "Preview"),
    "coach": ("Practice and feedback", "Take one guided step and improve with evidence", "Begin session", "Context", "Feedback"),
    "simulator": ("Assumptions to scenarios", "Change the inputs and understand the consequences", "Run scenario", "Assumptions", "Scenarios"),
    "game": ("Play immediately", "Learn through a short, responsive challenge", "Play", "Challenge", "Progress"),
    "comparator": ("Options side by side", "Compare consistent criteria and make the tradeoffs explicit", "Compare", "Options", "Comparison"),
    "coordinator": ("People, work, and handoffs", "Move one shared workflow from intake to closure", "Add work", "Intake", "Work queue"),
}


def remove_block(text: str, name: str) -> str:
    pattern = rf"\n?\s*/\* {re.escape(name)}_START \*/.*?/\* {re.escape(name)}_END \*/\s*\n?"
    return re.sub(pattern, "\n", text, flags=re.S)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True, dest="app_id")
    parser.add_argument("--name", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--template-id", help="domain template id from references/domains")
    parser.add_argument("--archetype", choices=sorted(ARCHETYPE_COPY))
    parser.add_argument("--required-capability", action="append", default=[], choices=sorted(GRANTS))
    parser.add_argument("--optional-capability", action="append", default=[], choices=sorted(GRANTS))
    parser.add_argument("--network-host", action="append", default=[])
    parser.add_argument("--ephemeral", action="store_true", help="do not add the starter's default storage permissions")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    template = None
    if args.template_id:
        template = next((item for item in load_catalog(root) if item["id"] == args.template_id), None)
        if template is None:
            parser.error(f"unknown template id: {args.template_id}")
    if args.ephemeral and template:
        parser.error("--ephemeral cannot be combined with --template-id; template permissions describe its complete flow")

    archetype = args.archetype or (template["archetype"] if template else "coordinator")
    required = set(template["requiredCapabilities"] if template else ([] if args.ephemeral else ["storage.get", "storage.set"]))
    optional = set(template["optionalCapabilities"] if template else [])
    required.update(args.required_capability)
    optional.update(args.optional_capability)
    overlap = required & optional
    if overlap:
        parser.error(f"capabilities cannot be both required and optional: {', '.join(sorted(overlap))}")
    storage_pair = {"storage.get", "storage.set"}
    if optional & storage_pair:
        parser.error("the starter treats persistence as core; declare storage.get and storage.set as required")
    if required & storage_pair and not storage_pair <= required:
        parser.error("the starter persistence flow requires storage.get and storage.set together")
    if args.network_host and "network.fetch" not in required | optional:
        parser.error("--network-host requires network.fetch as a required or optional capability")
    if "network.fetch" in required | optional and not args.network_host:
        parser.error("network.fetch requires at least one --network-host")

    starter = root / "assets" / "starter"
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error(f"output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    eyebrow, headline, action, input_label, output_label = ARCHETYPE_COPY[archetype]
    replacements = {
        "__APP_ID_JSON__": json.dumps(args.app_id, ensure_ascii=False),
        "__APP_NAME_JSON__": json.dumps(args.name, ensure_ascii=False),
        "__APP_DESCRIPTION_JSON__": json.dumps(args.description, ensure_ascii=False),
        "__APP_NAME_HTML__": html.escape(args.name),
        "__ARCHETYPE_EYEBROW_HTML__": html.escape(eyebrow),
        "__ARCHETYPE_HEADLINE_HTML__": html.escape(headline),
        "__ARCHETYPE_ACTION_HTML__": html.escape(action),
        "__ARCHETYPE_INPUT_HTML__": html.escape(input_label),
        "__ARCHETYPE_OUTPUT_HTML__": html.escape(output_label),
        "__REQUIRED_CAPABILITIES_JSON__": json.dumps(sorted(required), ensure_ascii=False),
        "__OPTIONAL_CAPABILITIES_JSON__": json.dumps(sorted(optional), ensure_ascii=False),
        "__NETWORK_HOSTS_JSON__": json.dumps(args.network_host, ensure_ascii=False),
    }
    for source in sorted(starter.iterdir()):
        target = output / TOKENS.get(source.name, source.name)
        if source.suffix == ".tmpl":
            text = source.read_text(encoding="utf-8")
            for token, value in replacements.items():
                text = text.replace(token, value)
            if source.name == "app.js.tmpl" and not storage_pair <= required:
                text = remove_block(text, "PERSISTENCE")
            target.write_text(text, encoding="utf-8")
        else:
            shutil.copy2(source, target)

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
