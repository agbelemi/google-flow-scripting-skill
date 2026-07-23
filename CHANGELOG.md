# Changelog

## 1.3.1 — 2026-07-23

### Validator

- Scopes beat extraction to each segment's `VIDEO PROMPT` sub-block so storyboard panels may quote time ranges without contaminating the video timeline.
- Falls back to whole-segment scanning only when no `VIDEO PROMPT` marker exists; recognized empty or malformed video prompts are not rescued by storyboard beats.
- Preserves raw beat order and duplicate detection within the scoped region.
- Always flags 6- and 8-digit hex colours; flags 3-/4-digit shorthand only when it contains `a`-`f`, allowing numeric issue references such as `#123` and `#1234`.

### Tests

- Adds passing storyboard-panel and failing storyboard/video-timeline regression fixtures.
- Raises the suite to **24 checks** and records that the false positive was found while testing the mandated storyboard workflow.

### Documentation

- Documents `--force` for predictable non-interactive reinstalls while retaining automatic backups.

## 1.3.0 — 2026-07-23

### Validator

- Preserves raw beat order and duplicate intervals instead of normalising them away.
- Rejects out-of-order and duplicated beat lines with targeted diagnostics.
- Requires the text policy to be the first semantic line of every prompt.
- Accepts explicit intentional-text policies as an alternative to blanket no-text instructions.
- Adds `--no-require-audio` while keeping audio checks enabled by default.
- Treats `AUDIO: Intentional silence.` as a valid deliberate choice.
- Emits pure machine-readable JSON with settings and disabled-check metadata.
- Expands hex-colour detection to common 3-, 4-, 6- and 8-digit forms.

### Packaging and installation

- Adds a canonical root `SKILL.md` package.
- Installs native Skills to Claude Code, Cursor and Windsurf Skill directories.
- Keeps Claude specialist subagents as an optional `--install-subagents` add-on.
- Stages installations atomically and creates timestamped backups before replacement.
- Adds `--target` for explicit destination control.
- Resolves the `formats` division dependency on core resources.

### Tests

- Adds regression fixtures for out-of-order beats, duplicate beats, misplaced text policy, multiple segments, a malformed middle segment, intentional text, intentional silence and disabled audio checking.
- Adds integration tests for pure JSON output, installer dry-run behaviour, native Cursor Skill layout and backup preservation.

### Documentation

- Replaces absolute “no memory” language with “no guaranteed implicit memory.”
- Replaces “Pixar-style” as a category label with descriptive family-feature 3D language.
- Replaces the ambiguous verification badge with a documentation-review record.
- Clarifies that pacing, text and audio requirements are project policies rather than universal creative laws.
