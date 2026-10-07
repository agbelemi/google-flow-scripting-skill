// TypeScript port of scripts/validate.py. Keep the two in lockstep: the
// parity test in web/test/parity.test.ts runs both against the shared fixtures
// and fails on any difference.

export type Surface = "unspecified" | "flow" | "gemini-api";
export type Model =
  | "unspecified"
  | "veo-3.1"
  | "veo-3.1-lite"
  | "veo-3.1-fast"
  | "veo-3.1-quality"
  | "omni-flash"
  | "other";
export type Mode =
  | "unspecified"
  | "text-to-video"
  | "first-frame"
  | "first-last-frame"
  | "references-to-video"
  | "video-edit"
  | "extend";
export type BeatMode = "exact" | "coverage" | "loose" | "off";

export interface ValidateOptions {
  segmentLength?: number | null;
  beatMode?: BeatMode;
  surface?: Surface;
  model?: Model;
  mode?: Mode;
  requireAudio?: boolean;
}

export interface Finding {
  line: number;
  snippet: string;
  reason: string;
}

export interface ValidationResult {
  skipped: boolean;
  passed: boolean;
  disabled_checks: string[];
  checks: Record<string, Finding[]>;
}

export const SURFACES: Surface[] = ["unspecified", "flow", "gemini-api"];
export const MODELS: Model[] = [
  "unspecified",
  "veo-3.1",
  "veo-3.1-lite",
  "veo-3.1-fast",
  "veo-3.1-quality",
  "omni-flash",
  "other",
];
export const MODES: Mode[] = [
  "unspecified",
  "text-to-video",
  "first-frame",
  "first-last-frame",
  "references-to-video",
  "video-edit",
  "extend",
];
export const BEAT_MODES: BeatMode[] = ["exact", "coverage", "loose", "off"];

export const CHECK_LABELS: Record<string, string> = {
  backward_references: "Backward references",
  text_bleed_tokens: "Text-bleed tokens",
  em_dashes: "Em dashes",
  text_policy: "Text policy",
  reference_handles: "Reference handles",
  storyboard_contract: "Storyboard contract",
  beat_timeline: "Beat timeline",
  unsupported_specifications: "Unsupported specifications",
  model_duration: "Model duration",
  veo_prompt_length: "Veo prompt length estimate",
  audio_direction: "Audio direction",
};

type Issue = [number, string, string];
type Pattern = [string, string];

const BACKWARD_REFS: Pattern[] = [
  [String.raw`\bfrom (?:segment|seg|shot)\s+\d+`, "refers back to another segment"],
  [String.raw`\b(?:as|like) in (?:scene|segment|seg|shot)\s+\d+`, "refers back to another shot"],
  [String.raw`\bidentical to (?:scene|segment|seg|shot)\s+\d+`, "refers back to another shot"],
  [String.raw`\breturns? to (?:scene|segment|seg|shot)\s+\d+`, "refers back to another shot"],
  [
    String.raw`\bthe same (?:trader|vendor|man|woman|person|character|customer|dog|cat|child|guy|lady|prop|costume|vehicle|room|location)\b`,
    '"the same X" assumes implicit memory',
  ],
  [String.raw`\bas (?:before|established|previously|earlier)\b`, "refers to earlier context"],
  [
    String.raw`\bcontinuing from (?:before|the previous|earlier)\b`,
    "vague continuation; describe the incoming frame in full",
  ],
  [
    String.raw`\bstill (?:wet|dirty|torn|bleeding|holding|wearing|soaked|muddy)\b`,
    '"still X" assumes memory; state the condition outright',
  ],
  [String.raw`\bsame as (?:above|before|previous)\b`, "refers to earlier content"],
  [String.raw`\bpreviously (?:seen|shown|established)\b`, "refers to earlier content"],
];

const TOKEN_LEAKS: Pattern[] = [
  [String.raw`\b\d{3,5}\s?K\b`, "colour-temperature value; use plain words"],
  [String.raw`#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})\b`, "hex colour code; use a colour name"],
  [
    String.raw`#(?=[0-9A-Fa-f]{3,4}\b)(?=[0-9A-Fa-f]*[A-Fa-f])[0-9A-Fa-f]{3,4}\b`,
    "short hex colour code; use a colour name",
  ],
  [
    String.raw`\((?:[A-Z][A-Za-z']*\s+){1,4}(?:Lane|Market|Street|Room|Interior|Exterior|House|Shop|Studio|Stall|Path|Clearing)\)`,
    "set name in brackets; it may be rendered as a caption",
  ],
];

const SPEC_VIOLATIONS: Pattern[] = [
  [
    String.raw`\b(?:aspect ratio|ratio)\s*[:\-]?\s*(?:1:1|4:3|2\.39:1|21:9)\b`,
    "this workflow targets native 16:9 or 9:16 output; crop other shapes in post",
  ],
  [
    String.raw`\b(?:square 1:1|classic 4:3|cinemascope 2\.39:1)\b`,
    "this workflow targets native 16:9 or 9:16 output; crop other shapes in post",
  ],
];

const IGNORE_FILE = /<!--\s*validate:ignore-file\s*-->/i;
const EXAMPLE_FENCE = /^```(?:example|counterexample|bad|dont|avoid)\b.*?^```/gims;

const TEXT_POLICY_MARKER = /^(?:NO TEXT IN THE IMAGE\b|INTENTIONAL TEXT(?: IN THE IMAGE)?\s*:)/i;
const PROMPT_MARKER_SRC = String.raw`^[ \t]*(?:[#>*_\-]+[ \t]*)*(?:VIDEO PROMPT|STORYBOARD IMAGE PROMPT|STORYBOARD CONTACT SHEET PROMPT|IMAGE PROMPT|REFERENCE SHEET)`;
const VIDEO_PROMPT_MARKER_SRC = String.raw`^[ \t]*(?:[#>*_\-]+[ \t]*)*VIDEO PROMPT`;
const STORYBOARD_PROMPT_MARKER_SRC = String.raw`^[ \t]*(?:[#>*_\-]+[ \t]*)*(?:STORYBOARD IMAGE PROMPT|STORYBOARD CONTACT SHEET PROMPT)`;
const SEGMENT_MARKER_SRC = String.raw`^[ \t]*(?:[#>*_\-]+[ \t]*)*(?:SEGMENT|SEG)\s+([\d.]+)`;
const BEAT_LINE_SRC = String.raw`^[ \t]*\[?(\d+)\s*-\s*(\d+)\s*s\]?\s*:`;
const AUDIO_MARKER = /^[ \t]*AUDIO\s*:/im;
const FENCE_LINE = /^(?:```|~~~)/;
const CANONICAL_HANDLE = /^@[A-Za-z][A-Za-z0-9]*$/;
const ANY_AT_TOKEN_SRC = String.raw`@[A-Za-z0-9_-]+`;

const REFERENCE_FIELD_SRC = String.raw`^[ \t]*(?:CHARACTER REFERENCES?|LOCATION REFERENCES?|LOCATION REFERENCE|REFERENCE HANDLE|REFERENCES TO ATTACH|SOURCE REFERENCES|OTHER ATTACHED REFERENCES|ATTACH|CAST|WHO IS IN THIS SHOT|WHO IS IN THIS FRAME|REFERENCED SUBJECTS)\s*:\s*(.+)$`;
const LOCATION_FIELD_SRC = String.raw`^[ \t]*LOCATION\s*:\s*(.+)$`;

const PROMPT_MARKER = () => new RegExp(PROMPT_MARKER_SRC, "gim");
const VIDEO_PROMPT_MARKER = () => new RegExp(VIDEO_PROMPT_MARKER_SRC, "gim");
const STORYBOARD_PROMPT_MARKER = () => new RegExp(STORYBOARD_PROMPT_MARKER_SRC, "gim");
const SEGMENT_MARKER = () => new RegExp(SEGMENT_MARKER_SRC, "gim");

const range = (start: number, stop: number): number[] =>
  Array.from({ length: stop - start }, (_, index) => start + index);

const FLOW_DURATIONS: Record<string, number[]> = {
  "veo-3.1": [4, 6, 8],
  "veo-3.1-lite": [4, 6, 8],
  "veo-3.1-fast": [4, 6, 8],
  "veo-3.1-quality": [8],
  "omni-flash": [4, 6, 8, 10],
};
const API_DURATIONS: Record<string, number[]> = {
  "veo-3.1": [4, 6, 8],
  "veo-3.1-lite": [4, 6, 8],
  "veo-3.1-fast": [4, 6, 8],
  "veo-3.1-quality": [4, 6, 8],
  "omni-flash": range(3, 11),
};

// Duration sets are based on the documented surface, model, and mode profiles
// reviewed in reference/FLOW-FEATURES.md. An empty list means unsupported.
export const MODE_DURATIONS: Record<string, Record<string, Record<string, number[]>>> = {
  flow: {
    "veo-3.1": {
      "text-to-video": [4, 6, 8],
      "first-frame": [4, 6, 8],
      "first-last-frame": [4, 6, 8],
      "references-to-video": [8],
      "video-edit": [],
      extend: [],
    },
    "veo-3.1-lite": {
      "text-to-video": [4, 6, 8],
      "first-frame": [4, 6, 8],
      "first-last-frame": [4, 6, 8],
      "references-to-video": [8],
      "video-edit": [],
      extend: [8],
    },
    "veo-3.1-fast": {
      "text-to-video": [4, 6, 8],
      "first-frame": [4, 6, 8],
      "first-last-frame": [4, 6, 8],
      "references-to-video": [8],
      "video-edit": [],
      extend: [],
    },
    "veo-3.1-quality": {
      "text-to-video": [8],
      "first-frame": [8],
      "first-last-frame": [8],
      "references-to-video": [],
      "video-edit": [],
      extend: [],
    },
    "omni-flash": {
      "text-to-video": [4, 6, 8, 10],
      "first-frame": [4, 6, 8, 10],
      "first-last-frame": [],
      "references-to-video": [4, 6, 8, 10],
      "video-edit": [4, 6, 8, 10],
      extend: [],
    },
  },
  "gemini-api": {
    "veo-3.1": {
      "text-to-video": [4, 6, 8],
      "first-frame": [4, 6, 8],
      "first-last-frame": [8],
      "references-to-video": [8],
      "video-edit": [],
      extend: [8],
    },
    "veo-3.1-lite": {
      "text-to-video": [4, 6, 8],
      "first-frame": [4, 6, 8],
      "first-last-frame": [8],
      "references-to-video": [8],
      "video-edit": [],
      extend: [8],
    },
    "veo-3.1-fast": {
      "text-to-video": [4, 6, 8],
      "first-frame": [4, 6, 8],
      "first-last-frame": [8],
      "references-to-video": [8],
      "video-edit": [],
      extend: [8],
    },
    "veo-3.1-quality": {
      "text-to-video": [4, 6, 8],
      "first-frame": [4, 6, 8],
      "first-last-frame": [8],
      "references-to-video": [8],
      "video-edit": [],
      extend: [8],
    },
    "omni-flash": {
      "text-to-video": range(3, 11),
      "first-frame": range(3, 11),
      "first-last-frame": [],
      "references-to-video": range(3, 11),
      "video-edit": range(3, 11),
      extend: [],
    },
  },
};

// Python slices strings by code point, JavaScript by UTF-16 unit.
function head(value: string, length = 60): string {
  return Array.from(value).slice(0, length).join("");
}

// Python str.strip() removes Unicode whitespace plus a few control separators.
const PY_WHITESPACE = String.raw`\s\x1c-\x1f\x85`;
const STRIP_RE = new RegExp(`^[${PY_WHITESPACE}]+|[${PY_WHITESPACE}]+$`, "gu");
function strip(value: string): string {
  return value.replace(STRIP_RE, "");
}

// Mirrors str.splitlines(keepends=True) for the separators Python recognises.
function splitLinesKeepEnds(value: string): string[] {
  const lines: string[] = [];
  const separator = new RegExp("\\r\\n|[\\n\\r\\x0b\\x0c\\x1c\\x1d\\x1e\\x85\\u2028\\u2029]", "g");
  let last = 0;
  for (const match of value.matchAll(separator)) {
    const end = (match.index ?? 0) + match[0].length;
    lines.push(value.slice(last, end));
    last = end;
  }
  if (last < value.length) lines.push(value.slice(last));
  return lines;
}

function compareIssues(left: Issue, right: Issue): number {
  for (let index = 0; index < 3; index += 1) {
    const a = left[index];
    const b = right[index];
    if (a < b) return -1;
    if (a > b) return 1;
  }
  return 0;
}

function sortIssues(issues: Issue[]): Issue[] {
  return [...issues].sort(compareIssues);
}

function uniqueIssues(issues: Issue[]): Issue[] {
  const seen = new Set<string>();
  return issues.filter((issue) => {
    const key = JSON.stringify(issue);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function lineOf(text: string, position: number): number {
  let count = 1;
  for (let index = text.indexOf("\n"); index !== -1 && index < position; index = text.indexOf("\n", index + 1)) {
    count += 1;
  }
  return count;
}

function blankExampleFences(text: string): string {
  return text.replace(EXAMPLE_FENCE, (match) => "\n".repeat(match.split("\n").length - 1));
}

function blocksBetween(text: string, marker: RegExp): [number, string][] {
  const starts = Array.from(text.matchAll(marker), (match) => match.index ?? 0);
  return starts.map((start, index) => {
    const end = index + 1 < starts.length ? starts[index + 1] : text.length;
    return [start, text.slice(start, end)];
  });
}

function semanticLines(block: string): [number, string][] {
  const result: [number, string][] = [];
  const lines = splitLinesKeepEnds(block);
  let offset = lines.length ? lines[0].length : 0;
  for (const line of lines.slice(1)) {
    const stripped = strip(line);
    if (stripped && !FENCE_LINE.test(stripped) && !stripped.startsWith("<!--")) {
      result.push([offset, stripped]);
    }
    offset += line.length;
  }
  return result;
}

function firstLineHeader(block: string, fallback: string): string {
  return strip(strip(block).split("\n")[0]) || fallback;
}

function checkPatterns(text: string, patterns: Pattern[]): Issue[] {
  const findings: Issue[] = [];
  for (const [pattern, reason] of patterns) {
    for (const match of text.matchAll(new RegExp(pattern, "gi"))) {
      findings.push([lineOf(text, match.index ?? 0), strip(match[0]), reason]);
    }
  }
  return sortIssues(findings);
}

function checkEmDashes(text: string): Issue[] {
  const findings: Issue[] = [];
  for (const match of text.matchAll(new RegExp(String.fromCharCode(0x2014), "g"))) {
    findings.push([lineOf(text, match.index ?? 0), "em dash", "em dashes are prohibited; use other punctuation"]);
  }
  return findings;
}

function checkTextPolicy(text: string): Issue[] {
  const findings: Issue[] = [];
  for (const [start, block] of blocksBetween(text, PROMPT_MARKER())) {
    const header = firstLineHeader(block, "(prompt)");
    const isStoryboard = new RegExp(STORYBOARD_PROMPT_MARKER_SRC, "i").test(header);
    const lines = semanticLines(block);
    if (!lines.length) {
      findings.push([lineOf(text, start), head(header), "prompt has no content"]);
      continue;
    }

    if (isStoryboard) {
      if (lines[0][1] !== "GENERATE THE STORYBOARD IMAGE NOW.") {
        findings.push([
          lineOf(text, start + lines[0][0]),
          head(lines[0][1]),
          "storyboard prompt must begin exactly with GENERATE THE STORYBOARD IMAGE NOW.",
        ]);
      }
      const early = lines.slice(0, 25);
      if (!early.some(([, value]) => TEXT_POLICY_MARKER.test(value))) {
        findings.push([
          lineOf(text, start),
          head(header),
          "storyboard prompt must place an explicit text policy near the top",
        ]);
      }
    } else if (!TEXT_POLICY_MARKER.test(lines[0][1])) {
      findings.push([
        lineOf(text, start + lines[0][0]),
        head(lines[0][1]),
        "the first semantic prompt line must declare NO TEXT or INTENTIONAL TEXT",
      ]);
    }
  }
  return findings;
}

function counter<T>(values: T[], key: (value: T) => string): Map<string, { value: T; count: number }> {
  const counts = new Map<string, { value: T; count: number }>();
  for (const value of values) {
    const id = key(value);
    const entry = counts.get(id);
    if (entry) entry.count += 1;
    else counts.set(id, { value, count: 1 });
  }
  return counts;
}

function checkStoryboardContract(text: string, segmentLength: number | null): Issue[] {
  const findings: Issue[] = [];
  const expectedByLength: Record<number, [number, string]> = {
    4: [2, "2x1"],
    6: [3, "3x1"],
    8: [3, "3x1"],
    10: [4, "2x2"],
  };

  for (const [start, block] of blocksBetween(text, STORYBOARD_PROMPT_MARKER())) {
    const header = firstLineHeader(block, "(storyboard prompt)");
    const lower = block.toLowerCase();
    const required: [string, string][] = [
      ["do not write a storyboard", "must prohibit a written storyboard response"],
      ["storyboard contact sheet", "must request one finished storyboard contact sheet"],
      ["do not invent additional actions", "must prohibit invented actions"],
      ["return only the completed", "must require only the completed image output"],
      ["do not ask for permission", "must prohibit permission questions"],
    ];
    for (const [phrase, reason] of required) {
      if (!lower.includes(phrase)) findings.push([lineOf(text, start), head(header), reason]);
    }

    const countMatch = /exactly\s+(\d+)\s+(?:cinematic\s+still-image\s+)?panels?/i.exec(block);
    const layoutMatch = /\b(2x1|3x1|2x2|3x3)\b/i.exec(block);
    if (!countMatch) findings.push([lineOf(text, start), head(header), "must declare the exact numeric panel count"]);
    if (!layoutMatch) findings.push([lineOf(text, start), head(header), "must declare a supported grid layout"]);

    const panelLabels = Array.from(block.matchAll(/^[ \t]*PANEL\s+([A-I])(?:\s|:|-)/gim), (match) => match[1]);
    const normalisedLabels = panelLabels.map((label) => label.toUpperCase());
    const duplicateLabels = Array.from(counter(normalisedLabels, (label) => label).values())
      .filter((entry) => entry.count > 1)
      .map((entry) => entry.value)
      .sort();
    if (duplicateLabels.length) {
      findings.push([lineOf(text, start), duplicateLabels.join(", "), "duplicate storyboard panel labels"]);
    }
    if (countMatch) {
      const declaredCount = parseInt(countMatch[1], 10);
      const expectedLabels = range(0, declaredCount).map((index) => String.fromCharCode(65 + index));
      if (normalisedLabels.join("\u0000") !== expectedLabels.join("\u0000")) {
        findings.push([
          lineOf(text, start),
          normalisedLabels.join(", ") || "no panel labels",
          "panel sections must appear once each in declared order: " + expectedLabels.join(", "),
        ]);
      }
    }

    if (segmentLength !== null && segmentLength in expectedByLength && countMatch && layoutMatch) {
      const [expectedCount, expectedLayout] = expectedByLength[segmentLength];
      const actualCount = parseInt(countMatch[1], 10);
      const actualLayout = layoutMatch[1].toLowerCase();
      const isExplicitNine = actualCount === 9 && actualLayout === "3x3" && lower.includes("nine distinct");
      if (!isExplicitNine && (actualCount !== expectedCount || actualLayout !== expectedLayout)) {
        findings.push([
          lineOf(text, start),
          `${actualCount} panels in ${actualLayout}`,
          `${segmentLength}s defaults to ${expectedCount} panels in ${expectedLayout}`,
        ]);
      }
    }
  }
  return findings;
}

function splitTopLevelCommas(value: string): string[] {
  const items: string[] = [];
  let current = "";
  let depth = 0;
  for (const char of value) {
    if ("([{".includes(char)) depth += 1;
    else if (")]}".includes(char) && depth) depth -= 1;
    if (char === "," && depth === 0) {
      items.push(strip(current));
      current = "";
    } else {
      current += char;
    }
  }
  if (current) items.push(strip(current));
  return items;
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function checkReferenceHandles(text: string): Issue[] {
  const findings: Issue[] = [];

  for (const match of text.matchAll(new RegExp(ANY_AT_TOKEN_SRC, "g"))) {
    const token = match[0];
    if (!CANONICAL_HANDLE.test(token)) {
      findings.push([
        lineOf(text, match.index ?? 0),
        head(token),
        "reference handles must be @PascalCase with letters and numbers only",
      ]);
    }
  }

  for (const match of text.matchAll(new RegExp(REFERENCE_FIELD_SRC, "gim"))) {
    const fieldValue = strip(match[1]);
    const fieldName = strip(match[0].split(":")[0]);
    const value = strip(fieldValue.split(/\bNo other named characters\b/i)[0]);
    if (["NONE", "N/A"].includes(value.toUpperCase())) continue;
    for (const item of splitTopLevelCommas(value)) {
      const stripped = strip(item.replace(/^\[\d+\]\s*/, ""));
      if (!stripped || ["NONE", "N/A"].includes(stripped.toUpperCase())) continue;
      if (!stripped.startsWith("@")) {
        findings.push([
          lineOf(text, match.index ?? 0),
          head(stripped),
          `${fieldName} contains a reference without a leading @`,
        ]);
      } else if (/^@[A-Za-z][A-Za-z0-9]*\s+[A-Z][A-Za-z0-9]*/.test(stripped)) {
        findings.push([
          lineOf(text, match.index ?? 0),
          head(stripped),
          "reference handles cannot contain spaces; convert the name to PascalCase",
        ]);
      }
    }
  }

  for (const match of text.matchAll(new RegExp(LOCATION_FIELD_SRC, "gim"))) {
    const value = strip(match[1]);
    if (value && !value.startsWith("@")) {
      findings.push([lineOf(text, match.index ?? 0), head(value), "LOCATION must begin with a canonical @LocationHandle"]);
    }
  }

  // Once a canonical handle is declared, the same exact asset name must not
  // appear bare inside prompt blocks.
  const handles = Array.from(
    new Set(
      Array.from(text.matchAll(new RegExp(ANY_AT_TOKEN_SRC, "g")), (match) => match[0])
        .filter((token) => CANONICAL_HANDLE.test(token))
        .map((token) => token.slice(1)),
    ),
  ).sort();
  if (handles.length) {
    for (const [promptStart, block] of blocksBetween(text, PROMPT_MARKER())) {
      for (const handle of handles) {
        const pattern = new RegExp(String.raw`(?<!@)\b${escapeRegExp(handle)}\b`, "g");
        for (const match of block.matchAll(pattern)) {
          findings.push([
            lineOf(text, promptStart + (match.index ?? 0)),
            handle,
            `referenced asset must be written as @${handle}`,
          ]);
        }
      }
    }
  }

  return sortIssues(uniqueIssues(findings));
}

function checkAudio(text: string): Issue[] {
  const findings: Issue[] = [];
  for (const [start, block] of blocksBetween(text, VIDEO_PROMPT_MARKER())) {
    if (!AUDIO_MARKER.test(block)) {
      const header = strip(strip(block).split("\n")[0]);
      findings.push([
        lineOf(text, start),
        head(header) || "(video prompt)",
        "no AUDIO block; use AUDIO: Intentional silence. when silence is deliberate",
      ]);
    }
  }
  return findings;
}

type Interval = [number, number];

function formatIntervals(intervals: Interval[], limit = 4): string {
  return intervals
    .slice(0, limit)
    .map(([start, end]) => `${start}-${end}s`)
    .join(", ");
}

function videoPromptRegion(segmentBlock: string): string {
  const videoMatch = new RegExp(VIDEO_PROMPT_MARKER_SRC, "im").exec(segmentBlock);
  if (!videoMatch) return segmentBlock;
  let end = segmentBlock.length;
  const marker = PROMPT_MARKER();
  marker.lastIndex = videoMatch.index + videoMatch[0].length;
  const next = marker.exec(segmentBlock);
  if (next) end = next.index;
  return segmentBlock.slice(videoMatch.index, end);
}

function compareIntervals(left: Interval, right: Interval): number {
  return left[0] - right[0] || left[1] - right[1];
}

function intervalProblems(raw: Interval[], segmentLength: number, mode: BeatMode): string[] {
  const problems: string[] = [];
  const key = (interval: Interval) => `${interval[0]},${interval[1]}`;
  const counts = counter(raw, key);
  const duplicates = Array.from(counts.values())
    .filter((entry) => entry.count > 1)
    .map((entry) => entry.value);
  if (duplicates.length) problems.push(`duplicate interval(s): ${formatIntervals(duplicates)}`);

  const sorted = [...raw].sort(compareIntervals);
  if (raw.some((interval, index) => compareIntervals(interval, sorted[index]) !== 0)) {
    problems.push("intervals are out of chronological order");
  }

  const reversedIntervals = raw.filter(([start, end]) => end <= start);
  if (reversedIntervals.length) {
    problems.push(`reversed or zero-length interval(s): ${formatIntervals(reversedIntervals)}`);
  }

  const outOfRange = raw.filter(([start, end]) => start < 0 || end > segmentLength);
  if (outOfRange.length) problems.push(`out-of-range interval(s): ${formatIntervals(outOfRange)}`);

  if (mode === "loose") return problems;

  const ordered = raw;
  if (ordered.length) {
    if (ordered[0][0] !== 0) problems.push(`timeline starts at ${ordered[0][0]}s, expected 0s`);
    const last = ordered[ordered.length - 1];
    if (last[1] !== segmentLength) problems.push(`timeline ends at ${last[1]}s, expected ${segmentLength}s`);
  }

  for (let index = 0; index + 1 < ordered.length; index += 1) {
    const left = ordered[index];
    const right = ordered[index + 1];
    if (left[1] < right[0]) problems.push(`gap between ${left[1]}s and ${right[0]}s`);
    else if (left[1] > right[0]) problems.push(`overlap between ${right[0]}s and ${left[1]}s`);
  }

  if (mode === "exact") {
    const expected: Interval[] = range(0, segmentLength).map((second) => [second, second + 1]);
    const expectedKeys = new Set(expected.map(key));
    const badLength = raw.filter(([start, end]) => end - start !== 1);
    if (badLength.length) problems.push(`non-one-second interval(s): ${formatIntervals(badLength)}`);
    const missing = expected.filter((interval) => !counts.has(key(interval)));
    const unexpected = raw.filter((interval) => !expectedKeys.has(key(interval)));
    if (raw.length !== segmentLength) problems.push(`${raw.length} beat lines, expected ${segmentLength}`);
    if (missing.length) problems.push(`missing expected interval(s): ${formatIntervals(missing)}`);
    if (unexpected.length) problems.push(`unexpected interval(s): ${formatIntervals(unexpected)}`);
  }

  return problems;
}

function checkBeats(text: string, segmentLength: number, mode: BeatMode): Issue[] {
  if (mode === "off") return [];

  const findings: Issue[] = [];
  for (const [start, block] of blocksBetween(text, SEGMENT_MARKER())) {
    const segmentMatch = new RegExp(SEGMENT_MARKER_SRC, "im").exec(block);
    const segmentId = segmentMatch ? segmentMatch[1] : "?";
    const videoPromptFound = new RegExp(VIDEO_PROMPT_MARKER_SRC, "im").test(block);
    const beatRegion = videoPromptRegion(block);
    const raw: Interval[] = Array.from(beatRegion.matchAll(new RegExp(BEAT_LINE_SRC, "gim")), (match) => [
      parseInt(match[1], 10),
      parseInt(match[2], 10),
    ]);
    if (!raw.length) {
      if (videoPromptFound) {
        findings.push([lineOf(text, start), `segment ${segmentId}`, "recognized VIDEO PROMPT contains no beat timeline"]);
      }
      continue;
    }

    const problems = intervalProblems(raw, segmentLength, mode);
    if (problems.length) findings.push([lineOf(text, start), `segment ${segmentId}`, problems.join("; ")]);
  }
  return findings;
}

export function checkModelDuration(
  surface: Surface,
  model: Model,
  mode: Mode,
  segmentLength: number | null,
): Finding[] {
  if (!segmentLength || surface === "unspecified" || model === "unspecified" || model === "other") return [];

  let supported: number[] | undefined;
  if (mode !== "unspecified") {
    supported = MODE_DURATIONS[surface]?.[model]?.[mode];
  } else {
    const matrix = surface === "flow" ? FLOW_DURATIONS : API_DURATIONS;
    supported = matrix[model];
  }

  if (supported === undefined) return [];
  const profile = mode !== "unspecified" ? `${surface}/${model}/${mode}` : `${surface}/${model}`;
  if (!supported.length) {
    return [{ line: 1, snippet: profile, reason: "this generation mode is not supported by the selected profile" }];
  }
  if (supported.includes(segmentLength)) return [];
  const choices = [...supported].sort((a, b) => a - b).join(", ");
  return [
    {
      line: 1,
      snippet: `${profile}/${segmentLength}s`,
      reason: `unsupported duration for this profile; supported integer lengths: ${choices}`,
    },
  ];
}

// Python's \w is Unicode-aware, so letters such as Vietnamese diacritics count
// as word characters there. Match that here.
export function approximateTokens(text: string): number {
  return Array.from(text.matchAll(/[\p{L}\p{N}_]+|[^\p{L}\p{N}_\s]/gu)).length;
}

function checkVeoPromptLength(text: string, surface: Surface, model: Model): Issue[] {
  if (surface !== "gemini-api" || !model.startsWith("veo-3.1")) return [];
  const findings: Issue[] = [];
  for (const [start, block] of blocksBetween(text, VIDEO_PROMPT_MARKER())) {
    const estimate = approximateTokens(block);
    if (estimate > 1024) {
      findings.push([
        lineOf(text, start),
        `approximately ${estimate} tokens`,
        "Veo 3.1 publishes a 1,024-token text-input limit; local estimate may differ from the service tokenizer",
      ]);
    }
  }
  return findings;
}

function toFindings(issues: Issue[]): Finding[] {
  return issues.map(([line, snippet, reason]) => ({ line, snippet, reason }));
}

export function validateText(input: string, options: ValidateOptions = {}): ValidationResult {
  const segmentLength = options.segmentLength ?? null;
  const beatMode = options.beatMode ?? "exact";
  const surface = options.surface ?? "unspecified";
  const model = options.model ?? "unspecified";
  const mode = options.mode ?? "unspecified";
  const requireAudio = options.requireAudio ?? true;

  // Python reads files with universal newlines.
  const raw = input.replace(/\r\n?/g, "\n");
  if (IGNORE_FILE.test(raw)) {
    return { skipped: true, passed: true, disabled_checks: [], checks: {} };
  }

  const text = blankExampleFences(raw);
  const checks: Record<string, Finding[]> = {
    backward_references: toFindings(checkPatterns(text, BACKWARD_REFS)),
    text_bleed_tokens: toFindings(checkPatterns(text, TOKEN_LEAKS)),
    em_dashes: toFindings(checkEmDashes(text)),
    text_policy: toFindings(checkTextPolicy(text)),
    reference_handles: toFindings(checkReferenceHandles(text)),
    storyboard_contract: toFindings(checkStoryboardContract(text, segmentLength)),
    unsupported_specifications: toFindings(checkPatterns(text, SPEC_VIOLATIONS)),
    model_duration: checkModelDuration(surface, model, mode, segmentLength),
    veo_prompt_length: toFindings(checkVeoPromptLength(text, surface, model)),
  };
  const disabledChecks: string[] = [];

  if (segmentLength !== null && beatMode !== "off") {
    checks.beat_timeline = toFindings(checkBeats(text, segmentLength, beatMode));
  } else {
    disabledChecks.push("beat_timeline");
  }

  if (requireAudio) checks.audio_direction = toFindings(checkAudio(text));
  else disabledChecks.push("audio_direction");

  const passed = Object.values(checks).every((issues) => issues.length === 0);
  return { skipped: false, passed, disabled_checks: disabledChecks, checks };
}
