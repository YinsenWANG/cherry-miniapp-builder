#!/usr/bin/env python3
"""Regression checks for interpreter selection and the UTF-8 CLI contract."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cli_output import configure_output
from search_templates import load_catalog, rank, render
from test_tools import run_python


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def cli(script: str, *args: str, encoding: str = "cp1252", root: Path = ROOT) -> subprocess.CompletedProcess[bytes]:
    env = os.environ.copy()
    env.update(PYTHONIOENCODING=encoding, PYTHONUTF8="0", PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, "-B", str(root / "scripts" / script), *args], capture_output=True, env=env)


class CliReliabilityTests(unittest.TestCase):
    def assert_output(self, result, code, text, *, stderr=False):
        self.assertEqual(result.returncode, code, result.stderr.decode("utf-8", errors="backslashreplace"))
        output = (result.stderr if stderr else result.stdout).decode("utf-8")
        self.assertIn(text, output)
        self.assertNotIn("UnicodeEncodeError", output)
        return output

    def test_current_interpreter_without_path_alias(self):
        with patch.dict(os.environ, {"PATH": ""}):
            result = run_python("-c", "import sys; print(sys.executable)")
        self.assertTrue(os.path.samefile(result.stdout.strip(), sys.executable))

    def test_explicit_utf8_subprocess_decoding(self):
        # Model a legacy default decoder, but execute a real child and decode real bytes.
        native_run = subprocess.run
        def legacy_run(command, **kwargs):
            return native_run(command, **{"encoding": "cp1252", **kwargs})
        with patch("test_tools.subprocess.run", side_effect=legacy_run):
            result = run_python("-c", "import sys; sys.stdout.buffer.write(bytes.fromhex('e7bbb4e68aa4'))")
        self.assertEqual(result.stdout, "维护")

    def test_child_stdio_is_utf8_under_legacy_environment(self):
        with patch.dict(os.environ, {"PYTHONIOENCODING": "ascii", "PYTHONUTF8": "0"}):
            result = run_python("-c", "print('\\u7ef4\\u62a4')")
        self.assertEqual(result.stdout.strip(), "维护")

    def test_original_child_errors_are_visible_and_preserved(self):
        output = StringIO()
        with redirect_stderr(output), self.assertRaises(subprocess.CalledProcessError) as caught:
            run_python("-c", "import sys; print('original-' + 'child-output'); print('original-' + 'child-error', file=sys.stderr); sys.exit(7)")
        self.assertEqual(caught.exception.returncode, 7)
        self.assertEqual(caught.exception.stdout.strip(), "original-child-output")
        self.assertEqual(caught.exception.stderr.strip(), "original-child-error")
        self.assertIn("original-child-output", output.getvalue())
        self.assertIn("original-child-error", output.getvalue())

    def test_symlink_privilege_fallback_is_explicit_and_still_checks_rejection(self):
        import test_tools
        privilege_error = OSError("Windows symlink privilege is required")
        privilege_error.winerror = 1314
        with tempfile.TemporaryDirectory(prefix="cherry-symlink-") as temp:
            app = Path(temp) / "app"
            self.assertEqual(cli("scaffold_app.py", "--id", "com.example.symlink", "--name", "Test", "--description", "Test", "--output", str(app), encoding="utf-8").returncode, 0)
            output = StringIO()
            with patch.object(Path, "symlink_to", side_effect=privilege_error), redirect_stdout(output):
                test_tools.check_symlink_rejection(app, platform="win32")
            self.assertIn("SKIP: native symlink", output.getvalue())
            self.assertIn("1314", output.getvalue())
            self.assertIn("simulated", output.getvalue())
            self.assertFalse((app / "broken.js").exists())
            with patch.object(Path, "symlink_to", side_effect=privilege_error), patch("test_tools.errors", return_value=[]), redirect_stdout(StringIO()):
                with self.assertRaises(AssertionError):
                    test_tools.check_symlink_rejection(app, platform="win32")

    def test_unexpected_symlink_errors_are_not_skipped(self):
        import test_tools
        for platform, winerror in (("linux", 1314), ("win32", 5), ("win32", None)):
            error = OSError("unexpected creation failure")
            error.winerror = winerror
            with self.subTest(platform=platform, winerror=winerror), patch.object(Path, "symlink_to", side_effect=error):
                with self.assertRaises(OSError) as caught:
                    test_tools.check_symlink_rejection(Path("unused"), platform=platform)
                self.assertIs(caught.exception, error)

    def test_search_json_text_and_parser_errors(self):
        selected = [item for _, item in rank(load_catalog(ROOT), "")[:2]]
        for encoding in ("cp1252", "ascii"):
            with self.subTest(encoding=encoding):
                result = cli("search_templates.py", "--limit", "2", "--json", encoding=encoding)
                output = self.assert_output(result, 0, selected[0]["title"])
                self.assertEqual(json.loads(output), selected)
                self.assertEqual(result.stderr, b"")
                result = cli("search_templates.py", "--limit", "2", encoding=encoding)
                output = self.assert_output(result, 0, selected[0]["title"])
                self.assertEqual(output.replace("\r\n", "\n"), "\n\n".join(map(render, selected)) + "\n")
                self.assert_output(cli("search_templates.py", "--unknown-维护", encoding=encoding), 2, "--unknown-维护", stderr=True)
                self.assert_output(cli("search_templates.py", "--category", "absent", encoding=encoding), 0, "No matching template.")

    def test_unicode_toolchain_paths_findings_and_archives(self):
        for encoding in ("cp1252", "ascii"):
            with self.subTest(encoding=encoding), tempfile.TemporaryDirectory(prefix="cherry-encoding-") as temp:
                app = Path(temp) / "维护助手"
                scaffold_args = ("--id", "com.example.encoding", "--name", "维护助手", "--description", "检查异常趋势", "--output", str(app))
                result = cli("scaffold_app.py", *scaffold_args, encoding=encoding)
                self.assert_output(result, 0, str(app.resolve()))
                manifest = json.loads((app / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["name"], {"en": "维护助手", "zh": "维护助手"})
                self.assertEqual(manifest["description"], {"en": "检查异常趋势", "zh": "检查异常趋势"})
                self.assert_output(cli("scaffold_app.py", *scaffold_args, encoding=encoding), 2, str(app.resolve()), stderr=True)
                self.assert_output(cli("scaffold_app.py", *scaffold_args, "--template-id", "不存在", encoding=encoding), 2, "unknown template id: 不存在", stderr=True)
                self.assert_output(cli("validate_app.py", str(Path(temp) / "不存在"), encoding=encoding), 1, "不存在")
                self.assert_output(cli("validate_app.py", str(app), encoding=encoding), 0, "PASS: 0 errors")
                (app / "警告.js").write_text("// localStorage", encoding="utf-8")
                self.assert_output(cli("validate_app.py", str(app), encoding=encoding), 0, "警告.js: localStorage")
                first = Path(temp) / "维护包.miniapp"
                second = Path(temp) / "第二包.miniapp"
                for archive in (first, second):
                    output = self.assert_output(cli("package_app.py", str(app), "--output", str(archive), encoding=encoding), 0, str(archive.resolve()))
                    self.assertIn("警告.js: localStorage", output)
                    self.assertIn("Mini Apps → + → Package", output)
                self.assertEqual(first.read_bytes(), second.read_bytes())
                manifest["entry"] = "不存在.html"
                (app / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
                self.assert_output(cli("validate_app.py", str(app), encoding=encoding), 1, "不存在.html")
                self.assert_output(cli("package_app.py", str(app), encoding=encoding), 1, "不存在.html")

    def test_catalog_and_load_errors_use_utf8(self):
        for encoding in ("cp1252", "ascii"):
            with self.subTest(encoding=encoding), tempfile.TemporaryDirectory(prefix="cherry-catalog-") as temp:
                root = Path(temp) / "目录"
                shutil.copytree(SCRIPTS, root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
                shutil.copytree(ROOT / "references" / "domains", root / "references" / "domains")
                benchmarks = [{"query": "维护", "expected": "nonexistent", "top": 1}]
                (root / "references" / "search-benchmarks.json").write_text(json.dumps(benchmarks, ensure_ascii=False), encoding="utf-8")
                self.assert_output(cli("validate_catalog.py", encoding=encoding, root=root), 1, "search '维护'")
                (root / "references" / "domains" / "损坏.jsonl").write_text("{bad json", encoding="utf-8")
                self.assert_output(cli("search_templates.py", encoding=encoding, root=root), 1, "损坏.jsonl:1:", stderr=True)


if __name__ == "__main__":
    configure_output()
    unittest.main()
