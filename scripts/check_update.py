#!/usr/bin/env python3
"""Check whether a newer GitHub Release is available."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from package_utils import DEFAULT_REPOSITORY, SemVer, fetch_json, read_version, release_api_url

ROOT = Path(__file__).resolve().parent.parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPOSITORY, help="GitHub repository in owner/name form")
    parser.add_argument("--current-version", help="override the local VERSION file")
    parser.add_argument("--latest-version", help="compare against this version without using the network")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="return exit code 10 when an update is available; successful checks otherwise return 0",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        current_text = args.current_version or read_version(ROOT)
        current = SemVer.parse(current_text)
        release_url = None
        if args.latest_version:
            latest_text = str(SemVer.parse(args.latest_version))
        else:
            release_url = release_api_url(args.repo)
            release = fetch_json(release_url)
            tag = release.get("tag_name")
            if not isinstance(tag, str):
                raise RuntimeError("latest release response has no tag_name")
            latest_text = str(SemVer.parse(tag))
        latest = SemVer.parse(latest_text)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"Update check failed: {exc}", file=sys.stderr)
        return 2

    comparison = current.compare(latest)
    if comparison < 0:
        status = "update_available"
    elif comparison == 0:
        status = "up_to_date"
    else:
        status = "local_newer"

    payload = {
        "ok": True,
        "repository": args.repo,
        "current_version": str(current),
        "latest_version": str(latest),
        "status": status,
        "release_api_url": release_url,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Installed version: {current}")
        print(f"Latest version:    {latest}")
        if status == "update_available":
            print("Update available.")
            print("Run: python scripts/update.py")
        elif status == "up_to_date":
            print("This installation is up to date.")
        else:
            print("The local version is newer than the latest published release.")

    return 10 if args.exit_code and status == "update_available" else 0


if __name__ == "__main__":
    sys.exit(main())
