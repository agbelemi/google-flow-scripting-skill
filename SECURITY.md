# Security policy

## Supported versions

Security fixes are applied to the latest release. Older downloaded copies do not update automatically.

## Reporting a vulnerability

Do not publish secrets, private prompts, API keys, personal data, or a working exploit in a public issue.

Use GitHub's private vulnerability reporting feature when it is enabled for the repository. Otherwise, contact the repository owner privately through the contact method listed on the GitHub profile and include:

- affected version
- operating system and Python version
- exact script or workflow involved
- reproduction steps
- realistic impact
- suggested mitigation, when known

## Release integrity

Official releases include:

- a versioned ZIP archive
- a versioned tar.gz archive
- `SHA256SUMS`
- an internal `MANIFEST.json`
- GitHub build provenance attestation when published by the release workflow

The updater verifies the external archive checksum and the internal file manifest before replacing an installation.

## Update safety

The updater:

- does not update silently
- detects local modifications when an installation manifest is present
- creates a timestamped backup before replacement
- rejects path traversal and archive links
- refuses to replace a Git working tree by default
- runs package verification and tests before installation

Never enter a Google, GitHub, or AI-service API key into this repository's prompt files or test fixtures.
