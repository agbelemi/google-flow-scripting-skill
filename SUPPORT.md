# Support

## Before opening an issue

Run:

```bash
python scripts/verify_package.py .
python tests/run_tests.py
python scripts/validate.py your-script.md --segment-length 8 --surface flow --model veo-3.1-fast --mode text-to-video
```

Include the failing command, complete validator output, Skill version, Python version, operating system, selected Flow surface, model, mode, and duration.

## Installation questions

For a Git clone:

```bash
git pull --ff-only origin main
python tests/run_tests.py
python scripts/install.py --tool cursor --force
```

For a downloaded or installed release:

```bash
python scripts/check_update.py
python scripts/update.py
```

Downloaded ZIP files and installed AI Skills do not update automatically. Restart the AI tool or begin a new session after installing an update.

## Platform behaviour

Google Flow and Gemini API features can vary by model, region, plan, and interface rollout. Check `reference/FLOW-FEATURES.md`, then confirm the active interface before spending credits.

This repository cannot provide support for account billing, regional availability, service outages, or content moderation decisions made by Google.
