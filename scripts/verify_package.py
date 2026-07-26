#!/usr/bin/env python3
"""Verify package structure, history, version consistency, manifests, and text rules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from package_utils import SemVer, iter_package_files, read_version, verify_manifest

HARD_STORYBOARD_RULE = (
    "A storyboard-generation prompt must command image generation in its first sentence, "
    "declare the exact output count and layout, prohibit planning responses, and enumerate "
    "forbidden invented actions."
)
FIRST_STORYBOARD_SENTENCE = "GENERATE THE STORYBOARD IMAGE NOW."

REQUIRED_FILES = {
    "VERSION",
    "README.md",
    "SKILL.md",
    "CHANGELOG.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "SUPPORT.md",
    "CODE_OF_CONDUCT.md",
    "divisions.json",
    "scripts/validate.py",
    "scripts/install.py",
    "scripts/install.sh",
    "scripts/install.ps1",
    "scripts/check_update.py",
    "scripts/update.py",
    "scripts/update.sh",
    "scripts/update.ps1",
    "scripts/build_release.py",
    "scripts/start_release.py",
    "scripts/verify_package.py",
    "scripts/generate_storyboard_prompt.py",
    "prompts/storyboard-contact-sheet.md",
    "reference/UPDATE-GUIDE.md",
    "reference/RELEASE-PROCESS.md",
    "reference/VERSIONING.md",
    "reference/MIGRATING.md",
    "release-history/README.md",
    "release-history/index.json",
    ".github/workflows/tests.yml",
    ".github/workflows/release.yml",
}

HARD_RULE_FILES = {
    "SKILL.md",
    "core/flow-storyboard-director.md",
    "prompts/storyboard-contact-sheet.md",
    "scripts/generate_storyboard_prompt.py",
}

FIRST_SENTENCE_FILES = {
    "SKILL.md",
    "core/flow-storyboard-director.md",
    "prompts/storyboard-contact-sheet.md",
    "scripts/generate_storyboard_prompt.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--require-manifest", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_release_history(root: Path, version: str, changelog_text: str) -> list[str]:
    errors: list[str] = []
    index_path = root / "release-history" / "index.json"
    if not index_path.is_file():
        return ["missing release-history/index.json"]

    try:
        index = json.loads(text(index_path))
    except json.JSONDecodeError as exc:
        return [f"release-history/index.json is invalid: {exc}"]

    if index.get("schema_version") != 1:
        errors.append("release-history/index.json schema_version must be 1")
    entries = index.get("releases")
    if not isinstance(entries, list) or not entries:
        return errors + ["release-history/index.json has no release entries"]

    seen: set[str] = set()
    parsed_versions: list[SemVer] = []
    current_entries = 0
    for position, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"release-history entry {position + 1} is not an object")
            continue
        entry_version = entry.get("version")
        date = entry.get("date")
        record_name = entry.get("record")
        status = entry.get("status")
        if not isinstance(entry_version, str):
            errors.append(f"release-history entry {position + 1} has no valid version")
            continue
        try:
            parsed = SemVer.parse(entry_version)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        parsed_versions.append(parsed)
        if entry_version in seen:
            errors.append(f"duplicate release-history version: {entry_version}")
        seen.add(entry_version)
        if status == "current":
            current_entries += 1
            if entry_version != version:
                errors.append(f"release {entry_version} is marked current instead of {version}")
        if not isinstance(date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            errors.append(f"release {entry_version} has an invalid date")
        expected_record = f"release-history/v{entry_version}.md"
        if record_name != expected_record:
            errors.append(f"release {entry_version} record must be {expected_record}")
        record = root / expected_record
        if not record.is_file():
            errors.append(f"missing release record: {expected_record}")
            continue
        record_text = text(record)
        expected_heading = f"# Google Flow Scripting Skill v{entry_version}"
        if not record_text.startswith(expected_heading + "\n"):
            errors.append(f"{expected_record} has the wrong heading")
        if f"Release date: {date}" not in record_text:
            errors.append(f"{expected_record} date does not match the index")
        if re.search(r"\bTODO\b", record_text):
            errors.append(f"{expected_record} contains an unfinished TODO")
        if not re.search(rf"^## \[{re.escape(entry_version)}\]", changelog_text, re.M):
            errors.append(f"CHANGELOG.md has no [{entry_version}] section")

    if current_entries != 1:
        errors.append(f"release-history must contain exactly one current entry, found {current_entries}")
    if version not in seen:
        errors.append(f"release-history/index.json has no {version} entry")
    for left, right in zip(parsed_versions, parsed_versions[1:]):
        if left.compare(right) <= 0:
            errors.append("release-history entries must be ordered newest to oldest")
            break
    return errors


def check(root: Path, require_manifest: bool) -> list[str]:
    errors: list[str] = []
    try:
        version = read_version(root)
    except (FileNotFoundError, ValueError) as exc:
        return [str(exc)]

    missing = sorted(relative for relative in REQUIRED_FILES if not (root / relative).is_file())
    if missing:
        errors.append("missing required files: " + ", ".join(missing))

    skill = root / "SKILL.md"
    if skill.is_file():
        match = re.search(r"^\*\*Version:\*\*\s*([^\s]+)", text(skill), re.M)
        if not match:
            errors.append("SKILL.md has no version line")
        elif match.group(1) != version:
            errors.append(f"SKILL.md version {match.group(1)} does not match VERSION {version}")

    readme = root / "README.md"
    if readme.is_file() and f"Version {version} highlights" not in text(readme):
        errors.append(f"README.md has no Version {version} highlights section")

    divisions = root / "divisions.json"
    if divisions.is_file():
        try:
            payload = json.loads(text(divisions))
            if payload.get("version") != version:
                errors.append("divisions.json version does not match VERSION")
        except json.JSONDecodeError as exc:
            errors.append(f"divisions.json is invalid: {exc}")

    changelog = root / "CHANGELOG.md"
    changelog_text = text(changelog) if changelog.is_file() else ""
    if changelog.is_file() and not re.search(rf"^## \[{re.escape(version)}\]", changelog_text, re.M):
        errors.append(f"CHANGELOG.md has no [{version}] section")
    errors.extend(check_release_history(root, version, changelog_text))

    for relative in HARD_RULE_FILES:
        path = root / relative
        if path.is_file() and HARD_STORYBOARD_RULE not in text(path):
            errors.append(f"{relative} does not hard-code the storyboard rule")
    for relative in FIRST_SENTENCE_FILES:
        path = root / relative
        if path.is_file() and FIRST_STORYBOARD_SENTENCE not in text(path):
            errors.append(f"{relative} does not contain the exact storyboard first sentence")

    em_dash_hits: list[str] = []
    cache_hits: list[str] = []
    for path in iter_package_files(root):
        relative = path.relative_to(root).as_posix()
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            cache_hits.append(relative)
        try:
            content = text(path)
        except UnicodeDecodeError:
            continue
        if chr(0x2014) in content:
            em_dash_hits.append(relative)
    if em_dash_hits:
        errors.append("em dash found in: " + ", ".join(em_dash_hits[:20]))
    if cache_hits:
        errors.append("generated cache files found in package: " + ", ".join(cache_hits[:20]))

    tests_workflow = root / ".github" / "workflows" / "tests.yml"
    if tests_workflow.is_file():
        workflow = text(tests_workflow)
        for command in (
            "python scripts/verify_package.py .",
            "python tests/run_tests.py",
            "bash -n scripts/install.sh",
            "bash -n scripts/update.sh",
        ):
            if command not in workflow:
                errors.append(f"tests workflow is missing: {command}")

    release_workflow = root / ".github" / "workflows" / "release.yml"
    if release_workflow.is_file():
        workflow = text(release_workflow)
        for required in ("tags:", "scripts/build_release.py", "SHA256SUMS", "release-history/v"):
            if required not in workflow:
                errors.append(f"release workflow is missing required content: {required}")

    manifest = root / "MANIFEST.json"
    if require_manifest and not manifest.is_file():
        errors.append("MANIFEST.json is required but missing")
    if manifest.is_file():
        errors.extend(verify_manifest(root))

    return errors


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.path.resolve()
    errors = check(root, args.require_manifest)
    payload = {"ok": not errors, "path": str(root), "errors": errors}
    if args.json:
        print(json.dumps(payload, indent=2))
    elif errors:
        print("Package verification failed:")
        for error in errors:
            print(f"  - {error}")
    else:
        print(f"Package verification passed: {root}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
