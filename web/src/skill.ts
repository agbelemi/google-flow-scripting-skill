// Bundles the Skill's own Markdown files into the Gemini system instruction so
// the web app follows exactly the same rules as the repository.

import skillMd from "../../SKILL.md";
import orchestrator from "../../core/flow-orchestrator.md";
import storyArchitect from "../../core/flow-story-architect.md";
import assetManager from "../../core/flow-asset-manager.md";
import storyboardDirector from "../../core/flow-storyboard-director.md";
import continuityAuditor from "../../core/flow-continuity-auditor.md";
import flowFeatures from "../../reference/FLOW-FEATURES.md";
import templates from "../../reference/TEMPLATES.md";
import failureModes from "../../reference/FAILURE-MODES.md";
import playbook from "../../reference/PLAYBOOK.md";
import storyboardPrompt from "../../prompts/storyboard-contact-sheet.md";
import examplePackage from "../../examples/generated-storyboard-package.md";
import format2d from "../../formats/flow-2d-animation.md";
import format3d from "../../formats/flow-3d-animation.md";
import formatAds from "../../formats/flow-ads.md";
import formatDocumentary from "../../formats/flow-documentary.md";
import formatLiveAction from "../../formats/flow-live-action.md";
import formatMusicVideo from "../../formats/flow-music-video.md";
import type { BeatMode, Mode, Model, Surface } from "./validator.ts";

export const FORMATS: Record<string, { label: string; text: string }> = {
  "live-action": { label: "Live action", text: formatLiveAction },
  "3d-animation": { label: "3D animation", text: format3d },
  "2d-animation": { label: "2D animation", text: format2d },
  ads: { label: "Advertising", text: formatAds },
  documentary: { label: "Documentary", text: formatDocumentary },
  "music-video": { label: "Music video", text: formatMusicVideo },
};

export interface Profile {
  brief: string;
  surface: Surface;
  model: Model;
  mode: Mode;
  segmentLength: number;
  runtime: number;
  aspectRatio: "16:9" | "9:16";
  format: string;
  beatMode: BeatMode;
  audioPolicy: "generated" | "silence" | "post";
  textPolicy: "none" | "intentional";
  intentionalText?: string;
  notesLanguage: "vi" | "en";
  extraNotes?: string;
}

const PANELS: Record<number, string> = {
  4: "exactly 2 cinematic still-image panels in a 2x1 grid",
  6: "exactly 3 cinematic still-image panels in a 3x1 grid",
  8: "exactly 3 cinematic still-image panels in a 3x1 grid",
  10: "exactly 4 cinematic still-image panels in a 2x2 grid",
};

function beatRule(profile: Profile): string {
  const n = profile.segmentLength;
  switch (profile.beatMode) {
    case "exact":
      return `Inside every VIDEO PROMPT, under WHAT HAPPENS:, write exactly ${n} beat lines, one per second, each starting at the beginning of the line: 0-1s:, 1-2s:, ... ${n - 1}-${n}s:. No other line from the first segment to the end of the response may start with a time range.`;
    case "coverage":
      return `Inside every VIDEO PROMPT, under WHAT HAPPENS:, write beat lines such as 0-3s:, 3-7s:, 7-${n}s: that start at 0s, end at ${n}s, are in order, and have no gaps or overlaps.`;
    case "loose":
      return `Inside every VIDEO PROMPT, under WHAT HAPPENS:, write beat lines in chronological order (for example 0-2s:) that stay between 0s and ${n}s.`;
    default:
      return "Timed beat lines are optional; describe the action in natural timing language.";
  }
}

function audioRule(profile: Profile): string {
  switch (profile.audioPolicy) {
    case "generated":
      return "Every VIDEO PROMPT contains an AUDIO: block with dialogue (if any), SFX, ambience, music, and what must not be heard.";
    case "silence":
      return "Every VIDEO PROMPT contains the line AUDIO: Intentional silence.";
    default:
      return "Sound is added in post. Write AUDIO: No generated audio; sound is added in post. in every VIDEO PROMPT.";
  }
}

function appContract(profile: Profile): string {
  const notes = profile.notesLanguage === "vi" ? "Vietnamese" : "English";
  const panels = PANELS[profile.segmentLength]
    ? `For ${profile.segmentLength}-second segments each storyboard uses ${PANELS[profile.segmentLength]}.`
    : `For ${profile.segmentLength}-second segments choose the smallest panel count and layout (2x1, 3x1, 2x2) that covers the authored moments, and state it explicitly.`;
  return `# WEB APP OUTPUT CONTRACT

You are the engine of a web app that implements the google-flow-scripting Skill reproduced below. You have no tools, files, or scripts: everything you need is in this instruction. The user will paste your prompts into Google Flow by hand. After you answer, the app runs an exact port of scripts/validate.py over your whole response, so follow these machine-readable rules exactly.

## Response shape
- Produce the complete production package in ONE response, in the order of SKILL.md section "Build the production package" (items 1 to 9). Do not ask questions; record assumptions in item 1 instead. For item 8 (mechanical validation results) write one line saying the app runs the validator automatically.
- Write explanations, operator notes, assumptions, checklists, and the continuity audit in ${notes}. Write every copy-paste generation prompt in English.
- Use Markdown headings for sections. Put each copy-paste prompt inside its own fenced block that opens with \`\`\`text and closes with \`\`\`.
- Directly above each fenced prompt, put one marker line, alone on its line, exactly one of:
  - \`REFERENCE SHEET - @Handle\` for character or location reference images (asset section, before the segments)
  - \`STORYBOARD CONTACT SHEET PROMPT\` for the storyboard of a segment
  - \`VIDEO PROMPT\` for the video prompt of a segment
- Each segment section starts with a heading line \`## SEGMENT <number>\` (1, 2, 3...). Inside a segment, in this order: operator note, STORYBOARD CONTACT SHEET PROMPT, approval checklist, VIDEO PROMPT.
- Those marker words open validator blocks. Never start any other line with SEGMENT, SEG, VIDEO PROMPT, IMAGE PROMPT, STORYBOARD, or REFERENCE SHEET. In the segment map (item 2) use a Markdown table whose rows start with "|", and never start a line with a time range such as 0-8s:.
- The operator note heading is \`OPERATOR NOTE - DO NOT PASTE INTO THE GENERATOR\`; the checklist heading is \`DO NOT INCLUDE THIS CHECKLIST IN THE GENERATION PROMPT\`.

## Prompt rules checked by the validator
- First non-empty line of every VIDEO PROMPT and REFERENCE SHEET block: ${
    profile.textPolicy === "none"
      ? "`NO TEXT IN THE IMAGE: do not render any words, letters, numbers, captions, subtitles, labels, logos, or watermarks.`"
      : `\`INTENTIONAL TEXT IN THE IMAGE: ${profile.intentionalText || "<exact words, surface, placement>"}; no other text.\``
  }
- First non-empty line of every storyboard block is exactly \`GENERATE THE STORYBOARD IMAGE NOW.\` and the same text policy line follows within the first lines.
- Every storyboard block contains these exact phrases: "Do not write a storyboard", "storyboard contact sheet", "exactly N cinematic still-image panels" with the numeric count, a layout token (2x1, 3x1, 2x2, or 3x3), "Do not invent additional actions.", "Do not ask for permission before generating.", and "Return only the completed".
- ${panels} Panel sections start lines "PANEL A - ...", "PANEL B - ...", in order, once each. Write the reading order on a single line that starts with "Panel order:".
- ${beatRule(profile)}
- ${audioRule(profile)}
- Every character, group, and location has one canonical handle: @ followed by PascalCase letters and digits only (e.g. @Kwame, @CafeLadies, @SidewalkCafe). Once a handle exists, write that name with @ everywhere in the response (prompts, notes, tables, audit), never bare. Never use @ for anything else (no emails, no social handles, no underscores or hyphens after @).
- Lines starting with CHARACTER REFERENCES:, LOCATION REFERENCE:, OTHER ATTACHED REFERENCES:, ATTACH:, CAST:, WHO IS IN THIS SHOT:, REFERENCED SUBJECTS:, or REFERENCE HANDLE: list only comma-separated @Handles (descriptions may follow inside parentheses) or NONE. Any line starting with LOCATION: begins with an @LocationHandle, including in operator notes.
- Never use an em dash anywhere in the response, in any language. Use a colon, comma, full stop, parentheses, or a spaced hyphen.
- Never write colour temperatures (5600K), hex colours (#AABBCC), or set names in brackets such as (Old Market Street).
- Never use backward references: "the same <person/character/woman/man/location/prop/...>", "as before", "as established", "as previously", "as earlier", "same as above", "previously seen/shown/established", "from segment 2", "as in shot 3", "continuing from the previous", "still holding/wearing/wet/...". Restate every state in full.
- Aspect ratio is ${profile.aspectRatio}; never mention 1:1, 4:3, 21:9, or 2.39:1.
${profile.surface === "gemini-api" && profile.model.startsWith("veo") ? "- Keep each VIDEO PROMPT under about 900 words-and-punctuation tokens (Veo API limit is 1,024 tokens).\n" : ""}- Do not use \`\`\`example, \`\`\`bad, \`\`\`dont, or \`\`\`avoid fences for real prompts; the validator skips them.
`;
}

export function buildSystemInstruction(profile: Profile): string {
  const format = FORMATS[profile.format] ?? FORMATS["live-action"];
  const files: [string, string][] = [
    ["SKILL.md", skillMd],
    ["core/flow-orchestrator.md", orchestrator],
    ["core/flow-story-architect.md", storyArchitect],
    ["core/flow-asset-manager.md", assetManager],
    ["core/flow-storyboard-director.md", storyboardDirector],
    ["core/flow-continuity-auditor.md", continuityAuditor],
    [`formats/flow-${profile.format}.md`, format.text],
    ["reference/FLOW-FEATURES.md", flowFeatures],
    ["reference/TEMPLATES.md", templates],
    ["reference/FAILURE-MODES.md", failureModes],
    ["reference/PLAYBOOK.md", playbook],
    ["prompts/storyboard-contact-sheet.md", storyboardPrompt],
    ["examples/generated-storyboard-package.md (style example for one segment)", examplePackage],
  ];
  const bundle = files.map(([name, text]) => `\n\n===== FILE: ${name} =====\n\n${text}`).join("");
  return `${appContract(profile)}\n# SKILL FILES${bundle}`;
}

const AUDIO_LABEL: Record<Profile["audioPolicy"], string> = {
  generated: "generated audio (dialogue, effects, ambience, music as needed)",
  silence: "intentional silence",
  post: "visual-only previs; sound added in post",
};

export function buildUserRequest(profile: Profile): string {
  const segments = Math.max(1, Math.ceil(profile.runtime / profile.segmentLength));
  return `PRODUCTION PROFILE (already confirmed by the user; do not ask again)
SURFACE: ${profile.surface === "flow" ? "Google Flow" : "Gemini API"}
MODEL: ${profile.model}
MODE: ${profile.mode}
SEGMENT LENGTH: ${profile.segmentLength} seconds
TARGET RUNTIME: about ${profile.runtime} seconds (about ${segments} segment${segments > 1 ? "s" : ""})
ASPECT RATIO: ${profile.aspectRatio}
FORMAT: ${FORMATS[profile.format]?.label ?? profile.format}
BEAT MODE: ${profile.beatMode}
AUDIO POLICY: ${AUDIO_LABEL[profile.audioPolicy]}
TEXT POLICY: ${profile.textPolicy === "none" ? "no text in the image" : `intentional text: ${profile.intentionalText || "(see brief)"}`}

BRIEF
${profile.brief.trim()}
${profile.extraNotes?.trim() ? `\nCAST, LOCATIONS, AND OTHER NOTES\n${profile.extraNotes.trim()}\n` : ""}
Write the complete production package now.`;
}

export function buildRevisionRequest(findings: string): string {
  return `The app's validator (exact port of scripts/validate.py) reported these findings on your package:

${findings}

Fix every finding without changing the story, handles, or approved structure. Return the COMPLETE corrected package from the beginning, not only the changed parts.`;
}
