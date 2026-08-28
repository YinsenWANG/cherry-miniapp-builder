#!/usr/bin/env python3
"""Behavioral smoke tests for the catalog and app toolchain."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from search_templates import load_catalog, score
from validate_app import validate


ROOT = Path(__file__).resolve().parents[1]


def top_id(items: list[dict], query: str) -> str:
    return max(items, key=lambda item: score(item, query))["id"]


def main() -> int:
    catalog = load_catalog(ROOT)
    assert len(catalog) == 200
    assert top_id(catalog, "工业设备预测性维护") == "manufacturing-maintenance"
    assert top_id(catalog, "salary payroll calculator") == "hr-salary-calculator"
    assert top_id(catalog, "合同版本差异") == "legal-contract-compare"
    assert top_id(catalog, "患者教育材料") == "health-clinical-education"

    benchmarks = json.loads((ROOT / "references" / "search-benchmarks.json").read_text(encoding="utf-8"))
    for case in benchmarks:
        ranked = sorted(catalog, key=lambda item: (-score(item, case["query"]), item["id"]))
        assert case["expected"] in [item["id"] for item in ranked[: case.get("top", 3)]], case

    with tempfile.TemporaryDirectory(prefix="cherry-miniapp-tools-") as temp:
        app = Path(temp) / "app"
        subprocess.run(
            [
                sys.executable, str(ROOT / "scripts" / "scaffold_app.py"),
                "--id", "com.example.smoke", "--name", "Smoke App",
                "--description", "Exercises the complete local toolchain", "--output", str(app),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        assert not [finding for finding in validate(app) if finding.level == "error"]
        archive = Path(temp) / "smoke.miniapp"
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "package_app.py"), str(app), "--output", str(archive)],
            check=True,
            capture_output=True,
            text=True,
        )
        with zipfile.ZipFile(archive) as package:
            assert {"manifest.json", "index.html", "app.js", "styles.css"} <= set(package.namelist())
            assert json.loads(package.read("manifest.json"))["id"] == "com.example.smoke"

        manifest_path = app / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["network"] = ["api.example.com"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        assert any("network hosts" in finding.message for finding in validate(app) if finding.level == "error")

        manifest["network"] = []
        manifest["package"] = {"url": "https://example.com/app.miniapp"}
        manifest["optionalPermissions"] = ["notification.show"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        source = app / "app.js"
        source.write_text(
            source.read_text(encoding="utf-8")
            + '\nfetch("https://example.com/data")\nnew Worker("worker.js")\n',
            encoding="utf-8",
        )
        findings = validate(app)
        assert any("unsupported packaged fields: package" in item.message for item in findings if item.level == "error")
        assert any("direct outbound browser requests" in item.message for item in findings if item.level == "warning")
        assert any("workers are blocked" in item.message for item in findings if item.level == "warning")
        assert any("declares notification.show" in item.message for item in findings if item.level == "warning")

        ephemeral = Path(temp) / "ephemeral"
        subprocess.run(
            [
                sys.executable, str(ROOT / "scripts" / "scaffold_app.py"),
                "--id", "com.example.calculator", "--name", "Calculator",
                "--description", "A session-only calculator", "--archetype", "calculator",
                "--ephemeral", "--output", str(ephemeral),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        ephemeral_manifest = json.loads((ephemeral / "manifest.json").read_text(encoding="utf-8"))
        assert ephemeral_manifest["permissions"] == []
        assert "cherry.storage" not in (ephemeral / "app.js").read_text(encoding="utf-8")
        assert not validate(ephemeral)

        salary = Path(temp) / "salary"
        subprocess.run(
            [
                sys.executable, str(ROOT / "scripts" / "scaffold_app.py"),
                "--id", "com.example.salary", "--name", "Salary",
                "--description", "Compare salary scenarios", "--template-id", "hr-salary-calculator",
                "--output", str(salary),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        salary_manifest = json.loads((salary / "manifest.json").read_text(encoding="utf-8"))
        assert salary_manifest["permissions"] == ["storage.get", "storage.set"]
        assert salary_manifest["optionalPermissions"] == ["ai.chat", "file.export"]
        assert "Calculate a trustworthy result" in (salary / "index.html").read_text(encoding="utf-8")

    print("PASS: search benchmarks, archetype scaffolds, validation checks, and deterministic packaging")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
