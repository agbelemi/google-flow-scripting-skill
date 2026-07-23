<!-- validate:ignore-file -->
# FLOW FEATURES
### The generation modes and controls, and how to use each one

*Documentation reviewed 23 July 2026. Flow changes frequently; treat this as a dated map and check the current interface.*

---

## Generation modes

### Text to Video
The default. A prompt produces a clip with no visual input.

Best for: establishing shots, abstract inserts, anything with no continuity obligation to a previous shot. Historically the most reliable mode for spoken dialogue — if speech comes out silent or wrong in another mode, test it here.

### Ingredients to Video
Supply up to **three reference images** — character, object, style, location — and the generation carries them.

This is the primary mechanism for consistency across shots, and it is what the whole asset system in this skill is built to feed.

Two rules that decide whether it works:

- **Reference images belong on a plain or segmented background.** A busy background behind your character drags that background into the output.
- **Your text must complement the references, not contradict them.** Do not re-describe a face the reference already shows. Describe state, action and what they hold.

Style and location references should not contain extra subjects unless you want those subjects in the shot.

### Frames to Video
Supply a **start frame**, an **end frame**, or both, and the clip is generated between them.

This is the strongest continuity tool available:

- **Start frame** — chains a clip to the previous one. Use the exported final frame of the segment before.
- **End frame** — lets you *target* the required final frame rather than hope for it.
- **Both** — the shot is bracketed at each end, and only the movement between is generated.

If your script already specifies a required final frame for every segment — as this skill insists — you are one still-image generation away from being able to supply it directly.

Keep the two frames compositionally close. Drastic changes in framing or colour between them produce unstable transitions.

### Extend
Continues an existing clip beyond its base length, building from its final moment. Sequences can run well past a minute this way.

Use Extend when an action genuinely needs longer than one segment and a cut would hurt. Prefer separate segments when you want a cut — you keep far more control.

Note that some edit modes cannot be applied to extended clips, so do your inserts and removals before extending.

---

## Editing an existing clip

- **Insert** — add an object or character into an existing shot, with lighting and perspective matched.
- **Remove** — take an element out; the background fills in.
- **Lasso** — draw a freehand selection and describe the change in plain language.
- **Camera** — adjust shot framing after generation.

Refinements can run for a few conversational turns before the model loses the thread of your edits. If you need to keep an intermediate version, save it before continuing.

---

## Scenebuilder

The timeline. Clips are arranged in sequence, extended, and previewed as an assembled scene.

Its most useful production feature is **Save frame as asset**: pause on any frame, save it, and reuse it as an ingredient, a start frame or an end frame. This is the actual mechanism behind every "export the final frame" instruction in this skill.

---

## Model tiers and credits

Flow offers tiers that trade quality against speed and cost. The names change; the strategy does not.

**Draft on the fastest tier. Commit only approved shots to the highest tier.**

Running every generation at top quality is the most common way to exhaust a plan, and blind testing generally shows a small quality gap between fast and standard tiers on ordinary scenes.

Budget realistically: **three to five attempts per segment** is normal, not a sign that something is wrong. A 30-segment film is a 90-to-150-generation project.

---

## Other controls

**Seed** — fixes the random starting point. Reuse the same seed to make a result repeatable while you adjust wording.

**Negative prompt** — a separate field for technical exclusions: watermarks, distortion, extra limbs, on-screen text. Keep these out of the main prompt, which should stay purely descriptive.

**Resolution and upscaling** — generate at lower resolution while iterating, then upscale the approved take.

**Audio toggle** — audio is generated with the video. Where an interface exposes a switch, leaving it on is usually right, since directed audio is part of the prompt.

---

## Making reference images

Flow includes image generation, and this is where your character and environment references should come from. Generate the reference, check it, save it, and only then start generating video against it.

A reference image is generated once and used dozens of times. It is worth several attempts to get right.

---

## What this means for the pipeline

| You want | Use |
|---|---|
| Consistent character across shots | Ingredients to Video, plain-background reference |
| Clips that cut together cleanly | Frames to Video with the previous final frame as start |
| To hit an exact ending composition | Frames to Video with an end frame |
| An action longer than one segment | Extend |
| To fix one element in a good take | Insert, Remove or Lasso |
| To assemble and review | Scenebuilder |
| To iterate cheaply | Fast tier, low resolution, fixed seed |

---

*Part of the Google Flow Scripting & Prompting Skill — https://github.com/agbelemi/google-flow-scripting-skill*
