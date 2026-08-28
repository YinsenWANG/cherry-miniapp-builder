#!/usr/bin/env python3
"""Behavioral smoke tests for the catalog and app toolchain."""

from __future__ import annotations

import json
import subprocess
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

    with tempfile.TemporaryDirectory(prefix="cherry-miniapp-tools-") as temp:
        app = Path(temp) / "app"
        subprocess.run(
            [
                "python3", str(ROOT / "scripts" / "scaffold_app.py"),
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
            ["python3", str(ROOT / "scripts" / "package_app.py"), str(app), "--output", str(archive)],
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

    print("PASS: catalog retrieval, scaffold, validation, packaging, and negative contract case")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
