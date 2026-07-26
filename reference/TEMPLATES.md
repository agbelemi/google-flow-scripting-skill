<!-- validate:ignore-file -->
# Templates

These are the six output shapes used by the skill. Copy their required lines literally.

## Canonical reference handles

Every character or location reference starts with `@`, followed by an alphanumeric PascalCase name with no spaces or punctuation.

```text
@Kwame
@CafeLadies
@SidewalkCafe
```

Convert `Cafe Ladies` to `@CafeLadies`. Keep the same handle in the asset library, operator notes, storyboard prompts, video prompts, and audits.

## Text policy

Video, reference-sheet, and ordinary image prompts open with one explicit text policy. Use this when no lettering is wanted:

```text
NO TEXT IN THE IMAGE: do not render any words, letters, numbers,
captions, subtitles, labels, location names, timecodes, colour
temperature values or watermarks anywhere in the frame.
```

For intentional lettering, replace it with:

```text
INTENTIONAL TEXT IN THE IMAGE: state the exact words, surface and placement; no other text.
```

Storyboard contact-sheet prompts are the exception to first-line placement. Their first sentence must command immediate image generation. Put the text policy immediately after the output contract.

## 1. Character reference sheet

Generated once per referenced character. Use a plain background so the background does not contaminate later generations.

```text
[TEXT-POLICY LINE]

REFERENCE HANDLE: @CharacterName

Character turnaround reference sheet on a plain neutral background,
showing front, three-quarter, side and back views of @CharacterName.

[FULL PHYSICAL DESCRIPTION: age, build, exact height, face, hair,
distinguishing features, and every wardrobe item with colour and
condition. Include any object the character always carries.]

[SIGNATURE POSE SHEET: one or two named poses this character repeats,
and any expression the story depends on.]

[STYLE LINE]
```

For a character based on a real person, prepend:

```text
ATTACH: @CharacterNameSourcePhoto
Stylise the attached face into the visual style below while keeping the
likeness clearly recognisable.
```

To restyle an existing render's face and hair while keeping body and wardrobe:

```text
NO TEXT IN THE IMAGE: no writing, labels, captions or watermarks.

BASE CHARACTER: @CharacterNameBase
FACE REFERENCE: @CharacterNameSourcePhoto

Using @CharacterNameBase as the body and wardrobe source:
1. Remove the original background completely.
2. Place the character on a plain white background with no markings.
3. Modify only the face and hairstyle to match @CharacterNameSourcePhoto.
4. Keep body type, height, clothing, accessories, pose, shading, lighting
   and camera angle unchanged.
```

## 2. Environment reference sheet

```text
[TEXT-POLICY LINE]

REFERENCE HANDLE: @LocationName

Environment reference for @LocationName, wide establishing view, no
people in frame.

[SET ANCHOR: fixed layout, object by object, with positions relative to
each other and approximate dimensions.]

[LIGHTING in plain words, with no colour-temperature values.]

[STYLE LINE]
```

## 3. Storyboard contact-sheet prompt

Generate one contact sheet per segment. Do not generate individual planning prose before the image.

Required layout by default:

| Segment | Panels | Layout |
|---|---:|---|
| 4 seconds | 2 | 2x1 |
| 6 seconds | 3 | 3x1 |
| 8 seconds | 3 | 3x1 |
| 10 seconds | 4 | 2x2 |

Use 3x3 only when nine distinct frames are explicitly authored. Never invent frames to fill a grid.

```text
GENERATE THE STORYBOARD IMAGE NOW.

Do not write a storyboard, scene breakdown, asset list, explanation,
proposal, caption, or follow-up question.

Create exactly ONE finished storyboard contact sheet containing exactly
[PANEL COUNT] cinematic still-image panels arranged in a clean [LAYOUT]
grid.

Panel order: [state the reading order and panel positions].
Do not create more than [PANEL COUNT] panels.
Do not add intermediate frames.
Do not invent additional actions.
Do not ask for permission before generating.

[TEXT-POLICY LINE]

CHARACTER REFERENCES: @CharacterOne, @CharacterTwo
LOCATION REFERENCE: @LocationName
OTHER ATTACHED REFERENCES: [@ReferenceName or NONE]

Use the attached references as the authoritative visual source. Match
them directly. Do not redesign faces, hair, clothing, body proportions,
environment architecture, recurring props, or visual style.

All panels show moments from the same continuous [N]-second segment.
Maintain exact continuity across every panel:
- same referenced faces and hairstyles
- same wardrobe and accessories
- same environment layout and screen direction
- same recurring props and their condition
- same lighting direction and weather
- same character proportions and rendering style

VISUAL STYLE
[STATIC STILL-IMAGE STYLE LINE. Do not describe motion.]
Each panel uses a [16:9 or 9:16] cinematic composition.

LOCATION CONTINUITY
@LocationName. [FULL SET ANCHOR]
Do not reverse, redesign, or rearrange the layout between panels.

LIGHTING CONTINUITY
[PLAIN-WORDS LIGHTING AND DIRECTION]

CAMERA PLAN FOR THE SEGMENT
[WHOLE-SEGMENT CAMERA PLAN FOR CONTINUITY]

PANEL A - [GRID POSITION] - [TIMECODE OR MOMENT]
REFERENCED SUBJECTS: @CharacterOne[, @CharacterTwo]
STATIC FRAMING: [shot size, angle, lens, subject placement].
MOMENT TO CAPTURE: [authored opening state or beat].
DO NOT SHOW: [specific plausible inventions or premature actions].

[PANEL B AND ANY MIDDLE PANELS IN THE SAME FORMAT]

PANEL [FINAL LETTER] - [GRID POSITION] - FINAL HANDOFF FRAME
REFERENCED SUBJECTS: [@Handles]
STATIC FRAMING: [final composition].
MOMENT TO CAPTURE: [exact required final visible state].
DO NOT SHOW: [new action, reaction, damage, or continuity drift].

GLOBAL FORBIDDEN CHANGES
[List the likely failures: changed face, changed wardrobe, damaged prop,
duplicate subject, extra people, altered architecture, text, logos,
watermarks, and any invented actions.] 

FINAL OUTPUT REQUIREMENT
Return only the completed [PANEL COUNT]-panel [LAYOUT] storyboard image.
No written response.
No storyboard rewrite.
No asset-development list.
No sound descriptions.
No dialogue.
No extra frames.
No confirmation question.
```

## 4. Video prompt

```text
[TEXT-POLICY LINE]

Generate one continuous [N]-second shot. [VIDEO STYLE LINE]

CHARACTER REFERENCES: @CharacterOne, @CharacterTwo
LOCATION REFERENCE: @LocationName

LOCATION: @LocationName. [SET ANCHOR]
LIGHTING: [plain-words lighting].

WHO IS IN THIS SHOT: @CharacterOne ([current state, action, and held
objects]), @CharacterTwo ([current state and action]). No other named
characters appear.
ALSO IN THIS SHOT:
  @FeaturedExtra - [action in this shot]

HOW THIS SHOT OPENS:
[CONTINUATION or CUT wording. Omit if the segment opens a scene.]

CAMERA: [camera description]

WHAT HAPPENS:
[TIMING FORMAT SELECTED FOR THE PROJECT]

AUDIO:
  Dialogue: @CharacterName says, "[exact line]" - [tone].
  SFX: [primary sound tied to visible action].
  Ambient: [background bed].
  Not heard: [what must remain absent].

THE SHOT MUST END ON EXACTLY THIS IMAGE: [complete final-frame state]

RULES: exactly [N] seconds; one location only; faces, hair, clothing and
referenced props must not change unexpectedly; no unapproved captions,
subtitles or on-screen writing.
```

Attachments should use canonical handles:

```text
ATTACH: @CharacterOne, @CharacterTwo, @LocationName, @PreviousFinalFrame
```

Where the interface supports a separate negative-prompt field, use:

```text
watermark, on-screen text, caption, subtitle, distorted hands, extra
limbs, warped face, duplicated character, low resolution
```

Omni does not support a separate negative-prompt parameter in the Gemini API. Put critical exclusions in the regular prompt when using Omni.

## 5. Operator note

Written for the human, not the generator.

```text
OPERATOR NOTE - DO NOT PASTE INTO THE GENERATOR
References to attach: @CharacterOne, @CharacterTwo, @LocationName
Start frame: NONE or @FinalFrameName
End frame: NONE or @TargetFinalFrame
Model and surface: [Flow or Gemini API], [model]
Mode: [Text to Video, Ingredients to Video, Frames to Video, Reference to Video, or Edit]
Order of work: generate the storyboard contact sheet first and approve it.
Only after approval, generate the video.
Watch for: [two or three likely failures]
Afterwards: crop and save the final storyboard panel as @PanelFinalName,
then save the approved video final frame as @FinalFrameName.
```

## 6. Approval checklist

This is human-facing and must never be included in the generation prompt.

```text
DO NOT INCLUDE THIS CHECKLIST IN THE GENERATION PROMPT

[ ] Faces match all attached references.
[ ] Every character and location reference uses its canonical @Handle.
[ ] Wardrobe, props and physical state are correct.
[ ] Environment layout and screen direction are unchanged.
[ ] No extra actions, people or objects were invented.
[ ] No unwanted text, numbers, captions, signs, logos or watermarks appear.
[ ] The final panel can be cropped into a clean standalone handoff image.
[ ] The final panel matches the required final state of the video prompt.
```

## Style lines by format

### 3D animation still

```text
High-quality stylised 3D animated feature-film still: soft skin shading,
expressive eyes, slightly exaggerated but believable proportions,
physically based materials, rich global illumination, cinematic depth
of field, and subtle film grain, [RATIO].
```

### 3D animation video

```text
High-quality stylised 3D animated feature film: soft skin shading,
expressive eyes, slightly exaggerated but believable proportions,
physically based materials, rich global illumination, cinematic depth
of field, subtle film grain, [RATIO], and smooth cinematic motion.
```

### 2D animation still

```text
2D animation still: clean vector linework, flat colour fills, simple cel
shading, bold shape language, limited palette, expressive silhouettes,
[RATIO].
```

### Live-action still

```text
Live-action film still: photographic realism, fine natural skin texture,
real optics, controlled depth of field, subtle lens character, filmic
colour grade, fine grain, [RATIO].
```

### Documentary still

```text
Observational documentary still: available light, unposed subjects,
real lived-in location, neutral colour grade, fine grain, [RATIO].
```

### Advertising still

```text
High-end commercial still: pristine product rendering, precise controlled
lighting, clean held highlights, contemporary colour grade, shallow depth
of field, immaculate surfaces, [RATIO].
```

### Music-video still

```text
Music-video still: heightened stylised look, bold saturated colour,
dramatic directional lighting, strong contrast, [RATIO].
```

Replace `[RATIO]` with `widescreen 16:9` or `vertical 9:16`.
