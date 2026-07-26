# Release history records

This directory keeps one permanent Markdown record for every published package version.

Rules:

1. Never delete or silently rewrite an old release record.
2. If an old claim is later found to be wrong, add a clearly dated correction note and point to the correcting release.
3. Keep `CHANGELOG.md` as the cumulative human-readable history.
4. Keep `release-history/index.json` as the machine-readable index.
5. A release tag, `VERSION`, the root changelog section, the index entry, and the release record filename must agree.
6. Build releases only with `python scripts/build_release.py`.

The release workflow refuses to publish a tag that does not match `VERSION` or lacks a matching record.
