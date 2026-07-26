#!/usr/bin/env python3
"""Build verified ZIP and tar.gz release assets with checksums."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from package_utils import copy_package_tree, read_version, sha256_file, write_manifest

ROOT = Path(__file__).resolve().parent.parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--skip-tests", action="store_true")
    return parser


def run(command: list[str], label: str) -> None:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        print(f"{label} failed", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(label)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        version = read_version(ROOT)
        run([sys.executable, str(ROOT / "scripts" / "verify_package.py"), str(ROOT)], "source verification")
        if not args.skip_tests:
            run([sys.executable, str(ROOT / "tests" / "run_tests.py")], "tests")

        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=True)
        for old in output.glob("google-flow-scripting-skill-v*"):
            if old.is_file():
                old.unlink()
            elif old.is_dir():
                shutil.rmtree(old)
        sums_path = output / "SHA256SUMS"
        sums_path.unlink(missing_ok=True)

        package_name = f"google-flow-scripting-skill-v{version}"
        with tempfile.TemporaryDirectory(prefix="flow-release-") as temp_name:
            temp = Path(temp_name)
            stage = temp / package_name
            copy_package_tree(ROOT, stage, include_tests=True)
            write_manifest(stage)
            run(
                [sys.executable, str(stage / "scripts" / "verify_package.py"), str(stage), "--require-manifest"],
                "staged package verification",
            )

            zip_base = output / package_name
            zip_path = Path(shutil.make_archive(str(zip_base), "zip", root_dir=temp, base_dir=package_name))
            tar_path = Path(shutil.make_archive(str(zip_base), "gztar", root_dir=temp, base_dir=package_name))

        assets = [zip_path, tar_path]
        lines = [f"{sha256_file(path)}  {path.name}" for path in assets]
        sums_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        print(f"Built release {version}:")
        for path in [*assets, sums_path]:
            print(f"  {path}")
        return 0
    except (FileNotFoundError, ValueError, RuntimeError, OSError) as exc:
        print(f"Release build failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
