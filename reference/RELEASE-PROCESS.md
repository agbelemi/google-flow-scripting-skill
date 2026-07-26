<!-- validate:ignore-file -->
# Release process

## 1. Start the release

```bash
python scripts/start_release.py 1.7.0 --date 2026-08-01
```

This updates `VERSION`, updates the version in `SKILL.md`, creates a release-history record, adds a changelog section, and updates the release index.

## 2. Complete the records

Replace every `TODO` in:

- `CHANGELOG.md`
- `release-history/v1.7.0.md`

Do not delete old release records. Add correction notes to historical records when needed.

## 3. Verify documentation claims

For every model or interface claim:

- use a dated official source
- distinguish Google Flow from the Gemini API
- identify model and generation mode
- avoid treating preview behaviour as permanent
- record the review in `reference/VERIFICATION.md`

## 4. Run local checks

```bash
python scripts/verify_package.py .
python tests/run_tests.py
python scripts/build_release.py --output dist
```

Inspect `dist/SHA256SUMS` and test the archive with:

```bash
mkdir -p /tmp/flow-release-check
unzip -q dist/google-flow-scripting-skill-v1.7.0.zip -d /tmp/flow-release-check
python /tmp/flow-release-check/google-flow-scripting-skill-v1.7.0/scripts/verify_package.py \
  /tmp/flow-release-check/google-flow-scripting-skill-v1.7.0 --require-manifest
```

## 5. Commit and push

```bash
git add -A
git commit -m "Release v1.7.0"
git push origin main
```

Wait for the Tests workflow to pass.

## 6. Tag the exact commit

```bash
git tag -a v1.7.0 -m "Google Flow Scripting Skill v1.7.0"
git push origin v1.7.0
```

The Publish release workflow checks that the tag matches `VERSION`, runs tests, builds archives, creates checksums, adds provenance attestations, and publishes the GitHub Release.

## 7. Do not mutate published releases

Do not replace files attached to an existing version. Publish a patch release instead. For example, fix v1.7.0 with v1.7.1.

## Release checklist

- [ ] Version follows semantic versioning.
- [ ] `VERSION` and `SKILL.md` agree.
- [ ] Root changelog has the version section.
- [ ] Permanent release record exists.
- [ ] Release-history index has the version.
- [ ] Verification date and sources are current.
- [ ] No em dashes exist in the package.
- [ ] New references use canonical `@PascalCase` handles.
- [ ] Tests pass on supported Python versions.
- [ ] Release assets build and verify.
- [ ] Migration notes exist for behaviour changes.
