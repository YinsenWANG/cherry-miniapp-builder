#!/usr/bin/env python3
"""Validate a Cherry Studio Real Mini App source directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


MAX_ARCHIVE = 50 * 1024 * 1024
MAX_EXTRACTED = 100 * 1024 * 1024
MAX_MANIFEST = 256 * 1024
MAX_ICON = 5 * 1024 * 1024
MAX_ENTRIES = 2000

GRANTS = {
    "ai.chat",
    "storage.get", "storage.set", "storage.delete", "storage.keys",
    "file.save", "file.load", "file.list", "file.delete", "file.export",
    "notification.show", "clipboard.read", "clipboard.write", "network.fetch",
}
NAMESPACES = {item.split(".", 1)[0] for item in GRANTS}
WINDOWS_RESERVED = {"con", "prn", "aux", "nul"} | {f"com{i}" for i in range(10)} | {f"lpt{i}" for i in range(10)}
ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*$")
HOST_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$")
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
MANIFEST_FIELDS = {
    "id", "name", "description", "version", "entry", "icon", "releaseNotes",
    "permissions", "optionalPermissions", "network", "update",
}


@dataclass(frozen=True)
class Finding:
    level: str
    message: str


def expand(items: list[str]) -> set[str]:
    result: set[str] = set()
    for item in items:
        if item.endswith(".*"):
            namespace = item[:-2]
            result.update(value for value in GRANTS if value.startswith(namespace + "."))
        else:
            result.add(item)
    return result


def valid_declaration(value: object) -> bool:
    return isinstance(value, str) and (value in GRANTS or (value.endswith(".*") and value[:-2] in NAMESPACES))


def validate_localized(value: object, field: str, cap: int, out: list[Finding]) -> None:
    if isinstance(value, str):
        if not value or len(value) > cap:
            out.append(Finding("error", f"{field} must contain 1–{cap} characters"))
        return
    if not isinstance(value, dict) or not ({"en", "zh"} & set(value)):
        out.append(Finding("error", f"{field} must be a string or locale object containing en or zh"))
        return
    if len(value) > 20:
        out.append(Finding("error", f"{field} has more than 20 locales"))
    for locale, text in value.items():
        if not isinstance(locale, str) or not isinstance(text, str) or not text or len(text) > cap:
            out.append(Finding("error", f"{field}.{locale} must contain 1–{cap} characters"))


def safe_relative(value: object) -> bool:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value:
        return False
    parts = value.split("/")
    return ".." not in parts and parts[0] != "__cherry"


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() or path.is_symlink():
            yield path


def scan_sources(root: Path, manifest: dict, out: list[Finding]) -> None:
    declarations = expand([*manifest.get("permissions", []), *manifest.get("optionalPermissions", [])])
    text_suffixes = {".html", ".htm", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".css", ".json", ".svg"}
    combined: list[tuple[Path, str]] = []
    for path in iter_files(root):
        if path.suffix.lower() not in text_suffixes or path.stat().st_size > 2 * 1024 * 1024:
            continue
        try:
            combined.append((path, path.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            continue

    banned = {
        r"\blocalStorage\b": "localStorage is unavailable; use cherry.storage",
        r"\bsessionStorage\b": "sessionStorage is unavailable; keep ephemeral state in memory",
        r"\bindexedDB\b": "IndexedDB is unavailable; use cherry.storage or cherry.file",
        r"navigator\.clipboard": "navigator.clipboard is denied; use cherry.clipboard",
        r"\bWebSocket\s*\(": "WebSocket is blocked; use bounded cherry.network.fetch requests",
        r"\bEventSource\s*\(": "EventSource is blocked; use cherry.network.fetch",
        r"serviceWorker\.register": "service workers are blocked",
        r"\bwindow\.open\s*\(": "popups are blocked",
        r"show(?:Open|Save|Directory)FilePicker\s*\(": "File System Access pickers are denied",
        r"\b(?:new\s+)?(?:Shared)?Worker\s*\(": "workers are blocked; keep computation in the page",
        r"\bRTCPeerConnection\s*\(": "WebRTC is blocked",
        r"\bnavigator\.sendBeacon\s*\(": "sendBeacon is blocked; use cherry.network.fetch",
        r"\bnavigator\.(?:geolocation|mediaDevices)\b": "browser permission APIs are blocked",
        r"\bNotification\s*\(": "browser notifications are blocked; use cherry.notification.show",
        r"\bcaches\.(?:open|match|keys|delete)\s*\(": "Cache API is unavailable",
        r"\bdocument\.cookie\b": "cookies are unavailable",
    }
    seen: set[str] = set()
    for path, text in combined:
        relative = path.relative_to(root)
        for pattern, message in banned.items():
            key = f"{relative}:{message}"
            if key not in seen and re.search(pattern, text):
                out.append(Finding("warning", f"{relative}: {message}"))
                seen.add(key)
        if re.search(r"(?:src|href)\s*=\s*['\"]https?://", text, re.I) or re.search(r"@import\s+['\"]https?://", text, re.I):
            out.append(Finding("warning", f"{relative}: remote runtime assets are blocked; bundle them"))
        if re.search(r"\bfetch\s*\(\s*['\"]https?://", text, re.I) or re.search(r"\bXMLHttpRequest\s*\(", text):
            out.append(Finding("warning", f"{relative}: direct outbound browser requests are blocked; use cherry.network.fetch"))
        if re.search(r"<\s*(?:iframe|frame)\b", text, re.I):
            out.append(Finding("warning", f"{relative}: frames are blocked"))
        if re.search(r"<\s*form\b[^>]*\baction\s*=", text, re.I):
            out.append(Finding("warning", f"{relative}: form navigation is blocked; handle submission inside the app"))

    joined = "\n".join(text for _, text in combined)
    call_to_grant = {
        "cherry.ai.chat": "ai.chat",
        "cherry.storage.get": "storage.get", "cherry.storage.set": "storage.set",
        "cherry.storage.delete": "storage.delete", "cherry.storage.keys": "storage.keys",
        "cherry.file.save": "file.save", "cherry.file.load": "file.load",
        "cherry.file.list": "file.list", "cherry.file.delete": "file.delete", "cherry.file.export": "file.export",
        "cherry.notification.show": "notification.show", "cherry.clipboard.read": "clipboard.read",
        "cherry.clipboard.write": "clipboard.write", "cherry.network.fetch": "network.fetch",
    }
    for call, grant in call_to_grant.items():
        if call in joined and grant not in declarations:
            out.append(Finding("error", f"source calls {call} but manifest does not declare {grant}"))

    used_grants = {grant for call, grant in call_to_grant.items() if call in joined}
    for declaration in sorted(declarations - used_grants):
        out.append(Finding("warning", f"manifest declares {declaration} but no matching window.cherry call was found"))

    html_files = [text for path, text in combined if path.suffix.lower() in {".html", ".htm"}]
    if html_files and not any('/__cherry/theme.css' in text for text in html_files):
        out.append(Finding("warning", "no HTML file includes /__cherry/theme.css"))


def validate(root: Path) -> list[Finding]:
    root = root.resolve()
    out: list[Finding] = []
    manifest_path = root / "manifest.json"
    if not root.is_dir():
        return [Finding("error", f"not a directory: {root}")]
    if not manifest_path.is_file():
        return [Finding("error", "manifest.json is missing at the app root")]
    if manifest_path.stat().st_size > MAX_MANIFEST:
        out.append(Finding("error", "manifest.json exceeds 256 KB"))
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        return [Finding("error", f"manifest.json is not valid UTF-8 JSON: {error}")]
    if not isinstance(manifest, dict):
        return [Finding("error", "manifest.json root must be an object")]
    unsupported = sorted(set(manifest) - MANIFEST_FIELDS)
    if unsupported:
        out.append(Finding("error", f"manifest contains unsupported packaged fields: {', '.join(unsupported)}"))

    app_id = manifest.get("id")
    if not isinstance(app_id, str) or len(app_id) > 120 or not ID_RE.fullmatch(app_id):
        out.append(Finding("error", "id is not a valid lowercase reverse-DNS mini-app id"))
    elif app_id.split(".")[0] in WINDOWS_RESERVED:
        out.append(Finding("error", "id starts with a Windows reserved device name"))
    elif app_id.startswith("com.cherrystudio."):
        out.append(Finding("error", "com.cherrystudio.* is reserved for official packages"))

    validate_localized(manifest.get("name"), "name", 64, out)
    validate_localized(manifest.get("description"), "description", 200, out)
    if "releaseNotes" in manifest:
        validate_localized(manifest["releaseNotes"], "releaseNotes", 500, out)
    version = manifest.get("version")
    if not isinstance(version, str) or len(version) > 32 or not SEMVER_RE.fullmatch(version):
        out.append(Finding("error", "version must be valid semver and at most 32 characters"))

    entry = manifest.get("entry")
    if not safe_relative(entry):
        out.append(Finding("error", "entry must be a safe package-relative POSIX path"))
    elif not (root / entry).is_file():
        out.append(Finding("error", f"entry does not exist as a regular file: {entry}"))

    icon = manifest.get("icon")
    if icon is not None:
        if not isinstance(icon, dict) or set(icon) != {"path", "sha256"} or not safe_relative(icon.get("path")):
            out.append(Finding("error", "icon must contain only a safe path and lowercase sha256"))
        else:
            icon_path = root / icon["path"]
            digest = icon.get("sha256")
            if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
                out.append(Finding("error", "icon.sha256 must be 64 lowercase hex characters"))
            elif not icon_path.is_file():
                out.append(Finding("error", f"icon file is missing: {icon['path']}"))
            elif icon_path.stat().st_size > MAX_ICON:
                out.append(Finding("error", "icon exceeds 5 MB"))
            elif hashlib.sha256(icon_path.read_bytes()).hexdigest() != digest:
                out.append(Finding("error", "icon.sha256 does not match the icon bytes"))

    permission_lists: dict[str, list[str]] = {}
    for key in ("permissions", "optionalPermissions"):
        value = manifest.get(key, [])
        if not isinstance(value, list) or len(value) > 32 or not all(valid_declaration(item) for item in value):
            out.append(Finding("error", f"{key} must contain at most 32 known permission leaves or wildcards"))
            permission_lists[key] = []
        elif len(set(value)) != len(value):
            out.append(Finding("error", f"{key} contains duplicate declarations"))
            permission_lists[key] = value
        else:
            permission_lists[key] = value
    required = expand(permission_lists["permissions"])
    optional = expand(permission_lists["optionalPermissions"])
    overlap = sorted(required & optional)
    if overlap:
        out.append(Finding("error", f"required and optional permissions overlap: {', '.join(overlap)}"))

    hosts = manifest.get("network", [])
    if not isinstance(hosts, list) or len(hosts) > 20 or len(set(hosts)) != len(hosts):
        out.append(Finding("error", "network must contain at most 20 unique hostnames"))
        hosts = []
    for host in hosts:
        if not isinstance(host, str) or not HOST_RE.fullmatch(host) or re.search(r"(?:^|\.)(?:\d+|0x[0-9a-f]*)$", host):
            out.append(Finding("error", f"invalid bare network hostname: {host!r}"))
    has_network = "network.fetch" in (required | optional)
    if bool(hosts) != has_network:
        out.append(Finding("error", "network hosts and a network.* permission must be declared together"))

    update = manifest.get("update")
    if update is not None:
        if not isinstance(update, dict) or set(update) - {"url", "urlCn"} or "url" not in update:
            out.append(Finding("error", "update must contain url and optional urlCn"))
        else:
            for key, value in update.items():
                parsed = urlparse(value) if isinstance(value, str) else None
                if not parsed or parsed.scheme != "https" or not parsed.hostname:
                    out.append(Finding("error", f"update.{key} must be an absolute HTTPS URL"))

    files = list(iter_files(root))
    if len(files) > MAX_ENTRIES:
        out.append(Finding("error", f"package has {len(files)} entries; maximum is {MAX_ENTRIES}"))
    total = 0
    for path in files:
        relative = path.relative_to(root)
        if path.is_symlink():
            out.append(Finding("error", f"symbolic link is not allowed: {relative}"))
            continue
        if relative.parts and relative.parts[0] == "__cherry":
            out.append(Finding("error", f"reserved top-level directory: {relative}"))
        total += path.stat().st_size
    if total > MAX_EXTRACTED:
        out.append(Finding("error", f"extracted files total {total} bytes; maximum is {MAX_EXTRACTED}"))

    scan_sources(root, manifest, out)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", type=Path)
    args = parser.parse_args()
    findings = validate(args.app)
    for finding in findings:
        print(f"{finding.level.upper()}: {finding.message}")
    errors = sum(item.level == "error" for item in findings)
    warnings = sum(item.level == "warning" for item in findings)
    if errors:
        print(f"FAIL: {errors} error(s), {warnings} warning(s)")
        return 1
    print(f"PASS: 0 errors, {warnings} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
