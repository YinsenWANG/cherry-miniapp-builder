#!/usr/bin/env python3
"""Behavioral smoke tests for the catalog and app toolchain."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

from package_app import package_archive
from search_templates import load_catalog, rank, score, terms
from validate_app import validate


ROOT = Path(__file__).resolve().parents[1]


def errors(app: Path) -> list[str]:
    return [finding.message for finding in validate(app) if finding.level == "error"]


def write_manifest(app: Path, **changes: object) -> None:
    path = app / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest.update(changes)
    path.write_text(json.dumps(manifest), encoding="utf-8")


def run_python(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", "-B", *args], check=True, capture_output=True, text=True, env=os.environ.copy())


def main() -> int:
    catalog = load_catalog(ROOT)
    assert len(catalog) == 200
    for query, expected in {
        "工业设备预测性维护": "manufacturing-maintenance",
        "salary payroll calculator": "hr-salary-calculator",
        "合同版本差异": "legal-contract-compare",
        "患者教育材料": "health-clinical-education",
    }.items():
        assert rank(catalog, query)[0][1]["id"] == expected
    tie_items = [{"id": "b", "title": "A", "keywords": [], "category": "x", "audience": "", "outcome": "", "flow": ""}, {"id": "a", "title": "A", "keywords": [], "category": "x", "audience": "", "outcome": "", "flow": ""}]
    assert [item["id"] for _, item in rank(tie_items, "A")] == ["a", "b"]
    assert {"a", "b"} <= terms("A/B") and "工资" in terms("工资计算")
    cli_rank = json.loads(run_python(str(ROOT / "scripts" / "search_templates.py"), "--limit", "2", "--json").stdout)
    assert [item["id"] for item in cli_rank] == [item["id"] for _, item in rank(catalog, "")[:2]]

    benchmarks = json.loads((ROOT / "references" / "search-benchmarks.json").read_text(encoding="utf-8"))
    for case in benchmarks:
        ranked = rank(catalog, case["query"])
        assert case["expected"] in [item["id"] for _, item in ranked[: case.get("top", 3)]], case

    with tempfile.TemporaryDirectory(prefix="cherry-miniapp-tools-") as temp:
        app = Path(temp) / "app"
        run_python(
            str(ROOT / "scripts" / "scaffold_app.py"),
                "--id", "com.example.smoke", "--name", "Smoke App",
                "--description", "Exercises the complete local toolchain", "--output", str(app),
        )
        assert not [finding for finding in validate(app) if finding.level == "error"]
        archive = Path(temp) / "smoke.miniapp"
        run_python(str(ROOT / "scripts" / "package_app.py"), str(app), "--output", str(archive))
        with zipfile.ZipFile(archive) as package:
            assert {"manifest.json", "index.html", "app.js", "styles.css"} <= set(package.namelist())
            assert json.loads(package.read("manifest.json"))["id"] == "com.example.smoke"

        for version, valid in {"1.0.0-01": False, "1.0.0-a..b": False, "1.0.0-rc.1+build.7": True}.items():
            write_manifest(app, version=version)
            assert bool(errors(app)) is not valid
        write_manifest(app, version="1.0.0", entry=".hidden/index.html")
        assert any("path segments must not start" in message for message in errors(app))
        write_manifest(app, entry="index.html", icon={"path": ".hidden/icon.svg", "sha256": "0" * 64})
        assert any("path segment starting" in message for message in errors(app))
        write_manifest(app, entry="index.html", permissions=["storage.*"], optionalPermissions=["storage.get"])
        assert any("permissions overlap" in message for message in errors(app))
        write_manifest(app, permissions=[], optionalPermissions=[])
        icon = app / "icon.svg"
        icon.write_text("<svg/>", encoding="utf-8")
        write_manifest(app, icon={"path": "icon.svg", "sha256": "0" * 64})
        assert any("icon.sha256 does not match" in message for message in errors(app))
        write_manifest(app, icon=None)
        (app / "broken.js").symlink_to(app / "missing.js")
        assert any("symbolic link is not allowed" in message for message in errors(app))
        (app / "broken.js").unlink()
        (app / "comment.js").write_text("// cherry.ai.chat", encoding="utf-8")
        findings = validate(app)
        assert any(finding.level == "warning" and "heuristic" in finding.message for finding in findings)
        warning_archive = Path(temp) / "warning.miniapp"
        assert "WARNING: heuristic:" in run_python(str(ROOT / "scripts" / "package_app.py"), str(app), "--output", str(warning_archive)).stdout
        (app / "links.html").write_text('<a href="https://example.com">link</a>', encoding="utf-8")
        assert not any("remote runtime assets" in finding.message for finding in validate(app))
        (app / "links.html").write_text('<script src="https://example.com/a.js"></script>', encoding="utf-8")
        assert any("remote runtime assets" in finding.message for finding in validate(app))
        (app / "remote.css").write_text("@import url(https://example.com/a.css);", encoding="utf-8")
        assert any("remote runtime assets" in finding.message for finding in validate(app))
        old = Path(temp) / "old.miniapp"
        old.write_bytes(b"old archive")
        try:
            package_archive(app, old, max_archive=1)
        except ValueError:
            pass
        else:
            raise AssertionError("small archive cap must reject")
        assert old.read_bytes() == b"old archive"
        assert not list(old.parent.glob(f".{old.name}.*.tmp"))

        ephemeral = Path(temp) / "ephemeral"
        run_python(
            str(ROOT / "scripts" / "scaffold_app.py"),
                "--id", "com.example.calculator", "--name", "Calculator",
                "--description", "A session-only calculator", "--archetype", "calculator",
                "--ephemeral", "--output", str(ephemeral),
        )
        ephemeral_manifest = json.loads((ephemeral / "manifest.json").read_text(encoding="utf-8"))
        assert ephemeral_manifest["permissions"] == []
        assert "cherry.storage" not in (ephemeral / "app.js").read_text(encoding="utf-8")
        assert not validate(ephemeral)

        salary = Path(temp) / "salary"
        run_python(
            str(ROOT / "scripts" / "scaffold_app.py"),
                "--id", "com.example.salary", "--name", "Salary",
                "--description", "Compare salary scenarios", "--template-id", "hr-salary-calculator",
                "--output", str(salary),
        )
        salary_manifest = json.loads((salary / "manifest.json").read_text(encoding="utf-8"))
        assert salary_manifest["permissions"] == ["storage.get", "storage.set"]
        assert salary_manifest["optionalPermissions"] == ["ai.chat", "file.export"]
        assert "Calculate a trustworthy result" in (salary / "index.html").read_text(encoding="utf-8")

    print("PASS: search benchmarks, deterministic rank, archetype scaffolds, validation checks, and deterministic packaging")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
