<!-- validate:ignore-file -->
# TEMPLATES
### The five prompt shapes. Copy these literally.

All open with one explicit text policy. Use the no-text form when no lettering is wanted:

```
NO TEXT IN THE IMAGE: do not render any words, letters, numbers,
captions, subtitles, labels, location names, timecodes, colour
temperature values or watermarks anywhere in the frame.
```

For intentional lettering, replace that policy with:

```text
INTENTIONAL TEXT IN THE IMAGE: state the exact words, surface and placement; no other text.
```

Referred to below as `[TEXT-POLICY LINE]`. In the templates, use the
`[TEXT-POLICY LINE]` placeholder with the policy appropriate to the project.

---

## 1. Character reference sheet

Generated once per character. **Plain background** — a busy background behind a reference drags into every generation that uses it.

```
[TEXT-POLICY LINE]

Character turnaround reference sheet on a plain neutral background,
showing front, three-quarter, side and back views of the same character.

[FULL PHYSICAL DESCRIPTION: age, build, exact height, face, hair,
distinguishing features, and every wardrobe item with colour and
condition. Include any object the character always carries.]

[SIGNATURE POSE SHEET: one or two named poses this character repeats,
and any expression the story depends on.]

[STYLE LINE]
```

For a character based on a real person, prepend:

```
[ATTACH THE REFERENCE PHOTO] - stylise this face into the style below
while keeping the likeness clearly recognisable.
```

**To restyle an existing render's face and hair to a real reference, keeping body and wardrobe:**

```
Using the attached character as the base:
1. Remove the original background completely.
2. Place the character on a plain white background with no text or
   markings.
3. Modify the face and hairstyle to match the attached reference photo,
   keeping the body, clothing and overall style unchanged.

Adapt face shape, features and skin tone to resemble the real person.
Match hairstyle, texture and colour to the reference. Keep body type,
height, clothing and accessories exactly as in the attached render.
Maintain the same shading, lighting and rendering. Preserve the camera
angle and pose.

Attach: [1] the base character image  [2] the real face reference
```

---

## 2. Environment reference sheet

```
[TEXT-POLICY LINE]

Environment reference, wide establishing view, no people in frame.

[SET ANCHOR: the fixed layout, object by object, with positions relative
to each other and approximate dimensions.]

[LIGHTING in plain words - no colour temperature values.]

[STYLE LINE]
```

---

## 3. Storyboard image prompt

One per key moment. Minimum: first frame, a middle beat, the final frame.

```
[TEXT-POLICY LINE]

A single still frame from a film. [STYLE LINE]

Location: [Name]. [SET ANCHOR]
Lighting: [plain-words lighting].

Who is in this frame: [Name] ([state and action - not a re-description
of what the reference already shows]), [Name].
Also present:
  [ExtraName] - [what they are doing in this shot]

Camera plan for the whole segment: [camera description]
This panel is the moment at [Xs]. Frame it using whichever camera setup
above is active at that point.

The moment to capture: [the beat text, or the final frame for the last
panel]
```

Attach the relevant reference images to every panel.

---

## 4. Video prompt

```
[TEXT-POLICY LINE]

Generate one continuous [4/6/8]-second shot. [STYLE LINE]

LOCATION: [Name]. [SET ANCHOR]
LIGHTING: [plain-words lighting].

WHO IS IN THIS SHOT: [Name] ([current state, action, what they hold]),
[Name]. No other named characters appear.
ALSO IN THIS SHOT:
  [ExtraName] - [action in this shot]

HOW THIS SHOT OPENS:
[CONTINUATION or CUT wording - see PLAYBOOK section 8. Omit entirely if
the segment opens a scene.]

CAMERA: [camera description]

WHAT HAPPENS, ONE BEAT PER SECOND:
  0-1s: ...
  1-2s: ...
  [one line for every second of the segment]

AUDIO:
  Dialogue: [Name] says, "[exact line]" - [tone].
  SFX: [the one primary sound, tied to visible action].
  Ambient: [the background bed].
  Not heard: [what should stay out].

THE SHOT MUST END ON EXACTLY THIS IMAGE: [final frame]

RULES: exactly [N] seconds; one location only; faces, hair and clothing
must not change between beats; no captions, subtitles or on-screen
writing.
```

**Attachments:** the character and environment references for this shot, plus the previous segment's exported final frame as the start frame where the interface accepts one.

Omit any audio line that does not apply. A segment with no speech simply has no dialogue line — but it should still have ambient, or you get whatever the model invents.

**Negative prompt field** (separate from the prompt above, where the interface offers it):

```
watermark, on-screen text, caption, subtitle, distorted hands, extra
limbs, warped face, duplicated character, low resolution
```

---

## 5. Operator note

Written for the human, not the generator.

```
OPERATOR NOTE - read before generating
References to attach: [Name]  [Name]  [Location]
Start frame: [none / the exported final frame of segment X]
End frame: [none / the target final frame still, where you have one]
Mode: [Text to Video / Ingredients to Video / Frames to Video]
Order of work: generate the storyboard panels first and check them.
  Only when they are right, generate the video.
Watch for: [the two or three things most likely to fail in this shot]
Afterwards: save the final frame as an asset, name it FINAL_X, and check
  it matches the required final frame before moving on.
```

---

## Style lines by format

Reused verbatim across a project. Describe positively; put technical exclusions in the negative prompt field.

**3D animation**
```
3D animated feature film: soft skin shading, large expressive eyes,
slightly exaggerated proportions, rich global illumination, creamy
background blur, gentle film grain, [RATIO], smooth cinematic motion.
```

**2D animation**
```
2D animation: clean vector linework, flat colour fills with simple cel
shading, bold shape language, a limited palette, expressive silhouettes,
[RATIO].
```

**Live action**
```
Live-action cinematography: photographic realism, fine natural skin
texture with visible pores, real optics with shallow depth of field,
subtle lens character, filmic colour grade, fine grain, [RATIO], 24fps
motion with natural motion blur.
```

**Documentary**
```
Observational documentary cinematography: available light, handheld
camera with natural micro-movement, unposed subjects, real lived-in
locations, neutral colour grade, fine grain, [RATIO].
```

**Advertising**
```
High-end commercial cinematography: pristine product rendering, precise
controlled lighting with clean held highlights, glossy contemporary
colour grade, shallow depth of field, immaculate surfaces, [RATIO].
```

**Music video**
```
Music video cinematography: heightened stylised look, bold saturated
colour, dramatic directional lighting, strong contrast, expressive
camera movement, [RATIO].
```

Replace `[RATIO]` with "widescreen 16:9" or "vertical 9:16" — the only two the generator produces natively.
