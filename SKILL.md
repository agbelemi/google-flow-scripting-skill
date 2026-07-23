---
name: google-flow-scripting
description: Plans, scripts, storyboards and audits multi-shot Google Flow and Veo video projects. Use for narrative shorts, animation, live action, documentaries, ads, music videos, continuity planning, reference-image planning, prompt writing, or pre-generation QA.
---

# Google Flow Scripting & Prompting

**Version:** 1.3.1

Use this Skill to turn a video brief into a production-ready, continuity-aware package for Google Flow or a comparable video generator.

## Operating principles

1. **Do not assume implicit memory between independent generations.** Carry continuity explicitly through self-contained prompt details, reference images or ingredients, saved frames, first/last-frame controls, extensions, and state tracking.
2. **Treat platform limits as dated facts, not eternal rules.** Read `reference/FLOW-FEATURES.md` before making a capability claim. When the current interface disagrees, trust the interface and flag the discrepancy.
3. **Plan assets before final segment prompts.** Establish the cast, recurring objects, environments, reference priority and set anchors before writing detailed shots.
4. **Storyboard before expensive video generation.** Check identity, geography, composition, state and handoffs in stills first.
5. **Make each generation prompt usable on its own.** Avoid phrases such as “the same person,” “as before,” or “continuing from scene 2” unless an actual attached reference or frame is named explicitly.
6. **Use project policies, not universal creative laws.** One beat per second, continuous shots, no on-screen text and generated audio are defaults that can be changed when the brief requires something else.

## Workflow

### 1. Establish the brief

Extract what is already known before asking questions. Resolve only production-critical gaps:

- format and visual treatment
- target runtime and segment duration
- aspect ratio and delivery platform
- audience and objective
- dialogue, generated audio, intentional silence, or sound added in post
- on-screen text policy
- rights-sensitive people, brands, locations or claims

Do not repeat questions the user has already answered. Make visible assumptions for minor gaps.

### 2. Choose the relevant craft files

Read:

- `core/flow-story-architect.md` for story structure and state tracking
- `core/flow-asset-manager.md` for references, ingredients and set anchors
- `core/flow-storyboard-director.md` for the storyboard package
- the closest file in `formats/` for format-specific craft
- `core/flow-continuity-auditor.md` before approving the final script

Use `core/flow-orchestrator.md` as the end-to-end routing reference.

### 3. Build the production package

Produce, in this order:

1. Brief and explicit assumptions
2. Runtime arithmetic and segment map
3. Cast, object, environment and state inventory
4. Prioritised reference/ingredient plan
5. Storyboard or keyframe plan
6. Self-contained segment prompts
7. Handoff map showing cut, match cut, continuation, extension, or first/last-frame strategy
8. Mechanical validation results
9. Human continuity audit and unresolved risks

### 4. Prompt text policy

The first semantic line of each prompt must declare one of these:

```text
NO TEXT IN THE IMAGE: do not render words, labels, captions or watermarks.
```

or:

```text
INTENTIONAL TEXT IN THE IMAGE: state the exact words, surface and location; no other text.
```

Do not use a blanket no-text rule when packaging, signs, interfaces, subtitles or titles are intentionally part of the shot.

### 5. Audio policy

For generated-audio workflows, include an `AUDIO:` block with dialogue, one primary sound effect, ambience and exclusions when useful.

Deliberate silence is explicit:

```text
AUDIO: Intentional silence.
```

For visual-only previs or sound added entirely in post, say so in the project assumptions and validate with `--no-require-audio`.

### 6. Validate

Run:

```bash
python scripts/validate.py your-script.md --segment-length 8
```

For visual-only or post-audio workflows:

```bash
python scripts/validate.py your-script.md --segment-length 8 --no-require-audio
```

The validator is a mechanical linter, not a substitute for judgement. After it passes, apply the continuity auditor to reference coverage, spatial continuity, state continuity, handoffs and final-frame feasibility.

## Safety and rights

Before using a real person, protected brand asset, sensitive claim, archival material or documentary reconstruction, identify the consent, licence, disclosure and factual-verification requirements. Never present generated reconstruction as authentic evidence.

## Supporting resources

- `reference/PLAYBOOK.md` — full production methodology
- `reference/FLOW-FEATURES.md` — dated platform capability notes
- `reference/TEMPLATES.md` — prompt and deliverable templates
- `reference/FAILURE-MODES.md` — evidence-tagged observed and inferred failures
- `reference/ADAPTING-OTHER-GENERATORS.md` — portability notes
- `reference/VERIFICATION.md` — what “documentation reviewed” means for this release
