# Contributing

Thanks for improving the project. The most useful contributions come from real production failures, reproducible validator cases, and corrections backed by current primary documentation.

## Before changing anything

1. Read `SKILL.md` and `reference/PLAYBOOK.md`.
2. Read `reference/VERIFICATION.md` before changing platform claims.
3. Keep every generated character and location reference in canonical `@PascalCase` form.
4. Do not introduce the Unicode em dash character anywhere in the package.
5. Do not silently rewrite an old release record.

## Report a production failure

Open an issue with:

1. **Symptom:** what appeared in the output.
2. **Expected result:** what the prompt required.
3. **Surface and model:** for example Flow with Omni Flash or Gemini API with Veo 3.1 Fast.
4. **Mode and settings:** duration, aspect ratio, reference mode, seed, and any other relevant controls.
5. **Prompt:** a minimal reproducible prompt when sharing it is safe.
6. **Evidence:** screenshots or clips when licensing and privacy permit.
7. **Fix:** what improved the result, if known.

Verified findings can be added to `reference/FAILURE-MODES.md`. Use the evidence tags honestly:

- `OBS`: directly observed
- `DOC`: documented by the platform owner
- `INF`: inferred or not independently verified
- `REC`: repository recommendation

## Add a validator rule

Validator rules must be mechanical. Subjective visual judgement belongs in `core/flow-continuity-auditor.md`.

For every new rule:

1. Add the implementation to `scripts/validate.py`.
2. Add at least one `fail_*` fixture proving broken input is rejected.
3. Add or retain a `pass_*` fixture proving valid input is accepted.
4. Register any expected failure label in `tests/run_tests.py`.
5. Run the complete test suite.

False negatives are the highest priority because they let broken input pass. False positives also matter because noisy checks train users to ignore the validator.

## Add a format specialist

Copy an existing file in `formats/` and retain:

- YAML frontmatter with `name`, `description`, and `color`
- a style line with `[RATIO]` as a placeholder
- format-specific craft guidance
- a format-specific failure table
- a deliverable statement

Add the specialist to `divisions.json`. Do not duplicate the shared playbook.

## Documentation and source standards

Use current primary sources for claims that may change. Record the review date and direct source in `reference/VERIFICATION.md`.

Separate:

- current documented platform behavior
- repository recommendations
- observed production behavior
- unverified inferences

Do not present an API capability as proof that the Flow interface exposes the same control. Do not present one Flow interface observation as an API guarantee.

## Style rules

- Plain, direct English.
- Short paragraphs and concrete examples.
- No hype.
- No Unicode em dashes.
- Character and location references use `@PascalCase` with no spaces or punctuation.
- Examples that intentionally contain bad patterns use an `example`, `counterexample`, `bad`, `dont`, or `avoid` code fence.

## Run tests

```bash
python scripts/verify_package.py .
python tests/run_tests.py
python -m compileall -q scripts tests
bash -n scripts/install.sh
bash -n scripts/update.sh
```

The pass count is intentionally not hard-coded in this document. The only acceptable result is zero failed checks.

## Changelog and release records

Every published version needs all of these:

- `VERSION`
- matching `**Version:**` in `SKILL.md`
- a root `CHANGELOG.md` section
- `release-history/vX.Y.Z.md`
- an entry in `release-history/index.json`
- a matching Git tag `vX.Y.Z`

Start a release with:

```bash
python scripts/start_release.py 1.7.0 --date 2026-08-01
```

Complete every TODO before publishing. Old release records are permanent. If an old statement is later corrected, append a dated correction note instead of erasing the historical record.

## Pull request checklist

- [ ] Current primary documentation supports time-sensitive claims.
- [ ] Generated references use canonical `@PascalCase` handles.
- [ ] No Unicode em dash exists in the package.
- [ ] New mechanical behavior has passing and failing regression coverage.
- [ ] Package verification passes.
- [ ] All tests pass with zero failures.
- [ ] `CHANGELOG.md` is updated under `Unreleased` or the new version.
- [ ] A permanent release record exists when preparing a release.
