<!-- validate:ignore-file -->
# THE PLAYBOOK
### Production method and configurable defaults for Google Flow

*Documentation reviewed 23 July 2026. See `FLOW-FEATURES.md` and `VERIFICATION.md`; current official documentation and the live interface take precedence.*

Every agent in this repository is built on this document. If you read only one file, read this one.

---

## 1. The constraint that drives everything

**Independent generations have no guaranteed implicit memory.**

Do not assume a fresh generation can infer the previous clip or resolve phrases such as "the same character as before." Carry continuity explicitly through attached references, saved frames, first/last-frame controls, extensions and fully stated current conditions.

Three working consequences follow. Apply them alongside the actual reference and frame controls available in the current interface.

**1.1 — Every prompt must be self-contained.** Style, location, layout, lighting, cast, wardrobe, physical state, camera, action, audio and ending, restated every time. A prompt must be generatable cold, out of order, with no other context.

**1.2 — Never write a backward reference.** "The same vendor", "continuing from before", "as in scene 2", "he is still wet" — not usable as a standalone identity or state instruction. If a character is wet, say *he is wet*.

**1.3 — Identity carries through explicit references plus current-state instructions.** Words alone do not reliably preserve identity. Use an attached reference or saved frame where available, then describe only the state and action the reference cannot show.

---

## 2. Hard specifications

These are generator limits, not style choices. Design the whole project around them.

| Setting | Supported | Notes |
|---|---|---|
| **Segment length** | **4s, 6s or 8s** | 8s is the default and the usual working choice |
| **Aspect ratio** | **16:9 or 9:16** | These two only. 1:1, 4:3 and 2.39:1 must be cropped or letterboxed in post |
| **Resolution** | 720p or 1080p | Upscaling to 2K and 4K available |
| **Frame rate** | 24fps | |
| **Reference images** | Up to 3 per generation | Via Ingredients to Video |
| **Audio** | Native, generated with the video | Directed by your prompt text |
| **Longer shots** | Extend continues a clip past its base length | Builds from the final moment of the previous clip |

**There is no 10-second segment.** A script written in 10-second units cannot be generated. Choose 4, 6 or 8 and build the whole structure on it.

**Ask the user for segment length and aspect ratio before writing anything.** Every scene duration, beat count and composition depends on both.

---

## 3. The asset system

### 3.1 What needs a locked reference

Lock a reference image for:

- Every named character, without exception
- **Every extra featured in frame** — the camera holds on them, or their hands, face or body carry a beat — **even if they appear once**
- Every extra appearing in more than one segment
- Every recurring group, as one group plate
- Every environment
- Every product or hero object

Leave as plain description only: true background texture, and one-shot props.

> **The threshold is *featured OR recurring*, not recurring alone.**
> A vendor appearing in two shots whose hands open the film is featured. Without a locked reference she will be a woman in one clip and a man in the next. This is the most commonly reported failure in AI video production.

### 3.2 How references bind

Flow's mechanism is **Ingredients to Video** — up to three reference images supplied per generation. Some builds also expose `@` shorthand for saved assets. Use whichever your interface offers; the discipline is identical.

Two rules that matter more than the mechanism:

**Reference images should sit on a plain or segmented background.** A character reference with a busy scene behind it drags that scene into your generation.

**Your text must complement your references, never contradict them.** If a reference shows the character, do not re-describe their face and clothing in competing detail — you are handing the model two sources that will disagree. Describe what the reference cannot show: their *state* right now, what they are doing, what they are holding.

This is the one place in the whole skill where more description makes output worse.

### 3.3 Naming

Short, CamelCase, no spaces, no punctuation: `Maya`, `Leo`, `StreetVendor`, `KitchenInterior`, `ForestClearing`.

Keep names identical everywhere — library, script and prompts.

### 3.4 Environment splitting

One physical location may need more than one reference. If a place is shot both wide and close, and the framings share no anchor objects, they drift apart.

Split when the location is large and some shots sit at a specific station within it.

> A single `Forest` reference fails, because a wide shot of trees and a close shot at a specific clearing share nothing. Split into `ForestPath` and `ForestClearing`.

Do not split small enclosed sets. One room is one reference, held by a set anchor.

### 3.5 Set anchors

Every environment carries a fixed **set anchor** paragraph, repeated in every prompt using it.

```
Location: CottageInterior. A single room roughly four by five metres.
Fixed layout: a heavy door at the back wall, a small window to its left,
a long wooden table in the centre, a stone hearth on the right wall with
a large iron pot, a bed in the far left corner, herbs hanging from the
ceiling beams.
```

For station environments the anchor must also state **where people stand**:

```
Location: MarketStall. The wooden counter is in frame at all times and
the vendor stands behind it, never out in the open lane.
```

---

## 4. Audio

**Choose an audio policy for the project.** In generated-audio workflows, an undirected prompt may produce unwanted sound, so direct it explicitly. Deliberate silence is written as `AUDIO: Intentional silence.` For visual-only previs or replacement sound in post, record that choice and disable the mechanical audio check.

### 4.1 Syntax

```
Dialogue — use quotation marks and name the speaker:
    Maya says, "We have to leave now." - quiet, urgent.

SFX — describe plainly and tie to visible action:
    SFX: the door latch clicks as her hand turns it.

Ambient — define the background bed:
    Ambient: distant birdsong and wind through leaves.
```

### 4.2 Keep it thin

One line of dialogue, one primary sound effect and one ambient bed is the working maximum for a short clip. Crowded soundscapes come out muddy.

Vagueness produces generic noise. "Spooky sounds" gives you nothing. "A faint metallic creak and a low draught through the chimney" gives you the scene.

### 4.3 State what should not be heard

```
Not heard: no music, no other voices, no traffic.
```

### 4.4 Silence is a choice you must make explicitly

If a moment should be silent, say so. Removing sound at an emotional low point is powerful, but only if you ask for it.

### 4.5 Practical limits

Lip-sync accuracy and effect timing vary between runs. For dialogue that must land exactly, generate several times and select, or replace the audio in post. Treat generated audio as a strong draft, not a locked mix.

---

## 5. Structure and arithmetic

- One **segment** = one prompt = one generation.
- A segment has **one beat per second**. An 8-second segment has 8 beats.
- Scene lengths must be whole multiples of the segment length.
- Runtime = segments x segment length.
- If the project needs horizontal and vertical, generate hero moments **natively vertical** rather than cropping. Vertical wants tighter framing and action in the centre band.

### Budget arithmetic

Most shots are not right first time. **Expect three to five attempts per segment.** Budget for it and tell the user up front.

Draft on the fastest model tier, then commit only approved shots to the highest quality tier. Running everything at top quality is the fastest way to exhaust a plan.

---

## 6. The pipeline

| Stage | Output | Gate |
|---|---|---|
| 1. Brief | Format, segment length, aspect ratio, runtime, tone | |
| 2. Concept | Logline, structure, ending | |
| 3. Cast bible | Look, wardrobe, signature gesture, arc | |
| 4. Breakdown | Scenes with durations, cast, hook, out-point | |
| 5. Segment script | Camera, beats, audio, required final frame | |
| 6. Reference list | Every locked reference, named and counted | |
| 7. Reference images | Generate them all | **Gate: no video before every reference exists** |
| 8. Storyboard | Still panels per segment | **Gate: no video before panels approved** |
| 9. Video | One clip per segment | |
| 10. Assembly | Edit, grade, sound finishing | |

The gates are not optional. Skipping them burns budget discovering faults that cheap stills would have caught.

---

## 7. Writing beats

- **One observable physical action per beat.** Something a camera can see.
- **Include camera state changes**: "CUT to", "the push-in begins", "WHIP-PAN to".
- **Give numbers.** "head tilts 10 degrees", "a 20cm push-in", "leans back 30 degrees".
- **Name emotion through the body**, never the label. Not "she is frightened" but "her hand stops halfway to the latch."
- **The last beat lands the final frame**, usually ending "hold on this."

### The final frame is load-bearing

Every segment states the exact image it ends on. That image is the generation target, the QA check, and the opening state of the next prompt. Where the interface accepts an end frame as an input, precision here pays twice.

---

## 8. Handoffs: cut or continuation

Classify every handoff.

**CONTINUATION** — the same unbroken camera move flowing on:

> This is a direct continuation of the same unbroken shot. At the instant this clip begins the frame looks exactly like this, and the action must carry straight on from it without resetting: [previous final frame, in full].

**CUT** — a new camera setup:

> This is a new camera setup. The story has just reached this point, so the people carry over exactly as described here, but the framing is new and must follow the camera direction below rather than the previous composition: [previous final frame, in full].

Getting this wrong either freezes a camera that should move, or preserves framing that should have been abandoned.

---

## 9. Text bleed

Label-shaped tokens get painted into the picture. A prompt containing a colour temperature value and a bracketed location name produced a frame with both rendered into the sky.

**Never put these in a prompt:** colour temperature values, hex colour codes, set or scene names in brackets, bare timecodes.

**Always open every prompt with:**

```
NO TEXT IN THE IMAGE: do not render any words, letters, numbers,
captions, subtitles, labels, location names, timecodes, colour
temperature values or watermarks anywhere in the frame. The only writing
allowed is writing that physically exists on a prop in the world, and
only where the description below explicitly names it.
```

Use plain words: "warm golden morning light", not a Kelvin value.

---

## 10. Exclusions: describe, do not forbid

Positive description outperforms negative commands. Rather than "no buildings", write "an empty moorland stretching unbroken to the horizon".

Where the interface exposes a **negative prompt field**, put technical exclusions there — watermarks, distortion, extra limbs, on-screen text — and keep the main prompt purely descriptive.

---

## 11. Storyboard first

Before animating a segment, generate its key moments as **still images**: first frame, one or two middle beats, and the final frame. Check them, then generate the video.

Stills are cheap. Video is not. A wrong face, a drifted set or burned-in text shows up in the stills, and the approved final-frame still is the reference you carry into the next segment.

**A video prompt cannot output storyboard stills.** Storyboards are separate image generations, always.

---

## 12. Cultural specificity

Specific detail travels; generic detail does not. Local food, transport, dress, weather and idiom make a story feel true and make audiences elsewhere lean in.

What does not travel is **assumed context**. If a scene depends on knowing a custom, let the scene teach it visually.

When writing for a place you do not know, ask rather than assume. When the user knows the place, follow their detail exactly and do not sand it into something generic.

---

*Part of the Google Flow Scripting & Prompting Skill — https://github.com/agbelemi/google-flow-scripting-skill*
