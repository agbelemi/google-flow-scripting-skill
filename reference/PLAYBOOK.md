<!-- validate:ignore-file -->
# The Playbook

Production method and configurable defaults for Google Flow and the Gemini API.

Documentation reviewed 24 July 2026. Current official documentation and the active interface take precedence.

## 1. The constraint that drives everything

Independent generations have no guaranteed implicit memory.

Carry continuity explicitly through approved references, saved frames, model-supported controls, editing, extension, fully stated current conditions and a state ledger.

### 1.1 Every prompt is self-contained

State the relevant style, location, layout, lighting, cast, wardrobe, physical state, camera, action, audio and ending in the prompt that needs them.

### 1.2 Never use vague backward references

Do not write `the same vendor`, `as before`, `continuing from scene 2`, or `still wet`. Name the current state and the actual attached reference.

### 1.3 References carry identity

Use an approved image or frame where available. Describe only the state, action, wardrobe variation or held object that the reference does not already show.

## 2. Mandatory capability profile

Ask for these before writing scenes:

1. surface: Google Flow or Gemini API
2. model
3. mode
4. duration
5. aspect ratio

Read `reference/FLOW-FEATURES.md` for the current matrix.

### 2.1 Duration summary

| Surface and model | Common supported duration |
|---|---|
| Flow, Veo 3.1 Lite or Fast | 4s, 6s, 8s |
| Flow, Veo 3.1 Quality | 8s |
| Flow, Gemini Omni Flash | 4s, 6s, 8s, 10s |
| Gemini API, Veo 3.1 | 4s, 6s, 8s, subject to mode restrictions |
| Gemini API, Gemini Omni Flash | 3s through 10s |

Never describe Omni as simply a 10-second version of Veo. It has a separate reference and conversational-editing workflow.

### 2.2 Token limits

- Veo 3.1 API: 1,024 text-input tokens.
- Gemini Omni Flash: 1,048,576-token total multimodal context window.
- No separate universal Flow prompt-editor character limit was found in the official sources reviewed for this release.

Use a practical safety margin for Veo API prompts. Local token estimates are advisory unless they use the production tokenizer.

## 3. Canonical reference handles

Every character and location reference starts with `@`, followed by an alphanumeric PascalCase name with no spaces or punctuation.

```text
@Kwame
@CafeLadies
@SidewalkCafe
```

Convert `Cafe Ladies` to `@CafeLadies`. Keep the handle identical in every file and generated script.

### 3.1 What needs a locked reference

Create a locked reference for:

- every named character
- every featured extra, even if appearing once
- every recurring extra
- every recurring group
- every environment
- every product or hero prop whose appearance must remain exact

True background texture and disposable one-shot objects can remain descriptive.

### 3.2 Reference allocation is model-specific

#### Veo

Veo reference-image generation supports up to three subject references. Use an approved composite plate when a shot needs more identity sources than the selected mode accepts.

```text
SLOT 1: @Lead
SLOT 2: @SupportingPlate
SLOT 3: @Location
```

#### Omni

Omni has a separate multi-image workflow. Use direct references and image-role tags where the surface supports them. Do not impose a three-reference ceiling.

```text
@Lead -> <IMAGE_REF_0>
@SupportingGroup -> <IMAGE_REF_1>
@Location -> <IMAGE_REF_2>
@HeroVehicle -> <IMAGE_REF_3>
```

### 3.3 Build plates from images, never identity prose

Composite approved reference images. Never recreate an identity by describing it in words.

```text
NO TEXT IN THE IMAGE: no labels, captions or watermarks.
SOURCE REFERENCES: @CharacterOne, @CharacterTwo

Create one clean group reference plate from the attached approved images.
Preserve each face, hairstyle, body shape, wardrobe item and accessory.
Use a plain neutral background. Do not redesign or substitute anyone.
```

Crop one clean view from a turnaround sheet before compositing to avoid duplicate bodies.

### 3.4 Set anchors

Every environment has a fixed set-anchor paragraph repeated wherever it is used.

```text
LOCATION: @CottageInterior. One room roughly four by five metres.
Fixed layout: heavy door on the back wall; small window to its left;
long wooden table in the centre; stone hearth on the right wall; bed in
the far-left corner; herbs hanging from ceiling beams.
```

State screen direction and where people stand when geography matters.

## 4. Storyboard before video

Storyboard every segment as a separate image-generation task.

Hard rule:

> "A storyboard-generation prompt must command image generation in its first sentence, declare the exact output count and layout, prohibit planning responses, and enumerate forbidden invented actions."

The first sentence is:

```text
GENERATE THE STORYBOARD IMAGE NOW.
```

### 4.1 Default panel layouts

| Duration | Panels | Layout |
|---|---:|---|
| 4s | 2 | 2x1 |
| 6s | 3 | 3x1 |
| 8s | 3 | 3x1 |
| 10s | 4 | 2x2 |

Use 3x3 only for nine explicitly authored visual frames. Never invent five extra actions to expand a four-frame board.

### 4.2 Separate the three outputs

1. internal operator note
2. copy-paste storyboard generation prompt
3. approval checklist

Never paste operator notes or the checklist into the image generator.

### 4.3 The contact-sheet prompt must prohibit

- a written storyboard
- a scene breakdown
- an asset list
- sound or dialogue notes
- a permission question
- extra panels
- intermediate frames
- invented actions

It must end by requiring only the completed contact-sheet image.

### 4.4 Static camera wording

A still cannot perform a camera move. State the segment-wide camera plan, then describe the static composition visible at each panel moment.

Crop and save the final approved panel as a standalone image before using it as a handoff reference.

## 5. Audio

Choose an audio policy for the project. Direct generated audio explicitly or declare that audio will be replaced.

```text
Dialogue: @Maya says, "We have to leave now." - quiet and urgent.
SFX: the latch clicks as her hand turns it.
Ambient: distant birdsong and wind through leaves.
Not heard: no music, no traffic, no other voices.
```

For silence:

```text
AUDIO: Intentional silence.
```

Keep short clips sonically focused. One dialogue line, one primary effect and one ambient bed are usually enough.

## 6. Structure, timing and arithmetic

- One segment equals one video generation.
- Scene lengths should divide cleanly into the chosen segment duration.
- Runtime equals segment count multiplied by segment duration.
- Storyboard panel count follows the selected layout.
- Retry assumptions must be stated as estimates, not guarantees.

### 6.1 Timing modes

Exact one-second beats are optional.

Use one of:

- `exact`: one interval per second
- `coverage`: ordered intervals cover the whole duration without gaps or overlaps
- `loose`: timing guidance exists but is not mechanically exact
- `off`: no timeline validation

Omni can use natural language or intervals such as:

```text
[0-3s] @Kwame steps from the taxi.
[3-6s] @Kwame puts on his sunglasses.
[6-10s] @Kwame walks toward the camera.
```

Choose the mode that communicates the action most clearly.

## 7. Pipeline

| Stage | Output | Gate |
|---|---|---|
| 1. Brief | surface, model, mode, duration, ratio, runtime | capability confirmed |
| 2. Structure | logline, scenes, state ledger | arithmetic confirmed |
| 3. References | canonical handles and set anchors | every required reference approved |
| 4. Segment draft | camera, action, audio, ending | references allocated |
| 5. Storyboard | contact sheet per segment | board approved and final panel cropped |
| 6. Video prompt | revised against approved board | validator and continuity audit pass |
| 7. Video | one approved clip per segment | final frame saved |
| 8. Assembly | edit, grade and sound finishing | complete |

## 8. Handoffs

Classify each handoff.

### Continuation

```text
CONTINUATION: the new clip begins from the attached @PreviousFinalFrame.
The opening composition and ongoing movement match that frame without a
reset. Current visible state: [complete standalone description].
```

### Cut

```text
CUT: this is a new camera setup. Story state carries over, but framing
follows the new camera instruction. Current visible state: [complete
standalone description].
```

Only offer first-and-last-frame interpolation or extension when the chosen surface, model and mode support it.

## 9. Text bleed and punctuation

Avoid tokens that can appear as unwanted text:

- colour-temperature values
- hex colour codes
- bracketed set labels
- bare timecodes outside a clearly marked timing section

Do not use em dashes in generated scripts. Use a colon, comma, full stop, parentheses, or spaced hyphen.

Video, reference-sheet and ordinary image prompts start with an explicit text policy.

Storyboard prompts start with `GENERATE THE STORYBOARD IMAGE NOW.`, declare the output contract, then place the text policy near the top.

## 10. Prompt length and attention

Long prompts trade compactness for precision. Let references carry visual identity and keep action language unambiguous.

- Put the most important constraints near the top.
- Keep each beat focused on one visible change.
- Limit exclusions to plausible failures.
- Shorten before rewriting when the model ignores middle instructions.
- For targeted Omni edits, describe only the requested change and add `Keep everything else the same.`

Do not state that no prompt limit exists. See section 2.2.

## 11. Positive and negative instructions

Prefer positive visual description. Use critical negative instructions for plausible failure modes.

Veo interfaces may provide a separate negative-prompt field. Omni API does not. Put Omni exclusions in the ordinary prompt.

## 12. Cultural specificity

Specific detail improves authenticity. Ask rather than invent when the user knows the location or custom better. Teach necessary context visually instead of relying on assumed knowledge.

Part of the Google Flow Scripting and Prompting Skill:
https://github.com/agbelemi/google-flow-scripting-skill
