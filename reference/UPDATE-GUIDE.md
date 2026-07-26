<!-- validate:ignore-file -->
# Updating the Skill

Updates are explicit. A downloaded ZIP, cloned repository, or installed AI Skill does not change when a new GitHub release appears.

## Identify your installation type

### Git clone

A Git clone contains a `.git` directory. Update it with Git:

```bash
git checkout main
git pull --ff-only origin main
python tests/run_tests.py
python scripts/install.py --tool cursor --force
```

Replace `cursor` with the host you use. Re-run the installer because the cloned source and the installed Skill are separate copies.

The release updater refuses to replace a Git working tree by default.

### Installed or downloaded release

An installed release contains `VERSION` and normally `.installed-manifest.json`, but no `.git` directory.

Check for a release:

```bash
python scripts/check_update.py
```

Apply it:

```bash
python scripts/update.py
```

In non-interactive use:

```bash
python scripts/update.py --yes
```

When local files were changed intentionally:

```bash
python scripts/update.py --force --yes
```

The prior installation is still backed up before replacement.

## Offline update

Download the release ZIP and `SHA256SUMS`, verify the ZIP checksum, then run:

```bash
python scripts/update.py --archive google-flow-scripting-skill-v1.6.0.zip --sha256 EXPECTED_HASH --yes
```

A local archive must also contain a valid internal `MANIFEST.json` and pass the package tests.

## What the updater checks

1. The target is an installed Skill.
2. A Git source tree is not being overwritten accidentally.
3. Local changes are detected through `.installed-manifest.json`.
4. The release asset matches `SHA256SUMS`.
5. Archive paths are safe.
6. The internal `MANIFEST.json` matches every packaged file.
7. The package version, changelog, and release record agree.
8. The full automated test suite passes.
9. The current installation is backed up before replacement.

## After updating

Restart the AI host or begin a new session. An already-running conversation may continue using instructions loaded from the prior version.

## Rollback

Backups use names such as:

```text
google-flow-scripting.bak-20260724-153000-12345
```

To roll back, close the AI host, rename the current installation, then rename the selected backup to the original installation path.
