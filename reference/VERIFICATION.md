<!-- validate:ignore-file -->
# Release verification record

## Release

- Package version: **1.3.1**
- Review date: **2026-07-23**
- Scope: documentation review, validator regression tests, and local installer integration tests

## What was reviewed

The release language and packaging were checked against current official documentation for:

- Google Gemini API / Veo video generation, including 4-, 6- and 8-second durations, native audio, reference images, first/last-frame generation and extension
- Claude Code Skills and custom subagents
- Cursor Agent Skills
- Windsurf/Cascade Skills

## What “documentation reviewed” does not mean

It does **not** mean every Flow account, region, plan, interface experiment or model combination was manually exercised. Flow changes frequently and account-level availability can differ. The current interface and official documentation take precedence over this repository.

## Software checks

Run:

```bash
python tests/run_tests.py
```

The suite covers validator fixtures plus installer and JSON-output integration checks. A passing suite establishes behaviour against those tests; it does not prove that all possible Markdown structures or generator behaviours are covered.

## Non-interactive installation

Reinstalling over an existing Skill normally asks for confirmation. In CI, piped shells, or other environments without a TTY, pass `--force` so replacement is predictable. The existing installation is still moved to a timestamped backup:

```bash
./scripts/install.sh --tool cursor --force
```

## Known limits

- The validator is a structural linter, not a semantic continuity model.
- Capability notes are dated and need periodic rechecking.
- Exact reference-image and first/last-frame constraints can vary by model and interface.
- Native Skill discovery and optional metadata can evolve independently across host applications.

## Primary documentation

- Google AI for Developers: Gemini API video generation and Veo documentation
- Anthropic: Claude Code Skills and custom subagents
- Cursor: Agent Skills
- Windsurf/Devin Desktop: Cascade Skills

## Official links used for this review

- Google Veo documentation: https://ai.google.dev/gemini-api/docs/veo
- Google Gemini API video overview: https://ai.google.dev/gemini-api/docs/video
- Google Gemini API changelog: https://ai.google.dev/gemini-api/docs/changelog
- Claude Code Skills: https://code.claude.com/docs/en/skills
- Claude Code custom subagents: https://code.claude.com/docs/en/sub-agents
- Cursor Agent Skills: https://cursor.com/docs/skills
- Windsurf/Cascade Skills: https://docs.windsurf.com/windsurf/cascade/skills
