// Runs scripts/validate.py and the TypeScript port over the same documents and
// profiles, and fails on any difference in their findings.

import { execFileSync } from "node:child_process";
import { mkdtempSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { validateText, type ValidateOptions } from "../src/validator.ts";

const ROOT = resolve(fileURLToPath(import.meta.url), "../../..");
const PYTHON = process.env.PYTHON ?? "python3";

const EXTRA_DOCUMENTS: Record<string, string> = {
  "unicode_tokens.md": [
    "SEGMENT 1",
    "VIDEO PROMPT",
    "```text",
    "NO TEXT IN THE IMAGE: không có chữ.",
    `${"Người đàn ông bước đi chậm rãi trên phố cổ Hà Nội. ".repeat(120)}`,
    "AUDIO: Tiếng mưa nhẹ.",
    `0-1s: @Kwame bước xuống ${String.fromCharCode(0x2014)} rồi dừng lại.`,
    "```",
    "",
  ].join("\n"),
  "crlf_and_handles.md": [
    "SEGMENT 2.1",
    "VIDEO PROMPT",
    "INTENTIONAL TEXT IN THE IMAGE: the sign reads OPEN.",
    "CHARACTER REFERENCES: @Kwame, Cafe Ladies, @Sidewalk Cafe, [1] @Ama",
    "WHO IS IN THIS SHOT: @Kwame (walking, holding a cup), @Ama. No other named characters appear.",
    "LOCATION: Market street at noon (Old Market Street)",
    "Kwame waves at @Ama, as before, the same woman still holding #ff00aa 5600K.",
    "aspect ratio: 4:3",
    "0-2s: a",
    "2-1s: b",
    "",
  ].join("\r\n"),
};

const PROFILES: { name: string; options: ValidateOptions }[] = [
  { name: "default-8", options: { segmentLength: 8 } },
  { name: "no-length", options: {} },
  {
    name: "flow-omni-10-coverage",
    options: { segmentLength: 10, surface: "flow", model: "omni-flash", mode: "text-to-video", beatMode: "coverage" },
  },
  {
    name: "flow-omni-10-refs",
    options: { segmentLength: 10, surface: "flow", model: "omni-flash", mode: "references-to-video" },
  },
  { name: "beats-off-no-audio-10", options: { segmentLength: 10, beatMode: "off", requireAudio: false } },
  {
    name: "api-veo-4-loose",
    options: { segmentLength: 4, surface: "gemini-api", model: "veo-3.1", mode: "references-to-video", beatMode: "loose" },
  },
  { name: "api-omni-3", options: { segmentLength: 3, surface: "gemini-api", model: "omni-flash", mode: "text-to-video" } },
  { name: "flow-quality-unspecified-mode-6", options: { segmentLength: 6, surface: "flow", model: "veo-3.1-quality" } },
  { name: "api-veo-fast-8-exact", options: { segmentLength: 8, surface: "gemini-api", model: "veo-3.1-fast", mode: "extend" } },
];

function pythonArgs(options: ValidateOptions): string[] {
  const args: string[] = [];
  if (options.segmentLength != null) args.push("--segment-length", String(options.segmentLength));
  if (options.beatMode) args.push("--beat-mode", options.beatMode);
  if (options.surface) args.push("--surface", options.surface);
  if (options.model) args.push("--model", options.model);
  if (options.mode) args.push("--mode", options.mode);
  if (options.requireAudio === false) args.push("--no-require-audio");
  return args;
}

function collectDocuments(): string[] {
  const fixtures = join(ROOT, "tests", "fixtures");
  const documents = readdirSync(fixtures)
    .filter((name) => name.endsWith(".md"))
    .map((name) => join(fixtures, name));
  for (const folder of ["examples", "prompts", "core", "formats"]) {
    for (const name of readdirSync(join(ROOT, folder))) {
      if (name.endsWith(".md")) documents.push(join(ROOT, folder, name));
    }
  }
  documents.push(join(ROOT, "SKILL.md"), join(ROOT, "README.md"));

  const scratch = mkdtempSync(join(tmpdir(), "validator-parity-"));
  for (const [name, content] of Object.entries(EXTRA_DOCUMENTS)) {
    const path = join(scratch, name);
    writeFileSync(path, content, "utf-8");
    documents.push(path);
  }
  return documents;
}

function runPython(paths: string[], options: ValidateOptions): Map<string, unknown> {
  let output: string;
  try {
    output = execFileSync(PYTHON, [join(ROOT, "scripts", "validate.py"), ...paths, "--json", ...pythonArgs(options)], {
      encoding: "utf-8",
      maxBuffer: 64 * 1024 * 1024,
    });
  } catch (error) {
    const failed = error as { status?: number; stdout?: string };
    if (failed.status !== 1 || !failed.stdout) throw error;
    output = failed.stdout;
  }
  const payload = JSON.parse(output) as { files: ({ file: string } & Record<string, unknown>)[] };
  return new Map(payload.files.map(({ file, ...rest }) => [file, rest]));
}

function normalise(result: Record<string, unknown>): string {
  const { skipped, passed, disabled_checks: disabledChecks, checks } = result;
  return JSON.stringify({ skipped, passed: skipped ? true : passed, disabledChecks, checks });
}

const documents = collectDocuments();
let compared = 0;
const failures: string[] = [];

for (const profile of PROFILES) {
  const expected = runPython(documents, profile.options);
  for (const path of documents) {
    const pythonResult = expected.get(path) as Record<string, unknown> | undefined;
    if (!pythonResult) {
      failures.push(`${profile.name}: python produced no result for ${path}`);
      continue;
    }
    const tsResult = validateText(readFileSync(path, "utf-8"), profile.options) as unknown as Record<string, unknown>;
    compared += 1;
    const want = normalise(pythonResult);
    const got = normalise(tsResult);
    if (want !== got) {
      failures.push(`${profile.name}: ${relative(ROOT, path)}\n  python: ${want}\n  ts:     ${got}`);
    }
  }
}

if (failures.length) {
  console.error(`Validator parity FAILED (${failures.length} of ${compared}):\n`);
  console.error(failures.slice(0, 10).join("\n\n"));
  process.exit(1);
}
console.log(`Validator parity passed: ${compared} document/profile comparisons match scripts/validate.py.`);
