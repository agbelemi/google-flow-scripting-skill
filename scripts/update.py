#!/usr/bin/env python3
"""Safely update an installed Skill from a verified GitHub Release."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from package_utils import (
    DEFAULT_REPOSITORY,
    SemVer,
    asset_download_url,
    build_manifest,
    download_file,
    fetch_json,
    find_local_modifications,
    find_package_root,
    iter_package_files,
    parse_sha256sums,
    read_version,
    release_api_url,
    safe_extract_tar,
    safe_extract_zip,
    sha256_file,
)

ROOT = Path(__file__).resolve().parent.parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPOSITORY, help="GitHub repository in owner/name form")
    parser.add_argument("--version", help="install this version instead of the latest release")
    parser.add_argument("--archive", type=Path, help="use a local release archive instead of the network")
    parser.add_argument("--sha256", help="expected SHA-256 for a local archive")
    parser.add_argument("--target", type=Path, default=ROOT, help="installed Skill directory")
    parser.add_argument("--yes", action="store_true", help="confirm replacement without prompting")
    parser.add_argument("--force", action="store_true", help="replace even when local modifications are detected")
    parser.add_argument("--allow-downgrade", action="store_true")
    parser.add_argument("--reinstall", action="store_true", help="reinstall the same version after verification")
    parser.add_argument("--allow-git-tree", action="store_true", help="allow replacing a Git working tree")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-backups", type=int, default=3)
    parser.add_argument("--skip-tests", action="store_true", help="skip release tests; not recommended")
    return parser


def load_installation_profile(target: Path) -> tuple[str, str]:
    path = target / ".installed-manifest.json"
    if not path.is_file():
        return "generic", "all"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "generic", "all"
    installation = payload.get("installation", {})
    if not isinstance(installation, dict):
        return "generic", "all"
    tool = installation.get("tool") if isinstance(installation.get("tool"), str) else "generic"
    division = installation.get("division") if installation.get("division") in {"all", "core", "formats"} else "all"
    return tool, division


def include_path(relative: Path, division: str) -> bool:
    first = relative.parts[0] if relative.parts else ""
    if first in {"tests", ".github"} or relative.name in {"CONTRIBUTING.md", "MANIFEST.json", ".installed-manifest.json"}:
        return False
    if first == "core":
        return division in {"all", "core", "formats"}
    if first == "formats":
        return division in {"all", "formats"}
    return True


def stage_installation(package_root: Path, destination: Path, tool: str, division: str) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for path in iter_package_files(package_root):
        relative = path.relative_to(package_root)
        if not include_path(relative, division):
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    manifest = build_manifest(destination)
    manifest["installation"] = {
        "tool": tool,
        "division": division,
        "installed_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "updated_from": "github-release-or-local-archive",
    }
    (destination / ".installed-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def prune_backups(target: Path, keep: int) -> None:
    backups = sorted(target.parent.glob(target.name + ".bak-*"), key=lambda path: path.stat().st_mtime, reverse=True)
    for backup in backups[keep:]:
        shutil.rmtree(backup, ignore_errors=True)


def resolve_network_archive(repository: str, requested_version: str | None, temp: Path) -> tuple[Path, str]:
    release = fetch_json(release_api_url(repository, requested_version))
    tag = release.get("tag_name")
    if not isinstance(tag, str):
        raise RuntimeError("release response has no tag_name")
    version = str(SemVer.parse(tag))
    archive_name = f"google-flow-scripting-skill-v{version}.zip"
    archive_url = asset_download_url(release, archive_name)
    sums_url = asset_download_url(release, "SHA256SUMS")
    if not archive_url:
        raise RuntimeError(f"release asset is missing: {archive_name}")
    if not sums_url:
        raise RuntimeError("release asset is missing: SHA256SUMS")

    archive = temp / archive_name
    sums = temp / "SHA256SUMS"
    download_file(archive_url, archive)
    download_file(sums_url, sums)
    expected = parse_sha256sums(sums.read_text(encoding="utf-8")).get(archive_name)
    if not expected:
        raise RuntimeError(f"SHA256SUMS has no entry for {archive_name}")
    actual = sha256_file(archive)
    if actual != expected:
        raise RuntimeError(f"archive checksum mismatch: expected {expected}, got {actual}")
    return archive, version


def extract_archive(archive: Path, destination: Path) -> Path:
    name = archive.name.lower()
    if name.endswith(".zip"):
        safe_extract_zip(archive, destination)
    elif name.endswith((".tar.gz", ".tgz", ".tar")):
        safe_extract_tar(archive, destination)
    else:
        raise ValueError("release archive must be .zip, .tar.gz, .tgz, or .tar")
    return find_package_root(destination)


def run_command(command: list[str], cwd: Path, label: str) -> None:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        detail = (result.stdout + "\n" + result.stderr).strip()
        raise RuntimeError(f"{label} failed\n{detail}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    target = args.target.expanduser().resolve()
    if args.keep_backups < 1:
        print("error: --keep-backups must be one or greater", file=sys.stderr)
        return 2
    if not target.is_dir() or not (target / "VERSION").is_file():
        print(f"error: target is not an installed Skill: {target}", file=sys.stderr)
        return 2
    if (target / ".git").exists() and not args.allow_git_tree:
        print("error: target is a Git working tree. Use git pull for source clones.", file=sys.stderr)
        print("Pass --allow-git-tree only when you intentionally want release files to replace it.", file=sys.stderr)
        return 2

    try:
        current_version = read_version(target)
        current = SemVer.parse(current_version)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    modifications = find_local_modifications(target)
    if modifications and not args.force:
        print("Local modifications or an untracked old installation were detected:", file=sys.stderr)
        for item in modifications[:20]:
            print(f"  - {item}", file=sys.stderr)
        print("A backup will always be made, but use --force to confirm replacement.", file=sys.stderr)
        return 2

    try:
        with tempfile.TemporaryDirectory(prefix="flow-skill-update-") as temp_name:
            temp = Path(temp_name)
            if args.archive:
                archive = args.archive.expanduser().resolve()
                if not archive.is_file():
                    raise FileNotFoundError(f"archive not found: {archive}")
                if args.sha256 and sha256_file(archive) != args.sha256.lower():
                    raise RuntimeError("local archive checksum does not match --sha256")
                expected_version = str(SemVer.parse(args.version)) if args.version else None
            else:
                archive, expected_version = resolve_network_archive(args.repo, args.version, temp)

            extracted = temp / "extracted"
            extracted.mkdir()
            package_root = extract_archive(archive, extracted)
            new_version = read_version(package_root)
            new = SemVer.parse(new_version)
            if expected_version and new_version != expected_version:
                raise RuntimeError(f"archive version {new_version} does not match requested {expected_version}")
            if new.compare(current) < 0 and not args.allow_downgrade:
                raise RuntimeError(f"refusing to downgrade from {current} to {new}; use --allow-downgrade")
            if new.compare(current) == 0 and not args.reinstall:
                print(f"Version {new} is already installed. Pass --reinstall to replace it after verification.")
                return 0

            run_command(
                [sys.executable, str(package_root / "scripts" / "verify_package.py"), str(package_root), "--require-manifest"],
                package_root,
                "package verification",
            )
            if not args.skip_tests:
                run_command([sys.executable, str(package_root / "tests" / "run_tests.py")], package_root, "release tests")

            tool, division = load_installation_profile(target)
            print(f"Installed version: {current}")
            print(f"New version:       {new}")
            print(f"Target:            {target}")
            print(f"Profile:           {tool}, division {division}")
            print("Verification:      passed")

            if args.dry_run:
                print("Dry run complete. No files were changed.")
                return 0
            if not args.yes:
                if not sys.stdin.isatty():
                    raise RuntimeError("confirmation required in non-interactive mode; pass --yes")
                answer = input("Back up the current installation and apply this update? [y/N]: ").strip().lower()
                if answer not in {"y", "yes"}:
                    print("Cancelled. Nothing was written.")
                    return 0

            stage_parent = Path(tempfile.mkdtemp(prefix=".flow-update-", dir=target.parent))
            stage = stage_parent / target.name
            backup = target.with_name(target.name + f".bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{os.getpid()}")
            replacement_started = False
            try:
                stage_installation(package_root, stage, tool, division)
                target.replace(backup)
                replacement_started = True
                stage.replace(target)
                prune_backups(target, args.keep_backups)
            except Exception:
                if replacement_started and backup.exists():
                    if target.exists():
                        shutil.rmtree(target, ignore_errors=True)
                    backup.replace(target)
                raise
            finally:
                shutil.rmtree(stage_parent, ignore_errors=True)

            print(f"Updated to version {new}.")
            print(f"Previous installation backed up to: {backup}")
            print("Restart the AI tool or begin a new session so it reloads the Skill.")
            return 0
    except (FileNotFoundError, ValueError, RuntimeError, OSError) as exc:
        print(f"Update failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
