# Prompt templates

This directory contains copy-paste prompt contracts that are intended to be generated or filled with project-specific details.

## Storyboard contact sheet

Use `storyboard-contact-sheet.md` as the canonical visual-storyboard contract.

The preferred route is the executable generator:

```bash
python scripts/generate_storyboard_prompt.py examples/storyboard-spec.json \
  --output storyboard-package.md
```

The generated package separates:

1. internal operator notes
2. the exact image-generation prompt
3. the human approval checklist

Only section 2 is sent to the image generator.

Every generated character or location reference must use one canonical handle:

```text
@Kwame
@CafeLadies
@SidewalkCafe
```

Do not use bare names after a handle is declared. Do not use spaces or punctuation inside a handle.

For a ten-second scene with four authored states, use four panels in a 2x2 grid. Use a 3x3 grid only when all nine distinct frames were authored in advance.

Every storyboard generation prompt begins exactly with:

```text
GENERATE THE STORYBOARD IMAGE NOW.
```

The prompt must request the image immediately, declare the exact panel count and layout, prohibit a planning response, prohibit invented actions, and require only the completed contact sheet.
