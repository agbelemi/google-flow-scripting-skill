#!/usr/bin/env python3
"""Shared package, version, manifest, archive, and network helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tarfile
import tempfile
from typing import Iterable, Iterator
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import zipfile

DEFAULT_REPOSITORY = "agbelemi/google-flow-scripting-skill"
USER_AGENT = "google-flow-scripting-skill-updater"
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)

EXCLUDED_PARTS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "dist",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".DS_Store"}


@dataclass(frozen=True)
class SemVer:
    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()
    build: tuple[str, ...] = ()

    @classmethod
    def parse(cls, value: str) -> "SemVer":
        clean = value.strip()
        if clean.startswith("v"):
            clean = clean[1:]
        match = SEMVER_PATTERN.fullmatch(clean)
        if not match:
            raise ValueError(f"invalid semantic version: {value!r}")
        prerelease = tuple(match.group(4).split(".")) if match.group(4) else ()
        build = tuple(match.group(5).split(".")) if match.group(5) else ()
        return cls(int(match.group(1)), int(match.group(2)), int(match.group(3)), prerelease, build)

    def __str__(self) -> str:
        value = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            value += "-" + ".".join(self.prerelease)
        if self.build:
            value += "+" + ".".join(self.build)
        return value

    def precedence_key(self) -> tuple[object, ...]:
        if not self.prerelease:
            pre: tuple[object, ...] = (1,)
        else:
            items: list[tuple[int, object]] = []
            for item in self.prerelease:
                if item.isdigit():
                    items.append((0, int(item)))
                else:
                    items.append((1, item))
            pre = (0, *items)
        return self.major, self.minor, self.patch, pre

    def compare(self, other: "SemVer") -> int:
        left = self.precedence_key()
        right = other.precedence_key()
        return (left > right) - (left < right)


def read_version(root: Path) -> str:
    path = root / "VERSION"
    if not path.is_file():
        raise FileNotFoundError(f"VERSION file not found at {path}")
    value = path.read_text(encoding="utf-8").strip()
    SemVer.parse(value)
    return value


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_excluded(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return True
    if path.name in EXCLUDED_SUFFIXES:
        return True
    if path.suffix in {".pyc", ".pyo"}:
        return True
    if path.name.endswith("~") or ".bak-" in path.name:
        return True
    return False


def iter_package_files(root: Path, extra_excludes: Iterable[str] = ()) -> Iterator[Path]:
    excluded = set(extra_excludes)
    for path in sorted(root.rglob("*")):
        if not path.is_file() or is_excluded(path, root):
            continue
        relative = path.relative_to(root).as_posix()
        if any(relative == item or relative.startswith(item.rstrip("/") + "/") for item in excluded):
            continue
        yield path


def build_manifest(root: Path, include_manifest: bool = False) -> dict[str, object]:
    version = read_version(root)
    files: list[dict[str, object]] = []
    for path in iter_package_files(root):
        relative = path.relative_to(root).as_posix()
        if not include_manifest and relative in {"MANIFEST.json", ".installed-manifest.json"}:
            continue
        files.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "schema_version": 1,
        "package": "google-flow-scripting-skill",
        "version": version,
        "generated_at": now_utc_iso(),
        "files": files,
    }


def write_manifest(root: Path, filename: str = "MANIFEST.json") -> Path:
    path = root / filename
    payload = build_manifest(root)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def verify_manifest(root: Path, filename: str = "MANIFEST.json") -> list[str]:
    path = root / filename
    if not path.is_file():
        return [f"missing {filename}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid {filename}: {exc}"]

    errors: list[str] = []
    if payload.get("version") != read_version(root):
        errors.append(f"{filename} version does not match VERSION")
    records = payload.get("files")
    if not isinstance(records, list):
        return errors + [f"{filename} files field is not a list"]

    expected_paths: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            errors.append(f"invalid file record in {filename}")
            continue
        relative = record.get("path")
        expected_hash = record.get("sha256")
        expected_size = record.get("size")
        if not isinstance(relative, str) or not isinstance(expected_hash, str):
            errors.append(f"invalid file record in {filename}")
            continue
        expected_paths.add(relative)
        file_path = root / relative
        if not file_path.is_file():
            errors.append(f"missing file listed in manifest: {relative}")
            continue
        if file_path.stat().st_size != expected_size:
            errors.append(f"size mismatch: {relative}")
        if sha256_file(file_path) != expected_hash:
            errors.append(f"checksum mismatch: {relative}")

    actual_paths = {
        path.relative_to(root).as_posix()
        for path in iter_package_files(root)
        if path.relative_to(root).as_posix() not in {filename, ".installed-manifest.json"}
    }
    untracked = sorted(actual_paths - expected_paths)
    if untracked:
        errors.append("untracked package files: " + ", ".join(untracked[:20]))
    return errors


def find_local_modifications(root: Path, filename: str = ".installed-manifest.json") -> list[str]:
    path = root / filename
    if not path.is_file():
        return ["installation manifest is missing"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["installation manifest is invalid"]

    changed: list[str] = []
    records = payload.get("files", [])
    if not isinstance(records, list):
        return ["installation manifest has an invalid files field"]

    expected_paths: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        relative = record.get("path")
        expected = record.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            continue
        expected_paths.add(relative)
        file_path = root / relative
        if not file_path.is_file():
            changed.append(relative + " (missing)")
        elif sha256_file(file_path) != expected:
            changed.append(relative)

    actual_paths = {
        item.relative_to(root).as_posix()
        for item in iter_package_files(root)
        if item.relative_to(root).as_posix() not in {filename, "MANIFEST.json"}
    }
    for relative in sorted(actual_paths - expected_paths):
        changed.append(relative + " (untracked)")
    return changed


def copy_package_tree(source: Path, destination: Path, *, include_tests: bool = True) -> None:
    excluded = [] if include_tests else ["tests", ".github", "CONTRIBUTING.md"]
    destination.mkdir(parents=True, exist_ok=True)
    for path in iter_package_files(source, excluded):
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def safe_extract_zip(archive: Path, destination: Path) -> None:
    destination_resolved = destination.resolve()
    with zipfile.ZipFile(archive) as zipped:
        for member in zipped.infolist():
            target = (destination / member.filename).resolve()
            if destination_resolved not in target.parents and target != destination_resolved:
                raise ValueError(f"unsafe archive path: {member.filename}")
            unix_mode = member.external_attr >> 16
            if unix_mode and stat.S_ISLNK(unix_mode):
                raise ValueError(f"archive links are not allowed: {member.filename}")
        zipped.extractall(destination)


def safe_extract_tar(archive: Path, destination: Path) -> None:
    destination_resolved = destination.resolve()
    with tarfile.open(archive, "r:*") as tarred:
        members = tarred.getmembers()
        for member in members:
            target = (destination / member.name).resolve()
            if destination_resolved not in target.parents and target != destination_resolved:
                raise ValueError(f"unsafe archive path: {member.name}")
            if member.issym() or member.islnk():
                raise ValueError(f"archive links are not allowed: {member.name}")
            if not (member.isfile() or member.isdir()):
                raise ValueError(f"unsupported archive entry: {member.name}")
        # Manual type checks above keep this compatible with Python 3.10,
        # where tarfile extraction filters are not consistently available.
        tarred.extractall(destination, members=members)


def find_package_root(extracted: Path) -> Path:
    candidates = [extracted]
    candidates.extend(path for path in extracted.iterdir() if path.is_dir())
    valid = [path for path in candidates if (path / "VERSION").is_file() and (path / "SKILL.md").is_file()]
    if len(valid) != 1:
        raise ValueError(f"expected one package root, found {len(valid)}")
    return valid[0]


def fetch_json(url: str, timeout: float = 20.0) -> dict[str, object]:
    request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            data = response.read()
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} while requesting {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"network error while requesting {url}: {exc.reason}") from exc
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid JSON returned by {url}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"unexpected JSON response from {url}")
    return payload


def download_file(url: str, destination: Path, timeout: float = 60.0) -> None:
    request = Request(url, headers={"Accept": "application/octet-stream", "User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response, destination.open("wb") as output:
            shutil.copyfileobj(response, output)
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} while downloading {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"network error while downloading {url}: {exc.reason}") from exc


def release_api_url(repository: str, version: str | None = None) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("repository must use owner/name format")
    base = f"https://api.github.com/repos/{repository}/releases"
    normalised = str(SemVer.parse(version)) if version else None
    return f"{base}/tags/v{normalised}" if normalised else f"{base}/latest"


def asset_download_url(release: dict[str, object], asset_name: str) -> str | None:
    assets = release.get("assets", [])
    if not isinstance(assets, list):
        return None
    for asset in assets:
        if isinstance(asset, dict) and asset.get("name") == asset_name:
            url = asset.get("browser_download_url")
            return url if isinstance(url, str) else None
    return None


def parse_sha256sums(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?(.+)", line.strip())
        if match:
            result[match.group(2)] = match.group(1).lower()
    return result


def temporary_directory(prefix: str) -> tempfile.TemporaryDirectory[str]:
    return tempfile.TemporaryDirectory(prefix=prefix)
