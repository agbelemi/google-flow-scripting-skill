# Changelog

All notable changes are recorded here. Individual release notes are preserved in `release-history/` and indexed by `release-history/index.json`.

The project uses semantic versioning:

- patch: backward-compatible fixes
- minor: backward-compatible features
- major: breaking behaviour or package-format changes

## [Unreleased]

No unreleased changes.

## [1.6.0] - 2026-07-24

### Added

- Cross-platform Python installer with Bash and PowerShell launchers.
- Explicit update checker and checksum-verified release updater.
- Installation manifests for local-modification detection.
- Safe backups, backup retention, dry runs, downgrade protection, and Git working-tree protection.
- Versioned ZIP and tar.gz release builder with internal file manifest and external SHA-256 checksums.
- Package verifier for required files, version consistency, release history, checksums, and em-dash prohibition.
- Tag-driven GitHub release workflow, repository templates, support policy, security policy, and Dependabot configuration.
- Permanent per-version records under `release-history/`.
- Canonical storyboard contact-sheet prompt template.
- JSON-driven storyboard prompt generator and worked ten-second 2x2 example.
- Surface, model, mode, and duration compatibility validation.

### Changed

- `VERSION` is now the single source for package and validator versioning.
- Storyboard validation now checks that actual panel sections match the declared count and order.
- Installation and update documentation now distinguishes Git clones from downloaded or installed release copies.
- Stale Flow, Veo, and Omni feature statements were corrected and dated.
- Release and test processes now verify changelog records before shipping.

### Security

- Network updates require a versioned release asset and matching `SHA256SUMS` entry.
- Archive extraction rejects path traversal and archive links.
- The updater refuses silent replacement, backs up the prior installation, and detects local modifications.

## [1.5.0] - 2026-07-23

### Added

- Hard storyboard-generation contract and exact first sentence.
- Four-panel 2x2 default for ten-second scenes with four authored moments.
- Canonical `@ReferenceHandle` rules and validator checks.
- Package-wide em-dash prohibition and integrity check.
- Flow and Gemini API model profiles.
- Flexible timing modes and Veo prompt-length estimate.
- GitHub Actions test workflow.

### Corrected

- Omni Flash Flow durations are 4, 6, 8, and 10 seconds, not only 10 seconds.
- Veo 3.1 API text input has a published 1,024-token limit.
- Three image references is not a universal Omni ceiling.
- Seed reuse is a consistency aid, not deterministic reproduction.

### Tests

- Expanded the suite to 40 passing regression, integration, and package-integrity checks.

## [1.4.0] - 2026-07-23

### Added

- Ten-second segment support.
- Markdown heading recognition for segment markers.
- Model-first intake and unconditional storyboard gate.
- Image-built reference-plate guidance.
- Three-pass asset planning.

### Historical note

Two statements in the original v1.4.0 notes were corrected in v1.5.0: Omni also supports shorter Flow durations, and Veo 3.1 publishes an API token limit. The original release record remains preserved with a correction note in `release-history/v1.4.0.md`.

### Tests

- Expanded the suite to 26 checks.

## [1.3.1] - 2026-07-23

### Fixed

- Scoped beat extraction to video prompt regions.
- Prevented storyboard timing from satisfying malformed video timing.
- Improved short hex-colour detection.

### Tests

- Expanded the suite to 24 checks.

## [1.3.0] - 2026-07-23

### Added

- Canonical root `SKILL.md` package.
- Native Skill installation for Claude Code, Cursor, and Windsurf.
- Optional Claude specialist subagent installation.
- Atomic staging and timestamped backups.
- Raw timing-order, duplicate-interval, text-policy, audio-policy, and JSON-output validation.
- Regression and installer integration tests.

### Changed

- Replaced absolute memory language with "no guaranteed implicit memory."
- Clarified that timing, text, and audio policies are configurable project choices.
