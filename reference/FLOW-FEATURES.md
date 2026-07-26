<!-- validate:ignore-file -->
# Flow and Gemini video features

Documentation reviewed 24 July 2026. Product capabilities, regional access, and credit costs change frequently. Check the active interface before spending credits.

## Record the complete generation profile

Always record:

```text
SURFACE: Google Flow or Gemini API
MODEL: Veo 3.1 Lite, Fast, Quality, or Gemini Omni Flash
MODE: Text to Video, First Frame, First and Last Frame, References to Video, Video Edit, or Extend
DURATION: whole seconds
ASPECT RATIO: 16:9 or 9:16
```

Do not infer an API limit from the Flow interface or a Flow feature from an API model card.

## Google Flow profile

The current Google Flow Help matrix distinguishes Veo variants from Gemini Omni Flash.

| Model | Text to Video | First Frame | First and Last | References to Video | Video Edit | Extend |
|---|---|---|---|---|---|---|
| Veo 3.1 Lite | 4s, 6s, 8s | 4s, 6s, 8s | 4s, 6s, 8s | 8s | no | extension operation for eligible 8s Veo clips |
| Veo 3.1 Fast | 4s, 6s, 8s | 4s, 6s, 8s | 4s, 6s, 8s | 8s | no | source clips can be eligible, but Flow performs extension through Lite |
| Veo 3.1 Quality | 8s in current credit documentation | confirm in the active interface | confirm in the active interface | not listed as supported in the current feature matrix | no | eligible 8s source clips may be extended through Lite |
| Gemini Omni Flash | 4s, 6s, 8s, 10s | 4s, 6s, 8s, 10s | coming soon in the reviewed Flow matrix | 4s, 6s, 8s, 10s with advanced character, avatar, and audio references | uploaded and generated video editing | coming soon in the reviewed Flow matrix |

Current official sources:

- https://support.google.com/flow/answer/16352836
- https://support.google.com/flow/answer/16526234
- https://support.google.com/flow/answer/16935718

The validator uses a conservative profile. When the active interface exposes a newer combination, record the discrepancy and update the dated matrix rather than silently overriding it.

## Gemini API model profiles

### Veo 3.1

Official model codes:

```text
veo-3.1-generate-preview
veo-3.1-fast-generate-preview
```

Documented profile:

- text and image input
- video with audio output
- 1,024-token text-input limit
- one output video per request
- ordinary durations of 4, 6, or 8 seconds
- feature-specific restrictions can require an 8-second generation
- first-frame, first-and-last-frame, reference-image, and extension workflows where documented
- up to three subject reference images in the Veo reference-image workflow
- seed reuse may slightly improve repeatability but does not guarantee identical output

Sources:

- https://ai.google.dev/gemini-api/docs/models/veo-3.1-generate-preview
- https://ai.google.dev/gemini-api/docs/veo

### Gemini Omni Flash

Official model code:

```text
gemini-omni-flash-preview
```

Documented profile:

- text, image, and video input
- video output
- 1,048,576-token total multimodal context window
- output video from 3 through 10 seconds at 720p and 24 FPS
- conversational generation and editing through the Interactions API
- multiple image references can be bound to roles
- no first-and-last-frame interpolation in the API
- no video extension in the API
- no separate negative-prompt parameter
- no system instructions, temperature, top-p, or stop sequences for video generation
- simple targeted edit instructions work better than long edit rewrites
- add `Keep everything else the same.` when a targeted edit must preserve unrelated content

Sources:

- https://ai.google.dev/gemini-api/docs/models/gemini-omni-flash
- https://ai.google.dev/gemini-api/docs/omni

## Prompt length

Do not state that video prompts have no published limit.

- Veo 3.1 API model cards publish a 1,024-token text-input limit.
- Gemini Omni Flash publishes a 1,048,576-token total multimodal context window.
- The reviewed sources do not publish one universal character limit for the Google Flow prompt editor.

A large context window does not make an enormous prompt desirable. Use references to carry appearance, keep action language unambiguous, and shorten prompts when adherence degrades.

The local token estimate is advisory because it does not use Google's production tokenizer.

## Timing

Exact one-second beats are a repository option, not a platform requirement.

Omni accepts natural timing language and interval syntax such as:

```text
[0-3s]: @Character walks toward the doorway.
[3-6s]: @Character stops and turns.
[6-10s]: @Character runs out of frame.
```

Use:

- `exact` for dense one-second choreography
- `coverage` for continuous broader intervals
- `loose` for ordered timing cues without full coverage
- `off` for untimed visual boards

## Reference workflows

### Veo

Veo reference-image generation uses up to three subject references. If more identity sources are necessary, build a plate from already approved images. Do not recreate identities from prose.

### Omni

Omni uses a separate multimodal reference workflow. Do not impose Veo's three-reference ceiling on Omni. Map canonical script handles to the current interface or API role tags.

```text
@Kwame -> <IMAGE_REF_0>
@CafeLadies -> <IMAGE_REF_1>
@SidewalkCafe -> <IMAGE_REF_2>
@YellowTaxi -> <IMAGE_REF_3>
```

## Frames and handoffs

Veo can use a first frame and, in supported modes, a last frame. These are strong continuity tools.

- first frame: begin from an approved visual state
- last frame: target an approved ending composition
- first and last: constrain both ends of the motion

Omni API does not currently support first-and-last-frame interpolation. Do not offer it under an Omni API profile.

## Extension

Use extension only when the selected surface and profile support it.

- The Veo API supports extension under documented restrictions.
- Flow currently performs eligible Veo extension through Veo 3.1 Lite.
- Omni API does not support extension.
- The reviewed Flow matrix lists Omni extension as coming soon.

## Conversational editing

Omni's defining workflow is iterative editing. For targeted edits, describe only the change:

```text
Remove the phone from @Kwame's hand. Keep everything else the same.
```

Long edit prompts can alter unrelated elements.

## Audio

Describe dialogue, sound effects, ambience, music, and intentional silence explicitly.

Do not assume every surface supports uploaded audio references or voice editing. Check the active interface and current documentation.

## Seed wording

Correct:

> Reusing a seed may slightly improve repeatability, but it does not guarantee identical output.

Incorrect:

> Reusing a seed makes the result repeatable.

## Storyboard image generation

Storyboard stills are separate image generations. A storyboard-generation prompt must:

1. command image generation in its first sentence
2. specify exact panel count and layout
3. prohibit written planning responses
4. prohibit extra frames and invented actions
5. return only the finished contact sheet

For a ten-second scene with four authored moments, use a 2x2 contact sheet. Use 3x3 only for nine explicitly authored moments.
