<!-- validate:ignore-file -->
# Paste-anywhere prompts and native Skill

The repository root is a native `SKILL.md` package for Claude Code, Cursor and Windsurf. This folder remains the no-install, paste-anywhere route for other assistants.

## Fastest route

Paste [`../reference/PLAYBOOK.md`](../reference/PLAYBOOK.md) into a fresh chat, then say what you are making:

> "Following this playbook, develop a 90-second 2D animated explainer. 8-second segments, 16:9."

## Add a specialist

For format-specific craft, paste the matching agent file after the playbook:

| Making | Paste |
|---|---|
| 3D animation | `../formats/flow-3d-animation.md` |
| 2D animation | `../formats/flow-2d-animation.md` |
| Live action | `../formats/flow-live-action.md` |
| Documentary | `../formats/flow-documentary.md` |
| Advert | `../formats/flow-ads.md` |
| Music video | `../formats/flow-music-video.md` |

## Add the templates

When you reach prompt-writing, paste [`../reference/TEMPLATES.md`](../reference/TEMPLATES.md) so the model uses the exact shapes rather than inventing its own.

## Before generating

Paste [`../core/flow-continuity-auditor.md`](../core/flow-continuity-auditor.md) and ask for an audit of the finished script. Or run the validator if you have Python:

```bash
python ../scripts/validate.py your-script.md --segment-length 8
```

## Minimum viable version

If you can only paste one thing, paste the playbook. Everything else is elaboration on it.
