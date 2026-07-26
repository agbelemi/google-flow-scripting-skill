# Google Flow and Veo Prompting Skill for Consistent AI Video

> An open-source Google Flow, Veo 3.1, and Gemini Omni Flash production workflow for character consistency, multi-scene continuity, visual storyboards, cinematic prompts, and pre-generation validation.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/agbelemi/google-flow-scripting-skill/actions/workflows/tests.yml/badge.svg)](https://github.com/agbelemi/google-flow-scripting-skill/actions/workflows/tests.yml)
[![Latest release](https://img.shields.io/github/v/release/agbelemi/google-flow-scripting-skill)](https://github.com/agbelemi/google-flow-scripting-skill/releases/latest)
[![Documentation reviewed July 2026](https://img.shields.io/badge/docs%20reviewed-July%202026-blue.svg)](reference/VERIFICATION.md)

## What this project solves

Independent AI video generations have no guaranteed implicit memory. Faces drift, clothing changes, sets rearrange, props break, text appears unexpectedly, and clips fail to join cleanly.

This Skill turns continuity into an explicit production system:

- canonical `@ReferenceHandles` for characters and locations
- cast, environment, prop, and state inventories
- model-specific reference allocation
- visual storyboard contact sheets before video generation
- self-contained segment prompts
- first-frame, last-frame, extension, edit, and cut planning when supported
- mechanical prompt validation
- human continuity auditing

It is an unofficial workflow and is not affiliated with Google.

## Version 1.6.0 highlights

- Safe, checksum-verified update system for downloaded and installed releases
- Cross-platform Python installer with Bash and PowerShell launchers
- Permanent release notes for every version
- Automated version consistency, package manifest, and release archive checks
- Tag-driven GitHub Release publishing
- Executable storyboard prompt generator
- Strict four-panel 2x2 contract for ten-second scenes with four authored states
- Canonical `@PascalCase` reference enforcement
- Package-wide em-dash prohibition
- Surface, model, mode, and duration validation

See [CHANGELOG.md](CHANGELOG.md) and [release-history/](release-history/) for the complete history.

## Quick start

### Clone the source repository

```bash
git clone https://github.com/agbelemi/google-flow-scripting-skill.git
cd google-flow-scripting-skill
python scripts/verify_package.py .
python tests/run_tests.py
python scripts/install.py --tool cursor
```

Supported installer targets:

```text
claude-code
cursor
windsurf
generic
```

Bash and PowerShell launchers are also included:

```bash
./scripts/install.sh --tool cursor
powershell -ExecutionPolicy Bypass -File scripts/install.ps1 --tool cursor
```

### Use without installation

Open `SKILL.md` in an AI coding assistant, or paste `reference/PLAYBOOK.md` and the specialist file you need into the conversation.

## Start every project with the production profile

Do not write timed scenes until these are known:

```text
SURFACE: Google Flow or Gemini API
MODEL: Veo 3.1 variant, Gemini Omni Flash, or another named model
MODE: Text to Video, First Frame, First and Last Frame, References to Video, Video Edit, or Extend
SEGMENT LENGTH: supported whole seconds
ASPECT RATIO: usually 16:9 or 9:16
```

Current reviewed examples:

- Flow Veo 3.1 Lite and Fast: 4, 6, or 8 seconds for ordinary generation
- Flow Veo 3.1 Quality: 8 seconds in current credit documentation
- Flow Gemini Omni Flash: 4, 6, 8, or 10 seconds
- Gemini API Veo 3.1: 4, 6, or 8 seconds with feature-specific restrictions
- Gemini API Omni Flash: 3 through 10 seconds at 720p and 24 FPS

Capabilities change. Read [reference/FLOW-FEATURES.md](reference/FLOW-FEATURES.md) and confirm the active interface.

## Canonical reference rule

Every generated character or location reference begins with `@` and uses one alphanumeric PascalCase name:

```text
@Kwame
@CafeLadies
@SidewalkCafe
```

Incorrect:

```text
Kwame
@Cafe Ladies
Sidewalk Cafe
@Sidewalk-Cafe
```

Use the same handle in asset records, operator notes, storyboard prompts, video prompts, attachment lists, and audits.

## Visual storyboard rule

The storyboard-generation contract is hard-coded:

> "A storyboard-generation prompt must command image generation in its first sentence, declare the exact output count and layout, prohibit planning responses, and enumerate forbidden invented actions."

Every copy-paste storyboard prompt begins exactly with:

```text
GENERATE THE STORYBOARD IMAGE NOW.
```

Default contact sheets:

| Segment | Default panels | Layout |
|---|---:|---|
| 4 seconds | 2 | 2x1 |
| 6 seconds | 3 | 3x1 |
| 8 seconds | 3 | 3x1 |
| 10 seconds | 4 | 2x2 |

Use a 3x3 grid only when nine distinct frames were explicitly authored. Do not let the generator invent filler actions.

Generate a storyboard package from JSON:

```bash
python scripts/generate_storyboard_prompt.py examples/storyboard-spec.json \
  --output storyboard-package.md
```

The output separates:

1. internal operator notes
2. the copy-paste image-generation prompt
3. the human approval checklist

## Validate a script

Flow and Omni reference generation:

```bash
python scripts/validate.py storyboard-package.md \
  --segment-length 10 \
  --surface flow \
  --model omni-flash \
  --mode references-to-video \
  --beat-mode off \
  --no-require-audio
```

Flow and Veo text to video:

```bash
python scripts/validate.py video-script.md \
  --segment-length 8 \
  --surface flow \
  --model veo-3.1-fast \
  --mode text-to-video \
  --beat-mode exact
```

Timing modes:

```text
exact     one line for every second
coverage  continuous intervals with no gaps or overlaps
loose     ordered timing cues without full coverage
 off      no timing validation
```

The validator checks:

- vague backward references
- text-bleed tokens
- prohibited em dashes
- prompt text policy
- canonical `@ReferenceHandles`
- storyboard output contract and panel order
- beat order, gaps, overlaps, duplicates, and duration
- surface, model, mode, and duration compatibility
- unsupported aspect ratios
- audio direction when required
- advisory Veo API prompt length

It does not replace visual review or continuity judgement.

## Specialist roster

### Core craft

| File | Responsibility |
|---|---|
| `core/flow-orchestrator.md` | Intake, capability profile, routing, and sequencing |
| `core/flow-story-architect.md` | Runtime arithmetic, segment map, state ledger, and story structure |
| `core/flow-asset-manager.md` | Canonical handles, references, plates, environments, and allocation |
| `core/flow-storyboard-director.md` | Visual contact-sheet prompts and storyboard approval gate |
| `core/flow-continuity-auditor.md` | Final adversarial continuity audit |

### Format specialists

- `formats/flow-3d-animation.md`
- `formats/flow-2d-animation.md`
- `formats/flow-live-action.md`
- `formats/flow-documentary.md`
- `formats/flow-ads.md`
- `formats/flow-music-video.md`

## Updating an installed copy

Downloaded ZIP files and installed AI Skills do not update automatically.

Check for a release:

```bash
python scripts/check_update.py
```

Apply a verified update:

```bash
python scripts/update.py
```

The updater:

- requires a versioned GitHub Release asset
- verifies `SHA256SUMS`
- verifies the internal `MANIFEST.json`
- runs the full package tests
- detects local modifications
- creates a timestamped backup
- refuses silent replacement
- refuses to replace a Git working tree by default

Git clones should update with:

```bash
git pull --ff-only origin main
python tests/run_tests.py
python scripts/install.py --tool cursor --force
```

Restart the AI host or begin a new session after updating. See [reference/UPDATE-GUIDE.md](reference/UPDATE-GUIDE.md).

## Building and publishing releases

Prepare a new version:

```bash
python scripts/start_release.py 1.7.0 --date 2026-08-01
```

Verify and build:

```bash
python scripts/verify_package.py .
python tests/run_tests.py
python scripts/build_release.py --output dist
```

Pushing a matching tag such as `v1.7.0` triggers `.github/workflows/release.yml`, which runs tests, builds ZIP and tar.gz assets, writes checksums, creates provenance attestations, and publishes a GitHub Release using the permanent record in `release-history/v1.7.0.md`.

See [reference/RELEASE-PROCESS.md](reference/RELEASE-PROCESS.md).

## Release history policy

Every published version must have:

- a `VERSION` value
- a matching `SKILL.md` version
- a root changelog section
- a permanent `release-history/vVERSION.md` file
- an entry in `release-history/index.json`
- a matching Git tag
- versioned release asset filenames

Old release records are never deleted. Later corrections are appended as explicit correction notes.

## Security and support

- [SECURITY.md](SECURITY.md)
- [SUPPORT.md](SUPPORT.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)

Do not place API keys, personal data, private prompts, or unlicensed source material in scripts, examples, issues, or test fixtures.

## License

MIT. See [LICENSE](LICENSE).
