#!/usr/bin/env python3
"""Regression and integration tests for the validator and installer."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = ROOT / "scripts" / "validate.py"
INSTALLER = ROOT / "scripts" / "install.sh"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

EXPECTED_FAILURES = {
    "fail_backward_refs.md": "Backward references",
    "fail_token_bleed.md": "Text-bleed tokens",
    "fail_no_notext.md": "Text policy",
    "fail_text_policy_not_first.md": "Text policy",
    "fail_beats_malformed.md": "Beat timeline",
    "fail_beats_gap.md": "Beat timeline",
    "fail_beats_out_of_order.md": "Beat timeline",
    "fail_beats_duplicate.md": "Beat timeline",
    "fail_middle_segment.md": "Beat timeline",
    "fail_storyboard_video_beats.md": "Beat timeline",
    "fail_specs.md": "Unsupported specifications",
    "fail_no_audio.md": "Audio direction",
}

EXTRA_ARGS = {
    "pass_audio_disabled.md": ["--no-require-audio"],
}

GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"


def run_validator(fixture: str, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            str(FIXTURES / fixture),
            "--segment-length",
            "8",
            "--no-colour",
            *EXTRA_ARGS.get(fixture, []),
            *extra,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def failing_checks(output: str) -> list[str]:
    return [line.strip() for line in output.splitlines() if "FAIL" in line]


def main() -> int:
    passed = 0
    failed = 0

    def record(name: str, ok: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if ok:
            passed += 1
            print(f"  {GREEN}PASS{RESET}  {name}")
        else:
            failed += 1
            print(f"  {RED}FAIL{RESET}  {name}")
            if detail:
                print(f"        {detail}")

    print(f"Testing {VALIDATOR.relative_to(ROOT)} and {INSTALLER.relative_to(ROOT)}\n")

    for fixture_path in sorted(FIXTURES.glob("*.md")):
        name = fixture_path.name
        result = run_validator(name)
        if name.startswith("pass_"):
            ok = result.returncode == 0
            detail = "" if ok else (
                f"expected exit 0, got {result.returncode}; "
                f"failing checks: {'; '.join(failing_checks(result.stdout)) or 'none shown'}"
            )
        else:
            wanted = EXPECTED_FAILURES.get(name)
            ok = result.returncode == 1 and (
                not wanted or any(wanted in line for line in failing_checks(result.stdout))
            )
            if name == "fail_token_bleed.md":
                ok = ok and "#C86B3C" in result.stdout and "#abc" in result.stdout
            if name == "fail_storyboard_video_beats.md":
                ok = ok and "recognized VIDEO PROMPT contains no beat timeline" in result.stdout
            if result.returncode != 1:
                detail = f"expected exit 1, got {result.returncode}; broken input was not rejected"
            elif wanted:
                detail = f'failed, but not on expected check "{wanted}"'
            else:
                detail = "fixture has no expected check registered"
        record(name, ok, detail)

    # JSON must be pure JSON with no terminal headings mixed into stdout.
    json_result = run_validator("pass_clean.md", "--json")
    try:
        payload = json.loads(json_result.stdout)
        json_ok = (
            json_result.returncode == 0
            and payload["passed"] is True
            and payload["version"] == "1.3.1"
            and payload["settings"]["require_audio"] is True
        )
        json_detail = "" if json_ok else "JSON payload had unexpected values"
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        json_ok = False
        json_detail = f"stdout was not valid validator JSON: {exc}"
    record("json_output_is_machine_readable", json_ok, json_detail)

    with tempfile.TemporaryDirectory(prefix="flow-skill-tests-") as temp_name:
        temp = Path(temp_name)
        env = os.environ.copy()
        env["HOME"] = str(temp / "home")
        (temp / "home").mkdir()

        dry = subprocess.run(
            [str(INSTALLER), "--tool", "cursor", "--dry-run"],
            cwd=temp,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        record(
            "installer_dry_run_writes_nothing",
            dry.returncode == 0 and not (temp / ".cursor").exists(),
            dry.stderr or dry.stdout,
        )

        install = subprocess.run(
            [str(INSTALLER), "--tool", "cursor", "--force"],
            cwd=temp,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        installed = temp / ".cursor" / "skills" / "google-flow-scripting"
        install_ok = (
            install.returncode == 0
            and (installed / "SKILL.md").is_file()
            and (installed / "scripts" / "validate.py").is_file()
            and (installed / "reference" / "PLAYBOOK.md").is_file()
        )
        record("installer_creates_native_cursor_skill", install_ok, install.stderr or install.stdout)

        if install_ok:
            marker = "LOCAL MODIFICATION FOR BACKUP TEST\n"
            (installed / "SKILL.md").write_text(marker, encoding="utf-8")
            reinstall = subprocess.run(
                [str(INSTALLER), "--tool", "cursor", "--force"],
                cwd=temp,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            backups = sorted((temp / ".cursor" / "skills").glob("google-flow-scripting.bak-*"))
            backup_ok = (
                reinstall.returncode == 0
                and backups
                and (backups[-1] / "SKILL.md").read_text(encoding="utf-8") == marker
            )
            record("installer_backs_up_existing_skill", bool(backup_ok), reinstall.stderr or reinstall.stdout)
        else:
            record("installer_backs_up_existing_skill", False, "initial installation failed")

    print(f"\n{passed} passed, {failed} failed")
    if failed:
        print(f"\n{RED}Regressions detected.{RESET} Do not ship this release.")
        return 1
    print(f"{GREEN}All regression and integration checks passed.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
