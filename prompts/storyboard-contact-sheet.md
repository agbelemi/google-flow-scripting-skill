<!-- validate:ignore-file -->
# Canonical storyboard contact-sheet prompt

The storyboard director and `scripts/generate_storyboard_prompt.py` use this contract. Keep the quoted rule and first sentence unchanged.

> "A storyboard-generation prompt must command image generation in its first sentence, declare the exact output count and layout, prohibit planning responses, and enumerate forbidden invented actions."

```text
GENERATE THE STORYBOARD IMAGE NOW.

Do not write a storyboard, scene breakdown, asset list, explanation, proposal, or follow-up question.

Create exactly [PANEL_COUNT] cinematic still-image panels arranged in one [LAYOUT] storyboard contact sheet.

Do not create additional panels.
Do not invent additional actions.
Do not ask for permission before generating.

NO TEXT IN THE IMAGE: do not render any words, letters, numbers, panel labels, captions, subtitles, timecodes, logos, or watermarks.

CHARACTER REFERENCES: [@CharacterHandles or NONE]
LOCATION REFERENCE: [@LocationHandle]

Use every attached reference as the authoritative visual source. Keep faces, clothing, body proportions, environment layout, lighting direction, props, and physical state consistent across all panels.

[PANEL SECTIONS IN AUTHORED ORDER]

Return only the completed storyboard contact sheet image.
```

For a 10-second segment with four authored moments, use four panels in a 2x2 grid. A 3x3 grid is allowed only when nine distinct frames are explicitly authored.
