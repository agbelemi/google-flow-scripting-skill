#!/usr/bin/env python3
"""Start a new release by updating version records and creating release notes."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys

from package_utils import SemVer, read_version

ROOT = Path(__file__).resolve().parent.parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="new semantic version, for example 1.7.0")
    parser.add_argument("--date", default=date.today().isoformat(), help="release date in YYYY-MM-DD format")
    parser.add_argument("--allow-downgrade", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        current_text = read_version(ROOT)
        current = SemVer.parse(current_text)
        new = SemVer.parse(args.version)
        if new.compare(current) <= 0 and not args.allow_downgrade:
            raise ValueError(f"new version {new} must be greater than current version {current}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
            raise ValueError("--date must use YYYY-MM-DD")
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    version = str(new)
    record = ROOT / "release-history" / f"v{version}.md"
    if record.exists():
        print(f"error: release record already exists: {record}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"Would update VERSION from {current} to {version}")
        print(f"Would update SKILL.md version to {version}")
        print(f"Would create {record.relative_to(ROOT)}")
        print("Would add the version to CHANGELOG.md and release-history/index.json")
        return 0

    (ROOT / "VERSION").write_text(version + "\n", encoding="utf-8")

    skill_path = ROOT / "SKILL.md"
    skill = skill_path.read_text(encoding="utf-8")
    updated_skill, count = re.subn(r"^\*\*Version:\*\*\s*\S+", f"**Version:** {version}", skill, count=1, flags=re.M)
    if count != 1:
        print("error: could not update SKILL.md version line", file=sys.stderr)
        return 1
    skill_path.write_text(updated_skill, encoding="utf-8")

    record.write_text(
        f"# Google Flow Scripting Skill v{version}\n\n"
        f"Release date: {args.date}\n\n"
        "## Added\n\n- TODO\n\n"
        "## Changed\n\n- TODO\n\n"
        "## Fixed\n\n- TODO\n\n"
        "## Verification\n\n- TODO: record test count and source-review date.\n",
        encoding="utf-8",
    )

    changelog_path = ROOT / "CHANGELOG.md"
    changelog = changelog_path.read_text(encoding="utf-8")
    marker = "## [Unreleased]\n\nNo unreleased changes.\n"
    replacement = (
        "## [Unreleased]\n\nNo unreleased changes.\n\n"
        f"## [{version}] - {args.date}\n\n"
        "### Added\n\n- TODO\n"
    )
    if marker not in changelog:
        print("error: CHANGELOG.md has no expected Unreleased section", file=sys.stderr)
        return 1
    changelog_path.write_text(changelog.replace(marker, replacement, 1), encoding="utf-8")

    index_path = ROOT / "release-history" / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    entries = index.get("releases")
    if not isinstance(entries, list):
        print("error: release-history/index.json has invalid releases list", file=sys.stderr)
        return 1
    for entry in entries:
        if isinstance(entry, dict) and entry.get("status") == "current":
            entry["status"] = "superseded"
    entries.insert(
        0,
        {
            "version": version,
            "date": args.date,
            "record": f"release-history/v{version}.md",
            "status": "current",
        },
    )
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    print(f"Started release {version}.")
    print("Complete the TODO entries, run tests, then build the release assets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
