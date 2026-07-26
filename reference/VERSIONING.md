<!-- validate:ignore-file -->
# Versioning policy

The project follows semantic versioning.

## Patch release

Use `x.y.Z` for backward-compatible corrections:

- validator false positive or false negative
- documentation correction
- installer or updater defect
- test-only improvement
- source-link refresh with no workflow change

## Minor release

Use `x.Y.0` for backward-compatible capability additions:

- new generator profile
- new specialist or template
- new optional validator check
- new installer target
- new automation command

## Major release

Use `X.0.0` when users must change existing scripts or installation practices:

- removing or renaming a public CLI option
- changing reference-handle syntax
- making a previously optional rule mandatory for all scripts
- changing package layout in a way old installers cannot understand
- dropping a supported Python version

## Pre-release versions

Preview work may use versions such as:

```text
2.0.0-alpha.1
2.0.0-beta.1
2.0.0-rc.1
```

Do not mark a preview release as latest unless it is intended for general use.

## Sources of version truth

`VERSION` is canonical. These must match it:

- the `SKILL.md` version line
- the root changelog section
- `release-history/vVERSION.md`
- the current entry in `release-history/index.json`
- the Git tag `vVERSION`
- release archive filenames

The validator reads `VERSION` at runtime, so it does not carry a separate hard-coded version string.
