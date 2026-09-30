#!/usr/bin/env python3
"""Behavioral smoke tests for the catalog and app toolchain."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

from cli_output import configure_output
from package_app import handoff_archive, main as package_main, package_archive
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
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        return subprocess.run([sys.executable, "-B", *args], check=True, capture_output=True, text=True, encoding="utf-8", env=env)
    except subprocess.CalledProcessError as error:
        # Captured output would otherwise disappear behind the parent's traceback.
        for output in (error.stdout, error.stderr):
            if output:
                print(output, end="" if output.endswith("\n") else "\n", file=sys.stderr)
        raise


def check_symlink_rejection(app: Path, *, platform: str = sys.platform) -> None:
    app = app.resolve()
    link = app / "broken.js"
    try:
        link.symlink_to(app / "missing.js")
    except OSError as error:
        if platform != "win32" or getattr(error, "winerror", None) != 1314:
            raise
        print("SKIP: native symlink creation requires Windows privilege (winerror 1314); checking simulated symlink rejection")
        # Exercise the real validator and traversal with only the OS predicate
        # simulated. Never skip the rejection assertion on restricted runners.
        link.write_text("", encoding="utf-8")
        native_is_symlink = Path.is_symlink
        try:
            with patch.object(Path, "is_symlink", lambda path: path == link or native_is_symlink(path)):
                assert any("symbolic link is not allowed" in message for message in errors(app))
        finally:
            link.unlink()
        print("PASS: simulated symlink rejection")
    else:
        try:
            assert any("symbolic link is not allowed" in message for message in errors(app))
        finally:
            link.unlink()
        print("PASS: native symlink rejection")


def main() -> int:
    contract = (ROOT / "references" / "technical-contract.md").read_text(encoding="utf-8")
    playbook = (ROOT / "references" / "build-playbook.md").read_text(encoding="utf-8")
    modal_example = (ROOT / "assets" / "modal-example.html").read_text(encoding="utf-8")
    for marker in ('role="dialog"', 'aria-modal="true"', "backdrop", "Escape", "restore focus", "max-height", "cherry.ai.cancel(callId)", "cherry.file.export"):
        assert marker in contract, marker
    for marker in ("backdrop-self", "idempotent close", "unique `callId`", "ordinary page"):
        assert marker in playbook, marker
    for marker in ('aria-modal="true"', "closeButton.addEventListener", "modal.addEventListener", "document.addEventListener", "event.key !== 'Escape'", "opener?.focus", "max-height", "overflow: auto", "cancelButton.disabled = false", "callId", "cherry.ai.cancel", "closeModal();\n      await cherry.file.export"):
        assert marker in modal_example, marker

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

        def unexpected_runner(*args, **kwargs):
            raise AssertionError((args, kwargs))

        default_output = StringIO()
        default_archive = Path(temp) / "default-no-handoff.miniapp"
        with redirect_stdout(default_output):
            assert package_main([str(app), "--output", str(default_archive)], runner=unexpected_runner, platform="darwin") == 0
        assert default_archive.is_file()
        assert "Manual install:" in default_output.getvalue()

        calls = []
        def recording_runner(command, **kwargs):
            calls.append((command, kwargs))

        handoff_output = StringIO()
        with redirect_stdout(handoff_output):
            handoff_archive(default_archive.resolve(), platform="darwin", runner=recording_runner)
        assert calls == [
            (["pbcopy"], {"check": True, "input": str(default_archive.resolve()), "text": True, "encoding": "utf-8"}),
            (["open", "-R", str(default_archive.resolve())], {"check": True}),
            (["open", "cherrystudio://navigate/app/mini-app/"], {"check": True}),
        ]
        assert handoff_output.getvalue().count("HANDOFF OK:") == 3

        unsupported_output = StringIO()
        with redirect_stdout(unsupported_output):
            handoff_archive(default_archive.resolve(), platform="linux", runner=unexpected_runner)
        assert "unsupported on this platform" in unsupported_output.getvalue()

        failed_calls = []
        def failing_runner(command, **kwargs):
            failed_calls.append(command)
            if command[0] == "pbcopy":
                raise OSError("clipboard unavailable")

        failed_output = StringIO()
        with redirect_stdout(failed_output):
            assert package_main([str(app), "--output", str(Path(temp) / "failed-handoff.miniapp"), "--handoff"], runner=failing_runner, platform="darwin") == 0
        assert len(failed_calls) == 3
        assert "HANDOFF FAILED:" in failed_output.getvalue()
        assert "Manual install:" in failed_output.getvalue()

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
        check_symlink_rejection(app)
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
        dialog_warning = "heuristic: dialog/modal found but no reachable close implementation was detected; verify close button, backdrop, and Escape"
        (app / "dialog.html").write_text('<div role="dialog" aria-modal="true">No close path</div>', encoding="utf-8")
        dialog_findings = validate(app)
        assert sum(finding.message == dialog_warning for finding in dialog_findings) == 1
        assert not [finding for finding in dialog_findings if finding.level == "error"]
        warning_archive = Path(temp) / "dialog-warning.miniapp"
        assert f"WARNING: {dialog_warning}" in run_python(str(ROOT / "scripts" / "package_app.py"), str(app), "--output", str(warning_archive)).stdout
        (app / "dialog.js").write_text("closeButton.addEventListener('click', closeModal); function closeModal() { modal.hidden = true; }", encoding="utf-8")
        assert not any(finding.message == dialog_warning for finding in validate(app))
        (app / "dialog.html").write_text('<div class="overlay">Overlay copy says role=&quot;dialog&quot;.</div>', encoding="utf-8")
        (app / "dialog.js").unlink()
        assert not any(finding.message == dialog_warning for finding in validate(app))
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
        assert not any(finding.message == dialog_warning for finding in validate(ephemeral))

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
    configure_output()
    raise SystemExit(main())
