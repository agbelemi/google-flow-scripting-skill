<!-- validate:ignore-file -->
# Migration notes

## From v1.5.0 to v1.6.0

### Installation

The installer is now implemented in Python and launched by both Bash and PowerShell wrappers.

Old command:

```bash
./scripts/install.sh --tool cursor --force
```

Still valid. Cross-platform alternatives:

```bash
python scripts/install.py --tool cursor --force
powershell -ExecutionPolicy Bypass -File scripts/install.ps1 --tool cursor --force
```

### Updates

Old installed copies remain unchanged. Install v1.6.0 once to gain `.installed-manifest.json`, explicit update checking, checksum verification, and safe release updates.

### Validator

Use `--mode` when checking model-specific features:

```bash
python scripts/validate.py script.md \
  --segment-length 10 \
  --surface flow \
  --model omni-flash \
  --mode references-to-video \
  --beat-mode coverage
```

Omitting `--mode` retains the broader model-duration check for compatibility with existing commands.

### Storyboard prompts

The storyboard contract is unchanged in principle but now checks actual panel sections. A declaration of four panels must include `PANEL A` through `PANEL D` once each and in order.

### Release records

Every future version must have both a cumulative changelog section and a permanent file under `release-history/`.
