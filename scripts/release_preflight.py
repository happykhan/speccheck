#!/usr/bin/env python3
"""Check local and public release state before running the Release workflow.

This script is deliberately read-only. It does not create tags, releases, PyPI
uploads, or Docker images. Use it immediately before the manual GitHub Actions
Release workflow.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

try:  # pragma: no cover - Python 3.11+ path in CI/local Pixi env.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback.
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
GITHUB_API = "https://api.github.com/repos/happykhan/speccheck"
PYPI_API = "https://pypi.org/pypi/speccheck-qc/json"
DOCKER_API = "https://hub.docker.com/v2/repositories/happykhan/speccheck/tags?page_size=100"
PAGES_URL = "https://happykhan.github.io/speccheck/"


@dataclass
class CheckResult:
    label: str
    ok: bool
    detail: str
    warning: bool = False


def read_project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def read_pixi_version() -> str:
    with (ROOT / "pixi.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def fetch_json(url: str):
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def url_status(url: str) -> int:
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, timeout=20) as response:
        return int(response.status)


def git_clean() -> CheckResult:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        return CheckResult("git tree", False, "working tree has uncommitted changes")
    return CheckResult("git tree", True, "working tree clean")


def metadata_consistent(version: str) -> list[CheckResult]:
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    zenodo = (ROOT / ".zenodo.json").read_text(encoding="utf-8")
    checks = [
        CheckResult(
            "pyproject version",
            read_project_version() == version,
            f"pyproject.toml version is {read_project_version()}",
        ),
        CheckResult(
            "pixi version",
            read_pixi_version() == version,
            f"pixi.toml version is {read_pixi_version()}",
        ),
        CheckResult(
            "CITATION version",
            f"version: {version}" in citation,
            f"CITATION.cff {'contains' if f'version: {version}' in citation else 'lacks'} {version}",
        ),
        CheckResult(
            "CITATION artifact",
            f"/releases/tag/v{version}" in citation,
            f"CITATION.cff {'points to' if f'/releases/tag/v{version}' in citation else 'does not point to'} v{version}",
        ),
        CheckResult(
            "CHANGELOG entry",
            f"## {version} -" in changelog,
            f"CHANGELOG.md {'contains' if f'## {version} -' in changelog else 'lacks'} {version}",
        ),
        CheckResult(
            "Zenodo metadata",
            f"Version {version}" in zenodo or f"version {version}" in zenodo,
            f".zenodo.json {'mentions' if (f'Version {version}' in zenodo or f'version {version}' in zenodo) else 'does not mention'} {version}",
        ),
    ]
    return checks


def github_release_state(version: str) -> list[CheckResult]:
    tag = f"v{version}"
    tags = fetch_json(f"{GITHUB_API}/tags?per_page=100")
    releases = fetch_json(f"{GITHUB_API}/releases?per_page=100")
    tag_names = {item["name"] for item in tags}
    release_tags = {item["tag_name"] for item in releases}
    return [
        CheckResult(
            "GitHub tag availability",
            tag not in tag_names,
            f"{tag} {'already exists' if tag in tag_names else 'is available'}",
        ),
        CheckResult(
            "GitHub release availability",
            tag not in release_tags,
            f"release {tag} {'already exists' if tag in release_tags else 'is available'}",
        ),
    ]


def pypi_state(version: str) -> CheckResult:
    data = fetch_json(PYPI_API)
    releases = set(data.get("releases", {}))
    current = data.get("info", {}).get("version", "unknown")
    return CheckResult(
        "PyPI version availability",
        version not in releases,
        f"PyPI current={current}; {version} {'already exists' if version in releases else 'is available'}",
    )


def docker_state(version: str) -> CheckResult:
    data = fetch_json(DOCKER_API)
    tags = {item["name"]: item.get("last_updated", "unknown") for item in data.get("results", [])}
    if version in tags:
        return CheckResult(
            "Docker tag state",
            True,
            f"Docker tag {version} already exists from {tags[version]}; release will overwrite the mutable tag",
            warning=True,
        )
    return CheckResult("Docker tag state", True, f"Docker tag {version} is not present")


def pages_state() -> CheckResult:
    try:
        status = url_status(PAGES_URL)
    except urllib.error.URLError as exc:
        return CheckResult("GitHub Pages", False, f"{PAGES_URL} not reachable: {exc}")
    return CheckResult("GitHub Pages", status == 200, f"{PAGES_URL} returned HTTP {status}")


def print_result(result: CheckResult) -> None:
    if result.ok and result.warning:
        prefix = "WARN"
    elif result.ok:
        prefix = "PASS"
    else:
        prefix = "FAIL"
    print(f"{prefix:4} {result.label}: {result.detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "version",
        nargs="?",
        default=read_project_version(),
        help="Release version to check. Defaults to pyproject.toml version.",
    )
    args = parser.parse_args(argv)

    checks: list[CheckResult] = [git_clean()]
    checks.extend(metadata_consistent(args.version))
    checks.extend(github_release_state(args.version))
    checks.append(pypi_state(args.version))
    checks.append(docker_state(args.version))
    checks.append(pages_state())

    for check in checks:
        print_result(check)

    failures = [check for check in checks if not check.ok]
    if failures:
        print(f"\nRelease preflight failed: {len(failures)} blocking check(s).", file=sys.stderr)
        return 1
    print("\nRelease preflight passed. It is safe to run the manual Release workflow.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
