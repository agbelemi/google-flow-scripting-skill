# 🎬 Google Flow Scripting & Prompting Skill

> **Turn any AI assistant into a film production crew for Google Flow.** Eleven specialists that script, storyboard, prompt and audit AI-generated video — built from real production runs and the faults they exposed.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://makeapullrequest.com)
[![Documentation reviewed July 2026](https://img.shields.io/badge/docs%20reviewed-July%202026-blue.svg)](reference/VERIFICATION.md)

---

## What this is

AI video generators produce beautiful short clips and then fall apart across a film. A trader is a woman in one shot and a man in the next. A market stall vanishes. "3500K" gets painted into the sky. Clips refuse to cut together.

None of that is bad luck. It follows from one production constraint: **independent generations have no guaranteed implicit memory.** Continuity must be carried through references, frames, extensions, state tracking and self-contained instructions.

This skill gives your AI assistant the craft to work around it — plus a validator that catches the mechanical faults before you spend a single generation on them.

---

## Quick start

```bash
git clone https://github.com/agbelemi/google-flow-scripting-skill.git
cd google-flow-scripting-skill
python tests/run_tests.py      # confirm the validator behaves
./scripts/install.sh
```

Then, in your assistant:

> "/google-flow-scripting I want to make a 90-second product film in Flow."

It runs the intake, routes you to the right specialist, and sequences the rest.

**No install?** Paste `reference/PLAYBOOK.md` and the agent you need into any model. Everything works as plain text.

**What "install" means per tool.** Claude Code, Cursor and Windsurf now receive a native `SKILL.md` package with bundled references and the validator. Claude Code users can additionally install the eleven specialist subagents with `--install-subagents`. Existing installations are backed up before replacement.

---

## The roster

### 🎯 Core Craft — runs on every project

| Agent | Does | Use when |
|---|---|---|
| 🎬 **flow-orchestrator** | Intake interview, routing, sequencing | Always start here |
| 📐 **flow-story-architect** | Structure, cast bible, scene breakdown with exact durations | You have a concept, not a shape |
| 🗂️ **flow-asset-manager** | Decides what needs an `@` handle, splits environments, writes reference sheets | Characters keep changing appearance |
| 🖼️ **flow-storyboard-director** | Still-panel prompts — the cheap QA gate | Before generating any video |
| 🔍 **flow-continuity-auditor** | Eight-check adversarial audit | Before generating anything at all |

### 🎨 Format Specialists — pick one

| Agent | For | Signature discipline |
|---|---|---|
| 🧊 **flow-3d-animation** | Stylised family-feature 3D, animated shorts | Exaggerated proportion, signature poses, material behaviour |
| ✏️ **flow-2d-animation** | Flat vector, cel, explainers | Silhouette-first design, limited palettes, deliberate typography |
| 🎥 **flow-live-action** | Photoreal drama and comedy | Skin texture, real optics, fewer faces per frame |
| 📹 **flow-documentary** | Observational, interview, archival-feel | Imperfection as aesthetic, plus synthetic-footage ethics |
| 📢 **flow-ads** | Product films, brand spots, social | Product as locked asset, native vertical, claim safety |
| 🎵 **flow-music-video** | Performance, narrative, visualisers | Segments mapped to bars via BPM |

---

## What your assistant learns

**The self-containment rule.** Every prompt restates style, location, layout, lighting, cast, wardrobe, physical state, camera, action and ending. No prompt ever refers backwards. `"the same trader"` provides no usable identity instruction unless an actual reference or frame is attached.

**The `@` handle threshold: featured *or* recurring.** Not recurring alone. A vendor in two shots whose hands open the film is featured. Without a handle, she changes.

**Environment splitting.** A market shot wide and close needs two assets, because a counter close-up and a lane wide-shot share no anchor objects and will drift apart.

**Set anchors.** A fixed-layout paragraph repeated in every prompt using that location, stating what is present and where people stand.

**Text policy and bleed.** Kelvin values, hex codes and bracketed set names can become unwanted lettering. Every prompt begins with either an explicit no-text policy or a precise intentional-text policy.

**Cut versus continuation.** Every handoff classified and worded accordingly, or the camera freezes when it should move.

**Audio is a project policy.** For generated-audio workflows, direct dialogue, effects, ambience and exclusions. Use `AUDIO: Intentional silence.` when silence is deliberate. For visual-only previs or sound added entirely in post, validate with `--no-require-audio`.

**Text must complement your references, not contradict them.** The counter-intuitive one. If a reference image already shows a character's face, re-describing it in detail hands the model two sources that disagree. Describe state and action instead.

**Storyboard first.** Stills cost a fraction of video. Every fault above is visible in stills.

---

## The validator

```bash
python scripts/validate.py your-script.md --segment-length 8
```

```
Google Flow script validation

your-script.md
  1. Backward references............ FAIL (2)
      line 10: The same vendor  -  "the same X" assumes implicit memory
      line 11: Continuing from the previous  -  describe the incoming frame in full
  2. Text-bleed tokens.............. FAIL (2)
      line 8: 3500K  -  colour temperature value - use plain words
      line 8: #C86B3C  -  hex colour code - use a colour name
  3. Text policy.................... PASS
  4. Beat timeline (expect 8)....... FAIL (1)
      line 2: segment 1.1  -  missing expected intervals; 4 beat lines, expected 8
  5. Unsupported specifications..... FAIL (1)
      line 6: 10-second shot  -  this workflow uses 4, 6 or 8 seconds
  6. Audio direction................ FAIL (1)
      line 2: VIDEO PROMPT 01  -  no AUDIO block; use intentional silence when deliberate

VERDICT: DO NOT GENERATE. Fix the failures above and re-run.
```

Mechanical checks only. The judgement checks — final-frame chain, handoff classification, reference coverage, state continuity — are the `flow-continuity-auditor` agent's job.

**It validates your prompts, including inside code fences.** That is where prompts normally live, so that is what gets checked. Documentation that quotes bad patterns on purpose opts out with `<!-- validate:ignore-file -->`, or per-block with a fence tagged ```` ```example ````.

**It is covered by regression and integration tests.** `python tests/run_tests.py` currently runs 22 checks, including malformed ordering, duplicate beats, multiple segments, pure JSON output, native Skill installation and backup preservation. Those exist to catch false negatives — a validator that silently passes broken input is worse than none, because it turns "I should check this" into "it passed".

---

## Configurable per project

The orchestrator asks before writing anything:

- **Segment length** — **4, 6 or 8 seconds**. These are the only lengths that generate
- **Aspect ratio** — **16:9 or 9:16**. These two generate natively; other shapes are cropped in post
- **Format** — routes to the matching specialist
- **Audio policy** — generated audio, intentional silence, visual-only previs, or replacement sound in post
- **Credit budget** — expect three to five attempts per segment, and hear the real number up front
- **Runtime**, with the arithmetic confirmed back to you

If you ask for something the generator does not support, it says so rather than quietly building something unusable.

---

## Reference library

| File | Contents |
|---|---|
| [`reference/PLAYBOOK.md`](reference/PLAYBOOK.md) | The universal rules. Read this one if you read nothing else |
| [`reference/FLOW-FEATURES.md`](reference/FLOW-FEATURES.md) | Ingredients, Frames to Video, Extend, Scenebuilder, model tiers, seeds |
| [`reference/TEMPLATES.md`](reference/TEMPLATES.md) | The five prompt shapes, plus style lines per format |
| [`reference/FAILURE-MODES.md`](reference/FAILURE-MODES.md) | Observed faults, causes, fixes |
| [`reference/ADAPTING-OTHER-GENERATORS.md`](reference/ADAPTING-OTHER-GENERATORS.md) | What transfers to Runway, Kling, Luma and others |
| [`reference/VERIFICATION.md`](reference/VERIFICATION.md) | What was reviewed, tested and not claimed by this release |

---

## Other generators

Written for Flow, but most of it is generator-agnostic craft. Only the `@` mention is Flow-specific — everywhere else, compensate with longer physical descriptions and aggressive start-frame chaining. See [`reference/ADAPTING-OTHER-GENERATORS.md`](reference/ADAPTING-OTHER-GENERATORS.md).

---

## What's coming

The repository relies on community contributions to keep pace with generator updates. Expect:

- **New format specialists.** The roster will expand into highly specific roles for emerging formats — notably short-form vertical comedy built for TikTok and Reels, where pacing, quick cuts and framing have to match the medium exactly.
- **Expanded validator checks.** `validate.py` will gain new mechanical checks for emerging text-bleed tokens and aspect-ratio conflicts, so a fault is caught before it costs a generation.
- **New failure modes.** Model updates fix old bugs and introduce new ones. `reference/FAILURE-MODES.md` will keep growing with newly discovered faults, their causes, and the prompting workarounds that bypass them.
- **Generator adaptations.** More cross-compatibility notes for other platforms. The focus stays squarely on the visual generation pipeline rather than audio tooling or music production — audio appears here only as a prompt field, because the generator produces it whether or not you direct it.

---

## Contributing

New format specialists, generator adaptations, and validator checks are all welcome — especially **new failure modes**. If you hit a fault this repo does not cover, open an issue with the symptom, the cause you found, and the fix. That table is the most valuable thing here and it grows by contribution.

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Licence

MIT — use it commercially, modify it, ship it. See [`LICENSE`](LICENSE).

Built by **[Agbelemi](https://github.com/agbelemi)** from real production runs, and the mistakes they surfaced.

Documentation was reviewed against current official Google Flow/Veo and host-tool Skill documentation on **23 July 2026**. This is not a claim that every account or interface variant was manually tested; see [`reference/VERIFICATION.md`](reference/VERIFICATION.md).

---

*If this saved you a generation budget, star the repo so the next person finds it.*
