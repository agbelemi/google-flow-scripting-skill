# Contributing

Thanks for helping. This repository gets better mainly through people hitting faults in real production and writing them down.

## The most valuable contribution: a new failure mode

If you hit a generation fault this repo does not cover, open an issue with:

1. **Symptom** — what you saw, concretely. "The vendor changed sex between clips."
2. **Cause** — what you worked out was responsible.
3. **Fix** — what actually solved it.
4. **Generator and settings** — Flow, Veo, Runway; segment length; aspect ratio.

Verified entries go into `reference/FAILURE-MODES.md` and, where mechanical, into `scripts/validate.py`.

## Adding a format specialist

New formats are welcome — animation styles, verticals like real estate or education, regional formats.

Copy an existing file in `formats/` and keep the shape:

- YAML frontmatter with `name`, `description`, `color`
- A style line with `[RATIO]` left as a placeholder
- **What this format rewards** — the craft that is specific to it
- **Format-specific failures** table
- A deliverable statement

Then add it to `divisions.json`.

Write only what is genuinely different about the format. Do not restate the playbook — agents cite `reference/PLAYBOOK.md` instead of duplicating it.

## Adding a validator check

Checks must be **mechanical** — findable by pattern or structure, with no judgement. Judgement checks belong in `flow-continuity-auditor`.

Add the pattern to the relevant list in `scripts/validate.py`, add a `fail_*` fixture to `tests/fixtures/`, register it in `EXPECTED_FAILURES` in `tests/run_tests.py`, and confirm the suite still reports zero failures.

Two failure modes to guard against, in priority order:

1. **False negatives** — broken input reported as clean. These are the dangerous kind and every `fail_*` fixture exists to prevent one.
2. **False positives** — valid input flagged. These train people to ignore the tool, which eventually causes a false negative by another route.

## Adapting to another generator

Add a row to the table in `reference/ADAPTING-OTHER-GENERATORS.md` describing that generator's equivalent of the `@` binding, and note anything that needs re-testing.

## Evidence standards for failure modes

Every row in `FAILURE-MODES.md` carries an evidence tag: **OBS** (observed directly), **DOC** (documented by the vendor), or **INF** (inferred and unverified).

Tag your contribution honestly. An INF row that says so is useful. An INF row dressed as OBS damages the whole table, because readers cannot tell which claims to trust.

Verifying or disproving an existing INF row is one of the most valuable contributions here.

## Style

- Plain, direct English. Short sentences.
- Concrete over abstract. Show the prompt rather than describing it.
- Global by default. Illustrate with examples that work anywhere, and never assume the reader's country, language or platform.
- No hype.

## Testing before you open a PR

```bash
python tests/run_tests.py
./scripts/install.sh --tool claude-code --dry-run
```

`run_tests.py` must report **24 passed, 0 failed** for version 1.3.1. It covers validator fixtures plus JSON and installer integration behaviour.

If you add a validator check, add **two** fixtures for it: one named `fail_*` that must be caught, and confirmation that the existing `pass_*` fixtures still pass. The `fail_*` fixtures guard against false negatives, which are the dangerous kind — a validator that silently passes broken input is worse than no validator.

Documentation that quotes bad patterns on purpose has two escape hatches: `<!-- validate:ignore-file -->` for a whole file, or a fence tagged ```` ```example ```` for one block. Do not reach for these to make a real script pass.
