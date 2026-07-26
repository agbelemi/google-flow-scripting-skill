#!/usr/bin/env python3
"""Regression, integration, update, release, and package-integrity tests."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
VALIDATOR = SCRIPTS / "validate.py"
INSTALLER = SCRIPTS / "install.py"
INSTALLER_SH = SCRIPTS / "install.sh"
UPDATER = SCRIPTS / "update.py"
UPDATER_SH = SCRIPTS / "update.sh"
CHECK_UPDATE = SCRIPTS / "check_update.py"
BUILD_RELEASE = SCRIPTS / "build_release.py"
VERIFY_PACKAGE = SCRIPTS / "verify_package.py"
STORYBOARD_GENERATOR = SCRIPTS / "generate_storyboard_prompt.py"
START_RELEASE = SCRIPTS / "start_release.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
TESTS_WORKFLOW = ROOT / ".github" / "workflows" / "tests.yml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

sys.path.insert(0, str(SCRIPTS))
from package_utils import (  # noqa: E402
    SemVer,
    build_manifest,
    find_local_modifications,
    parse_sha256sums,
    safe_extract_tar,
    safe_extract_zip,
    sha256_file,
)

GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"

# Each fixture gets a duration plus any model-specific validator arguments.
PROFILES: dict[str, tuple[int, list[str]]] = {
    "pass_ten_second.md": (10, []),
    "pass_omni_variable_intervals.md": (
        10,
        ["--surface", "flow", "--model", "omni-flash", "--mode", "text-to-video", "--beat-mode", "coverage"],
    ),
    "fail_veo_ten_second.md": (
        10,
        ["--surface", "flow", "--model", "veo-3.1-fast", "--mode", "text-to-video"],
    ),
    "pass_flow_omni_four_second.md": (
        4,
        ["--surface", "flow", "--model", "omni-flash", "--mode", "text-to-video"],
    ),
    "pass_storyboard_10s_2x2.md": (
        10,
        ["--surface", "flow", "--model", "omni-flash", "--mode", "references-to-video"],
    ),
    "fail_storyboard_10s_3x3.md": (
        10,
        ["--surface", "flow", "--model", "omni-flash", "--mode", "references-to-video"],
    ),
    "fail_reference_missing_at.md": (4, []),
    "fail_reference_space.md": (4, []),
    "fail_storyboard_contract.md": (4, []),
    "fail_omni_first_last_flow.md": (
        4,
        ["--surface", "flow", "--model", "omni-flash", "--mode", "first-last-frame"],
    ),
    "fail_omni_extend_api.md": (
        4,
        ["--surface", "gemini-api", "--model", "omni-flash", "--mode", "extend"],
    ),
    "pass_flow_veo_lite_extend_8.md": (
        8,
        ["--surface", "flow", "--model", "veo-3.1-lite", "--mode", "extend"],
    ),
    "fail_flow_quality_references.md": (
        8,
        ["--surface", "flow", "--model", "veo-3.1-quality", "--mode", "references-to-video"],
    ),
    "fail_storyboard_missing_panel.md": (10, ["--beat-mode", "off", "--no-require-audio"]),
    "fail_storyboard_duplicate_panel.md": (10, ["--beat-mode", "off", "--no-require-audio"]),
    "pass_storyboard_nine_explicit.md": (10, ["--beat-mode", "off", "--no-require-audio"]),
    "fail_bare_handle_after_declaration.md": (4, []),
    "pass_api_omni_three_second.md": (
        3,
        ["--surface", "gemini-api", "--model", "omni-flash", "--mode", "text-to-video"],
    ),
    "fail_veo_reference_four_second.md": (
        4,
        ["--surface", "gemini-api", "--model", "veo-3.1", "--mode", "references-to-video"],
    ),
}

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
    "fail_markdown_heading.md": "Beat timeline",
    "fail_reference_missing_at.md": "Reference handles",
    "fail_reference_space.md": "Reference handles",
    "fail_storyboard_contract.md": "Storyboard contract",
    "fail_veo_ten_second.md": "Model duration",
    "fail_storyboard_10s_3x3.md": "Storyboard contract",
    "fail_omni_first_last_flow.md": "Model duration",
    "fail_omni_extend_api.md": "Model duration",
    "fail_flow_quality_references.md": "Model duration",
    "fail_storyboard_missing_panel.md": "Storyboard contract",
    "fail_storyboard_duplicate_panel.md": "Storyboard contract",
    "fail_bare_handle_after_declaration.md": "Reference handles",
    "fail_veo_reference_four_second.md": "Model duration",
}

EXTRA_ARGS = {
    "pass_audio_disabled.md": ["--no-require-audio"],
}


def run(command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, check=False)


def run_validator(fixture: str, *extra: str) -> subprocess.CompletedProcess[str]:
    length, profile = PROFILES.get(fixture, (8, []))
    return run(
        [
            sys.executable,
            str(VALIDATOR),
            str(FIXTURES / fixture),
            "--segment-length",
            str(length),
            "--no-colour",
            *profile,
            *EXTRA_ARGS.get(fixture, []),
            *extra,
        ]
    )


def failing_checks(output: str) -> list[str]:
    return [line.strip() for line in output.splitlines() if "FAIL" in line]


def package_text_files() -> list[Path]:
    excluded = {".git", "__pycache__", "dist"}
    result: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in excluded for part in path.parts):
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        result.append(path)
    return result


def write_installed_manifest(target: Path, tool: str = "generic", division: str = "all") -> None:
    payload = build_manifest(target)
    payload["installation"] = {"tool": tool, "division": division, "installed_at": "2026-07-24T00:00:00Z"}
    (target / ".installed-manifest.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


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
                compact = detail.strip()
                print("        " + compact[:3000].replace("\n", "\n        "))

    print(f"Testing Google Flow Scripting Skill v{VERSION}\n")

    fixture_names = {path.name for path in FIXTURES.glob("*.md")}
    unregistered_failures = sorted(name for name in fixture_names if name.startswith("fail_") and name not in EXPECTED_FAILURES)
    record("all_fail_fixtures_registered", not unregistered_failures, ", ".join(unregistered_failures))

    for fixture_path in sorted(FIXTURES.glob("*.md")):
        name = fixture_path.name
        result = run_validator(name)
        if name.startswith("pass_"):
            ok = result.returncode == 0
            detail = "" if ok else (
                f"expected exit 0, got {result.returncode}; "
                f"failing checks: {'; '.join(failing_checks(result.stdout)) or 'none shown'}\n{result.stdout}\n{result.stderr}"
            )
        else:
            wanted = EXPECTED_FAILURES[name]
            failed_lines = failing_checks(result.stdout)
            ok = result.returncode == 1 and any(wanted in line for line in failed_lines)
            if name == "fail_token_bleed.md":
                ok = ok and "#C86B3C" in result.stdout and "#abc" in result.stdout
            if name == "fail_storyboard_video_beats.md":
                ok = ok and "recognized VIDEO PROMPT contains no beat timeline" in result.stdout
            if name == "fail_storyboard_duplicate_panel.md":
                ok = ok and "duplicate storyboard panel labels" in result.stdout
            if name == "fail_storyboard_missing_panel.md":
                ok = ok and "panel sections must appear once each" in result.stdout
            detail = "" if ok else (
                f'expected exit 1 on "{wanted}", got {result.returncode}; '
                f"failing checks: {'; '.join(failed_lines) or 'none shown'}\n{result.stdout}\n{result.stderr}"
            )
        record(name, ok, detail)

    json_result = run_validator("pass_clean.md", "--json")
    try:
        payload = json.loads(json_result.stdout)
        json_ok = (
            json_result.returncode == 0
            and payload["passed"] is True
            and payload["version"] == VERSION
            and payload["settings"]["require_audio"] is True
            and payload["settings"]["beat_mode"] == "exact"
            and payload["settings"]["mode"] == "unspecified"
        )
        json_detail = "" if json_ok else "JSON payload had unexpected values"
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        json_ok = False
        json_detail = f"stdout was not valid validator JSON: {exc}"
    record("json_output_is_machine_readable", json_ok, json_detail)

    verify = run([sys.executable, str(VERIFY_PACKAGE), str(ROOT), "--json"])
    try:
        verify_payload = json.loads(verify.stdout)
        verify_ok = verify.returncode == 0 and verify_payload.get("ok") is True
    except json.JSONDecodeError:
        verify_ok = False
    record("source_package_verifies", verify_ok, verify.stdout + verify.stderr)

    text_files = package_text_files()
    em_dash_hits = [
        str(path.relative_to(ROOT))
        for path in text_files
        if chr(0x2014) in path.read_text(encoding="utf-8")
    ]
    record("package_contains_no_em_dashes", not em_dash_hits, ", ".join(em_dash_hits[:20]))

    hard_rule = (
        "A storyboard-generation prompt must command image generation in its first sentence, "
        "declare the exact output count and layout, prohibit planning responses, and enumerate "
        "forbidden invented actions."
    )
    hard_rule_files = [
        ROOT / "SKILL.md",
        ROOT / "core" / "flow-storyboard-director.md",
        ROOT / "prompts" / "storyboard-contact-sheet.md",
        STORYBOARD_GENERATOR,
    ]
    missing_hard_rule = [str(path.relative_to(ROOT)) for path in hard_rule_files if hard_rule not in path.read_text(encoding="utf-8")]
    record("storyboard_rule_is_hard_coded", not missing_hard_rule, ", ".join(missing_hard_rule))

    index = json.loads((ROOT / "release-history" / "index.json").read_text(encoding="utf-8"))
    history_versions = [entry["version"] for entry in index["releases"]]
    records_exist = all((ROOT / "release-history" / f"v{version}.md").is_file() for version in history_versions)
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    changelog_complete = all(re.search(rf"^## \[{re.escape(version)}\]", changelog, re.M) for version in history_versions)
    record("release_history_is_complete", records_exist and changelog_complete and history_versions[0] == VERSION)

    tests_workflow_text = TESTS_WORKFLOW.read_text(encoding="utf-8") if TESTS_WORKFLOW.is_file() else ""
    tests_workflow_ok = (
        TESTS_WORKFLOW.is_file()
        and "python scripts/verify_package.py ." in tests_workflow_text
        and "python tests/run_tests.py" in tests_workflow_text
        and "bash -n scripts/install.sh" in tests_workflow_text
        and "bash -n scripts/update.sh" in tests_workflow_text
        and all(version in tests_workflow_text for version in ["3.10", "3.11", "3.12", "3.13"])
    )
    record("github_actions_tests_workflow_exists", tests_workflow_ok, str(TESTS_WORKFLOW))

    release_workflow_text = RELEASE_WORKFLOW.read_text(encoding="utf-8") if RELEASE_WORKFLOW.is_file() else ""
    release_workflow_ok = (
        RELEASE_WORKFLOW.is_file()
        and "scripts/build_release.py" in release_workflow_text
        and "SHA256SUMS" in release_workflow_text
        and "release-history/v" in release_workflow_text
        and "gh release create" in release_workflow_text
        and "attest-build-provenance" in release_workflow_text
    )
    record("github_actions_release_workflow_exists", release_workflow_ok, str(RELEASE_WORKFLOW))

    compile_result = run([sys.executable, "-m", "compileall", "-q", "scripts", "tests"])
    record("python_sources_compile", compile_result.returncode == 0, compile_result.stderr)

    for launcher in [INSTALLER_SH, UPDATER_SH]:
        shell_result = run(["bash", "-n", str(launcher)])
        record(f"{launcher.stem}_shell_syntax", shell_result.returncode == 0, shell_result.stderr)

    semver_ok = (
        SemVer.parse("v1.6.0").compare(SemVer.parse("1.5.9")) > 0
        and SemVer.parse("1.6.0-alpha.2").compare(SemVer.parse("1.6.0-alpha.10")) < 0
        and SemVer.parse("1.6.0").compare(SemVer.parse("1.6.0-rc.1")) > 0
    )
    record("semantic_version_comparison", semver_ok)

    check_result = run(
        [sys.executable, str(CHECK_UPDATE), "--current-version", VERSION, "--latest-version", "1.7.0", "--json", "--exit-code"]
    )
    try:
        check_payload = json.loads(check_result.stdout)
        check_ok = check_result.returncode == 10 and check_payload["status"] == "update_available"
    except (json.JSONDecodeError, KeyError):
        check_ok = False
    record("offline_update_check_detects_new_version", check_ok, check_result.stdout + check_result.stderr)

    dry_release = run([sys.executable, str(START_RELEASE), "1.7.0", "--date", "2026-08-01", "--dry-run"])
    record(
        "release_starter_dry_run_is_non_destructive",
        dry_release.returncode == 0 and (ROOT / "VERSION").read_text(encoding="utf-8").strip() == VERSION,
        dry_release.stdout + dry_release.stderr,
    )

    with tempfile.TemporaryDirectory(prefix="flow-skill-dynamic-") as temp_name:
        temp = Path(temp_name)

        em_dash_script = temp / "em-dash.md"
        em_dash_script.write_text(
            "SEGMENT 1.1\nVIDEO PROMPT 01\n```\n"
            "NO TEXT IN THE IMAGE: none.\nAUDIO: silence.\n"
            "0-1s: a\n1-2s: b\n2-3s: c\n3-4s: d\n"
            "A forbidden " + chr(0x2014) + " mark.\n```\n",
            encoding="utf-8",
        )
        result = run(
            [sys.executable, str(VALIDATOR), str(em_dash_script), "--segment-length", "4", "--no-colour"]
        )
        record("validator_rejects_em_dash", result.returncode == 1 and "Em dashes" in result.stdout, result.stdout)

        long_prompt = temp / "long-veo.md"
        filler = " ".join(f"detail{i}" for i in range(1100))
        long_prompt.write_text(
            "SEGMENT 1.1\nVIDEO PROMPT 01\n```\n"
            "NO TEXT IN THE IMAGE: none.\nAUDIO: room tone.\n"
            "0-1s: a\n1-2s: b\n2-3s: c\n3-4s: d\n"
            + filler
            + "\n```\n",
            encoding="utf-8",
        )
        result = run(
            [
                sys.executable,
                str(VALIDATOR),
                str(long_prompt),
                "--segment-length",
                "4",
                "--surface",
                "gemini-api",
                "--model",
                "veo-3.1",
                "--mode",
                "text-to-video",
                "--no-colour",
            ]
        )
        record(
            "validator_flags_veo_api_prompt_estimate",
            result.returncode == 1 and "Veo prompt length estimate" in result.stdout,
            result.stdout,
        )

        generated = temp / "storyboard-package.md"
        generation = run(
            [
                sys.executable,
                str(STORYBOARD_GENERATOR),
                str(ROOT / "examples" / "storyboard-spec.json"),
                "--output",
                str(generated),
            ]
        )
        generated_text = generated.read_text(encoding="utf-8") if generated.is_file() else ""
        generator_ok = (
            generation.returncode == 0
            and "INTERNAL OPERATOR NOTE" in generated_text
            and "DO NOT INCLUDE THIS CHECKLIST IN THE GENERATION PROMPT" in generated_text
            and "GENERATE THE STORYBOARD IMAGE NOW." in generated_text
            and "exactly 4" in generated_text
            and "2x2" in generated_text
            and all(handle in generated_text for handle in ["@Kwame", "@CafeLadies", "@SidewalkCafe"])
            and chr(0x2014) not in generated_text
        )
        record("storyboard_generator_creates_separated_2x2_package", generator_ok, generation.stdout + generation.stderr)

        generated_validation = run(
            [
                sys.executable,
                str(VALIDATOR),
                str(generated),
                "--segment-length",
                "10",
                "--surface",
                "flow",
                "--model",
                "omni-flash",
                "--mode",
                "references-to-video",
                "--beat-mode",
                "off",
                "--no-require-audio",
                "--no-colour",
            ]
        )
        record(
            "generated_storyboard_package_passes_validator",
            generated_validation.returncode == 0,
            generated_validation.stdout + generated_validation.stderr,
        )

        nine_spec = json.loads((ROOT / "examples" / "storyboard-spec.json").read_text(encoding="utf-8"))
        nine_spec["panels"] = [
            {"moment": f"Moment {index + 1}", "framing": "Static medium shot", "action": f"@Kwame performs authored action {index + 1}"}
            for index in range(9)
        ]
        nine_path = temp / "nine.json"
        nine_path.write_text(json.dumps(nine_spec), encoding="utf-8")
        denied = run([sys.executable, str(STORYBOARD_GENERATOR), str(nine_path)])
        nine_spec["allow_nine_panel"] = True
        nine_path.write_text(json.dumps(nine_spec), encoding="utf-8")
        accepted = run([sys.executable, str(STORYBOARD_GENERATOR), str(nine_path)])
        record(
            "nine_panel_generation_requires_explicit_opt_in",
            denied.returncode == 2 and accepted.returncode == 0 and "nine distinct frames" in accepted.stdout,
            denied.stderr + accepted.stderr,
        )

        traversal_zip = temp / "traversal.zip"
        with zipfile.ZipFile(traversal_zip, "w") as archive:
            archive.writestr("../escape.txt", "bad")
        try:
            safe_extract_zip(traversal_zip, temp / "zip-out")
            zip_rejected = False
        except ValueError:
            zip_rejected = True
        record("zip_path_traversal_is_rejected", zip_rejected)

        link_tar = temp / "link.tar"
        with tarfile.open(link_tar, "w") as archive:
            info = tarfile.TarInfo("link")
            info.type = tarfile.SYMTYPE
            info.linkname = "target"
            archive.addfile(info)
        try:
            safe_extract_tar(link_tar, temp / "tar-out")
            tar_rejected = False
        except ValueError:
            tar_rejected = True
        record("tar_links_are_rejected", tar_rejected)

    with tempfile.TemporaryDirectory(prefix="flow-skill-install-") as temp_name:
        temp = Path(temp_name)
        env = os.environ.copy()
        env["HOME"] = str(temp / "home")
        (temp / "home").mkdir()

        dry_target = temp / "dry-target"
        dry = run(
            [sys.executable, str(INSTALLER), "--tool", "cursor", "--target", str(dry_target), "--dry-run"],
            cwd=temp,
            env=env,
        )
        record("installer_dry_run_writes_nothing", dry.returncode == 0 and not dry_target.exists(), dry.stdout + dry.stderr)

        installed = temp / "installed-skill"
        install = run(
            [sys.executable, str(INSTALLER), "--tool", "cursor", "--target", str(installed), "--force"],
            cwd=temp,
            env=env,
        )
        install_ok = (
            install.returncode == 0
            and (installed / "SKILL.md").is_file()
            and (installed / "VERSION").read_text(encoding="utf-8").strip() == VERSION
            and (installed / "scripts" / "validate.py").is_file()
            and (installed / "scripts" / "check_update.py").is_file()
            and (installed / "scripts" / "update.py").is_file()
            and (installed / ".installed-manifest.json").is_file()
            and not (installed / "MANIFEST.json").exists()
            and not (installed / "tests").exists()
            and not (installed / ".github").exists()
        )
        record("installer_creates_updateable_native_skill", install_ok, install.stdout + install.stderr)

        if install_ok:
            untracked = installed / "local-note.txt"
            untracked.write_text("local", encoding="utf-8")
            modifications = find_local_modifications(installed)
            record(
                "installation_manifest_detects_untracked_files",
                any("local-note.txt (untracked)" == item for item in modifications),
                repr(modifications),
            )
            untracked.unlink()

            marker = "LOCAL MODIFICATION FOR BACKUP TEST\n"
            (installed / "SKILL.md").write_text(marker, encoding="utf-8")
            reinstall = run(
                [sys.executable, str(INSTALLER), "--tool", "cursor", "--target", str(installed), "--force"],
                cwd=temp,
                env=env,
            )
            backups = sorted(temp.glob("installed-skill.bak-*"))
            backup_ok = (
                reinstall.returncode == 0
                and backups
                and (backups[-1] / "SKILL.md").read_text(encoding="utf-8") == marker
            )
            record("installer_backs_up_existing_skill", bool(backup_ok), reinstall.stdout + reinstall.stderr)
        else:
            record("installation_manifest_detects_untracked_files", False, "initial installation failed")
            record("installer_backs_up_existing_skill", False, "initial installation failed")

    with tempfile.TemporaryDirectory(prefix="flow-skill-release-") as temp_name:
        temp = Path(temp_name)
        dist = temp / "dist"
        build = run([sys.executable, str(BUILD_RELEASE), "--output", str(dist), "--skip-tests"])
        zip_path = dist / f"google-flow-scripting-skill-v{VERSION}.zip"
        tar_path = dist / f"google-flow-scripting-skill-v{VERSION}.tar.gz"
        sums_path = dist / "SHA256SUMS"
        build_ok = build.returncode == 0 and zip_path.is_file() and tar_path.is_file() and sums_path.is_file()
        record("release_builder_creates_versioned_assets", build_ok, build.stdout + build.stderr)

        if build_ok:
            sums = parse_sha256sums(sums_path.read_text(encoding="utf-8"))
            sums_ok = sums.get(zip_path.name) == sha256_file(zip_path) and sums.get(tar_path.name) == sha256_file(tar_path)
            record("release_checksums_match_assets", sums_ok, repr(sums))

            unpacked = temp / "unpacked"
            safe_extract_zip(zip_path, unpacked)
            package_root = unpacked / f"google-flow-scripting-skill-v{VERSION}"
            package_verify = run(
                [sys.executable, str(package_root / "scripts" / "verify_package.py"), str(package_root), "--require-manifest"],
                cwd=package_root,
            )
            record("release_archive_manifest_verifies", package_verify.returncode == 0, package_verify.stdout + package_verify.stderr)

            old_target = temp / "old-install"
            shutil.copytree(package_root, old_target)
            (old_target / "MANIFEST.json").unlink(missing_ok=True)
            (old_target / "VERSION").write_text("1.5.0\n", encoding="utf-8")
            skill_text = (old_target / "SKILL.md").read_text(encoding="utf-8")
            skill_text = re.sub(r"^\*\*Version:\*\*\s*\S+", "**Version:** 1.5.0", skill_text, count=1, flags=re.M)
            (old_target / "SKILL.md").write_text(skill_text, encoding="utf-8")
            shutil.rmtree(old_target / "tests", ignore_errors=True)
            shutil.rmtree(old_target / ".github", ignore_errors=True)
            (old_target / "CONTRIBUTING.md").unlink(missing_ok=True)
            write_installed_manifest(old_target, tool="generic", division="all")

            update = run(
                [
                    sys.executable,
                    str(UPDATER),
                    "--archive",
                    str(zip_path),
                    "--target",
                    str(old_target),
                    "--yes",
                    "--skip-tests",
                    "--force",
                ]
            )
            update_backups = sorted(temp.glob("old-install.bak-*"))
            update_ok = (
                update.returncode == 0
                and (old_target / "VERSION").read_text(encoding="utf-8").strip() == VERSION
                and update_backups
                and (update_backups[-1] / "VERSION").read_text(encoding="utf-8").strip() == "1.5.0"
                and (old_target / ".installed-manifest.json").is_file()
                and not (old_target / "MANIFEST.json").exists()
            )
            record("local_release_update_is_verified_and_backed_up", bool(update_ok), update.stdout + update.stderr)

            git_target = temp / "git-install"
            shutil.copytree(old_target, git_target)
            (git_target / ".git").mkdir()
            git_refusal = run(
                [sys.executable, str(UPDATER), "--archive", str(zip_path), "--target", str(git_target), "--yes", "--reinstall"]
            )
            record(
                "updater_refuses_git_working_tree",
                git_refusal.returncode == 2 and "Git working tree" in git_refusal.stderr,
                git_refusal.stdout + git_refusal.stderr,
            )
        else:
            record("release_checksums_match_assets", False, "release build failed")
            record("release_archive_manifest_verifies", False, "release build failed")
            record("local_release_update_is_verified_and_backed_up", False, "release build failed")
            record("updater_refuses_git_working_tree", False, "release build failed")

    print(f"\n{passed} passed, {failed} failed")
    if failed:
        print(f"\n{RED}Regressions detected.{RESET} Do not ship this release.")
        return 1
    print(f"{GREEN}All regression, integration, update, release, and integrity checks passed.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
