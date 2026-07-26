#!/usr/bin/env python3
"""Cross-platform installer for the Google Flow Scripting Skill."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from package_utils import build_manifest, iter_package_files, read_version

ROOT = Path(__file__).resolve().parent.parent
SKILL_NAME = "google-flow-scripting"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", choices=["claude-code", "cursor", "windsurf", "generic"])
    parser.add_argument("--division", choices=["all", "core", "formats"], default="all")
    parser.add_argument("--target", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--install-subagents", action="store_true")
    parser.add_argument("--keep-backups", type=int, default=3)
    return parser


def choose_tool() -> str:
    if not sys.stdin.isatty():
        raise RuntimeError("--tool is required in non-interactive mode")
    print("Where should this Skill be installed?")
    print("  1) Claude Code   (global native Skill)")
    print("  2) Cursor        (project native Skill)")
    print("  3) Windsurf      (project native Skill)")
    print("  4) Generic       (portable Skill folder)")
    choice = input("Choice [1]: ").strip() or "1"
    mapping = {"1": "claude-code", "2": "cursor", "3": "windsurf", "4": "generic"}
    if choice not in mapping:
        raise RuntimeError("invalid tool choice")
    return mapping[choice]


def tool_profile(tool: str, cwd: Path) -> tuple[Path, str, str]:
    home = Path.home()
    profiles = {
        "claude-code": (home / ".claude" / "skills" / SKILL_NAME, "global", f"/{SKILL_NAME}"),
        "cursor": (cwd / ".cursor" / "skills" / SKILL_NAME, "project-local", f"/{SKILL_NAME}"),
        "windsurf": (cwd / ".windsurf" / "skills" / SKILL_NAME, "project-local", f"@{SKILL_NAME}"),
        "generic": (cwd / "flow-skill" / SKILL_NAME, "project-local portable folder", "open SKILL.md in your agent"),
    }
    return profiles[tool]


def include_path(relative: Path, division: str) -> bool:
    first = relative.parts[0] if relative.parts else ""
    if first in {"tests", ".github"} or relative.name in {"CONTRIBUTING.md", "MANIFEST.json", ".installed-manifest.json"}:
        return False
    if first == "core":
        return division in {"all", "core", "formats"}
    if first == "formats":
        return division in {"all", "formats"}
    return True


def copy_installation(source: Path, destination: Path, division: str) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for path in iter_package_files(source):
        relative = path.relative_to(source)
        if not include_path(relative, division):
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def write_installation_manifest(destination: Path, tool: str, division: str) -> None:
    payload = build_manifest(destination)
    payload["installation"] = {
        "tool": tool,
        "division": division,
        "installed_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
    }
    (destination / ".installed-manifest.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def prune_backups(destination: Path, keep: int) -> None:
    if keep < 0:
        return
    backups = sorted(destination.parent.glob(destination.name + ".bak-*"), key=lambda path: path.stat().st_mtime, reverse=True)
    for backup in backups[keep:]:
        if backup.is_dir():
            shutil.rmtree(backup)
        else:
            backup.unlink()


def install_subagents(source: Path, force: bool) -> None:
    destination = Path.home() / ".claude" / "agents"
    destination.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    for directory in (source / "core", source / "formats"):
        for path in sorted(directory.glob("*.md")):
            target = destination / path.name
            if target.exists():
                if not force and not sys.stdin.isatty():
                    raise RuntimeError(f"subagent exists at {target}; use --force")
                backup = target.with_name(target.name + f".bak-{stamp}-{os.getpid()}")
                target.replace(backup)
            shutil.copy2(path, target)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.keep_backups < 1:
        print("error: --keep-backups must be one or greater", file=sys.stderr)
        return 2

    try:
        tool = args.tool or choose_tool()
        default_destination, scope, invocation = tool_profile(tool, Path.cwd())
        destination = (args.target or default_destination).expanduser().resolve()
        version = read_version(ROOT)
    except (RuntimeError, FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.install_subagents and tool != "claude-code":
        print("error: --install-subagents is available only for --tool claude-code", file=sys.stderr)
        return 2

    print()
    print(f"Installing version:          {version}")
    print(f"Destination:                 {destination}")
    print(f"Scope:                       {scope}")
    print(f"Requested division:          {args.division}")
    if args.division == "formats":
        print("Dependency resolution:       core included because formats require it")
    if args.install_subagents:
        print("Claude subagents:             enabled")
    if args.dry_run:
        print("Mode:                         dry run; nothing will be written")

    if args.dry_run:
        if destination.exists():
            print("Existing destination would be backed up before replacement.")
        print("Dry run complete.")
        return 0

    if destination.exists() and not args.force:
        if not sys.stdin.isatty():
            print("error: destination exists; use --force for non-interactive replacement", file=sys.stderr)
            return 2
        answer = input("A Skill already exists. Back it up and replace it? [y/N]: ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Cancelled. Nothing was written.")
            return 0

    destination.parent.mkdir(parents=True, exist_ok=True)
    stage_parent = Path(tempfile.mkdtemp(prefix=".flow-install-", dir=destination.parent))
    stage = stage_parent / SKILL_NAME
    backup: Path | None = None
    try:
        copy_installation(ROOT, stage, args.division)
        write_installation_manifest(stage, tool, args.division)

        if destination.exists():
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = destination.with_name(destination.name + f".bak-{stamp}-{os.getpid()}")
            destination.replace(backup)
        stage.replace(destination)

        if args.install_subagents:
            install_subagents(ROOT, args.force)
        prune_backups(destination, args.keep_backups)
    except Exception as exc:
        if destination.exists() and backup is not None and backup.exists():
            shutil.rmtree(destination, ignore_errors=True)
            backup.replace(destination)
        print(f"error: installation failed: {exc}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(stage_parent, ignore_errors=True)

    print()
    print(f"Installed {SKILL_NAME} version {version}.")
    if backup is not None:
        print(f"Previous installation backed up to: {backup}")
    if args.install_subagents:
        print(f"Claude specialist subagents installed to: {Path.home() / '.claude' / 'agents'}")
    print(f"Invoke with: {invocation}")
    print()
    print("Check for future updates with:")
    print(f"  python {destination / 'scripts' / 'check_update.py'}")
    print("Apply a verified release update with:")
    print(f"  python {destination / 'scripts' / 'update.py'}")
    print("Restart the AI tool or begin a new session after updating.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
