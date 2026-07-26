<!-- validate:ignore-file -->
# Release verification record

## Release

- Package version: **1.6.0**
- Review date: **2026-07-24**
- Scope: current platform documentation, package behavior, validator regressions, installer integration, updater safety, and release-archive integrity

## Evidence boundaries

This review distinguishes four evidence classes:

- `DOC`: current primary documentation
- `OBS`: directly observed production behavior
- `INF`: inference that has not been independently verified
- `REC`: repository recommendation

A documentation review does not mean every account, region, subscription, interface experiment, or model combination was manually tested. The current interface and current official documentation take precedence over this repository.

## Current capability conclusions used by v1.6.0

### Google Flow

- Flow and the Gemini API are treated as separate surfaces.
- Flow Omni Flash supports 4-, 6-, 8-, and 10-second generation choices in the reviewed Flow support documentation.
- Flow Veo generation duration and available operations depend on the selected Veo variant and operation.
- Flow capabilities can change independently of API model capabilities.

### Gemini API Veo 3.1

- Veo 3.1 model documentation publishes a 1,024-token text-input limit.
- Ordinary output durations include 4, 6, and 8 seconds.
- Reference-image, first-and-last-frame, high-resolution, and extension operations can impose additional restrictions.
- Seed reuse can improve consistency but does not guarantee deterministic output.

### Gemini Omni Flash

- The model card publishes a 1,048,576-token multimodal context window.
- The reviewed API documentation describes 3- through 10-second output at 720p and 24 FPS.
- The API supports conversational video editing and multiple visual inputs.
- The reviewed API documentation does not expose Veo-style video extension or first-and-last-frame interpolation for Omni Flash.
- Simple targeted edit instructions are preferred for isolated edits. A phrase such as `Keep everything else the same.` can help constrain the change.

## Host-tool packaging conclusions

- Claude Code Skills use a `SKILL.md` package with optional supporting files. Global Skills are installed under `~/.claude/skills/` and project Skills can live under `.claude/skills/`.
- Cursor and Windsurf installation paths are treated as installer profiles. Users should confirm current host documentation if those products change their Skill discovery rules.
- A host may cache instructions in an active session. Restart the host or begin a new session after installation or update.

## Software verification commands

```bash
python scripts/verify_package.py .
python tests/run_tests.py
python -m compileall -q scripts tests
bash -n scripts/install.sh
bash -n scripts/update.sh
```

Release archives are additionally checked with:

```bash
python scripts/build_release.py --output dist
```

The release builder creates:

- a versioned ZIP archive
- a versioned tar.gz archive
- an internal `MANIFEST.json`
- external `SHA256SUMS`

The test suite covers validator fixtures, JSON output, storyboard prompt generation, model and mode profiles, installer backups, update checking, local archive updating, manifest verification, release history, workflows, punctuation rules, and release construction. A passing suite establishes behavior against those cases only.

## Update-security conclusions

The updater:

- downloads only named GitHub Release assets
- requires a matching checksum entry for network updates
- rejects archive path traversal and archive links
- verifies the internal file manifest
- runs the package tests before replacement unless explicitly bypassed
- detects changes against the installation manifest
- creates a timestamped backup
- rolls back when replacement fails
- refuses to replace a Git working tree by default
- never updates silently

Users should use `git pull --ff-only` for source clones and the release updater for installed or extracted release copies.

## Known limits

- The validator is a structural linter, not a visual continuity model.
- The local token count is an estimate and may differ from the service tokenizer.
- A capability matrix can become stale after the review date.
- Reference fidelity, identity preservation, and prompt adherence remain probabilistic.
- The updater cannot preserve arbitrary local edits automatically. It detects them, requires explicit confirmation, and keeps a backup.
- A downloaded ZIP or installed Skill does not automatically receive future updates.

## Primary sources reviewed

- Google Flow help, model and feature support: https://support.google.com/flow/answer/16526234
- Google Flow AI credits: https://support.google.com/flow/answer/16228981
- Gemini API Veo guide: https://ai.google.dev/gemini-api/docs/veo
- Gemini API Veo 3.1 model card: https://ai.google.dev/gemini-api/docs/models/veo-3.1-generate-preview
- Gemini API Omni guide: https://ai.google.dev/gemini-api/docs/omni
- Gemini Omni Flash model card: https://ai.google.dev/gemini-api/docs/models/gemini-omni-flash
- Gemini API changelog: https://ai.google.dev/gemini-api/docs/changelog
- Claude Code Skills: https://code.claude.com/docs/en/skills
- Claude Code custom subagents: https://code.claude.com/docs/en/sub-agents
- Cursor Agent Skills: https://cursor.com/docs/skills
- Windsurf Cascade Skills: https://docs.windsurf.com/windsurf/cascade/skills
