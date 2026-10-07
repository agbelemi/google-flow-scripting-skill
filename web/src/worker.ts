// Cloudflare Worker: serves the static UI from ./public and exposes a small
// JSON API. The Gemini API key comes from the browser on every request in the
// X-Gemini-Key header; the Worker never stores or logs it.

import { buildRevisionRequest, buildSystemInstruction, buildUserRequest, FORMATS, type Profile } from "./skill.ts";
import {
  BEAT_MODES,
  MODELS,
  MODES,
  SURFACES,
  validateText,
  type ValidateOptions,
} from "./validator.ts";

interface Env {
  ASSETS: { fetch(request: Request): Promise<Response> };
}

const GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta";
const MODEL_NAME = /^[a-z0-9][a-z0-9.\-]{0,80}$/;
const MAX_BRIEF = 20_000;
const MAX_PACKAGE = 400_000;

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

function fail(message: string, status = 400): Response {
  return json({ error: message }, status);
}

function apiKey(request: Request): string | null {
  const key = request.headers.get("x-gemini-key")?.trim();
  return key ? key : null;
}

function oneOf<T extends string>(value: unknown, allowed: readonly T[], fallback: T): T {
  return allowed.includes(value as T) ? (value as T) : fallback;
}

function text(value: unknown, limit: number): string {
  return typeof value === "string" ? value.slice(0, limit) : "";
}

function parseProfile(input: Record<string, unknown>): Profile | string {
  const brief = text(input.brief, MAX_BRIEF).trim();
  if (!brief) return "Hãy nhập ý tưởng (brief) cho video.";
  const segmentLength = Number(input.segmentLength);
  if (!Number.isInteger(segmentLength) || segmentLength < 3 || segmentLength > 10) {
    return "Độ dài mỗi đoạn phải là số nguyên từ 3 đến 10 giây.";
  }
  const runtime = Number(input.runtime);
  return {
    brief,
    surface: oneOf(input.surface, ["flow", "gemini-api"] as const, "flow"),
    model: oneOf(input.model, MODELS, "veo-3.1-fast"),
    mode: oneOf(input.mode, MODES, "text-to-video"),
    segmentLength,
    runtime: Number.isFinite(runtime) && runtime >= segmentLength ? Math.min(Math.round(runtime), 600) : segmentLength,
    aspectRatio: oneOf(input.aspectRatio, ["16:9", "9:16"] as const, "16:9"),
    format: Object.hasOwn(FORMATS, String(input.format)) ? String(input.format) : "live-action",
    beatMode: oneOf(input.beatMode, BEAT_MODES, "exact"),
    audioPolicy: oneOf(input.audioPolicy, ["generated", "silence", "post"] as const, "generated"),
    textPolicy: oneOf(input.textPolicy, ["none", "intentional"] as const, "none"),
    intentionalText: text(input.intentionalText, 500),
    notesLanguage: oneOf(input.notesLanguage, ["vi", "en"] as const, "vi"),
    extraNotes: text(input.extraNotes, MAX_BRIEF),
  };
}

async function upstreamError(response: Response): Promise<Response> {
  let message = `Gemini API trả về lỗi ${response.status}.`;
  try {
    const body = (await response.json()) as { error?: { message?: string } };
    if (body.error?.message) message = `Gemini API (${response.status}): ${body.error.message}`;
  } catch {
    // Keep the generic message.
  }
  return fail(message, response.status === 400 || response.status === 403 || response.status === 429 ? response.status : 502);
}

async function handleGenerate(request: Request): Promise<Response> {
  const key = apiKey(request);
  if (!key) return fail("Chưa có Gemini API key. Mở Cài đặt để nhập key.", 401);

  const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
  if (!body || typeof body.profile !== "object" || body.profile === null) return fail("Yêu cầu không hợp lệ.");
  const profile = parseProfile(body.profile as Record<string, unknown>);
  if (typeof profile === "string") return fail(profile);

  const model = text(body.model, 100) || "gemini-3-flash-preview";
  if (!MODEL_NAME.test(model)) return fail("Tên model không hợp lệ.");

  const contents: { role: "user" | "model"; parts: { text: string }[] }[] = [
    { role: "user", parts: [{ text: buildUserRequest(profile) }] },
  ];
  const previous = text(body.previous, MAX_PACKAGE);
  const findings = text(body.findings, MAX_BRIEF);
  if (previous && findings) {
    contents.push({ role: "model", parts: [{ text: previous }] });
    contents.push({ role: "user", parts: [{ text: buildRevisionRequest(findings) }] });
  }

  const upstream = await fetch(`${GEMINI_BASE}/models/${model}:streamGenerateContent?alt=sse`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-goog-api-key": key },
    body: JSON.stringify({
      systemInstruction: { parts: [{ text: buildSystemInstruction(profile) }] },
      contents,
      generationConfig: { temperature: 0.6 },
    }),
    signal: request.signal,
  });
  if (!upstream.ok || !upstream.body) return upstreamError(upstream);

  return new Response(upstream.body, {
    headers: { "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" },
  });
}

async function handleModels(request: Request): Promise<Response> {
  const key = apiKey(request);
  if (!key) return fail("Chưa có Gemini API key.", 401);
  const upstream = await fetch(`${GEMINI_BASE}/models?pageSize=200`, { headers: { "x-goog-api-key": key } });
  if (!upstream.ok) return upstreamError(upstream);
  const payload = (await upstream.json()) as {
    models?: { name: string; displayName?: string; supportedGenerationMethods?: string[] }[];
  };
  const models = (payload.models ?? [])
    .filter((model) => model.supportedGenerationMethods?.includes("generateContent"))
    .map((model) => ({ id: model.name.replace(/^models\//, ""), label: model.displayName ?? model.name }))
    .filter((model) => model.id.startsWith("gemini") && !/image|tts|audio|embedding|live/i.test(model.id));
  return json({ models });
}

async function handleValidate(request: Request): Promise<Response> {
  const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
  if (!body) return fail("Yêu cầu không hợp lệ.");
  const raw = (body.options ?? {}) as Record<string, unknown>;
  const segmentLength = Number(raw.segmentLength);
  const options: ValidateOptions = {
    segmentLength: Number.isInteger(segmentLength) && segmentLength >= 3 && segmentLength <= 10 ? segmentLength : null,
    beatMode: oneOf(raw.beatMode, BEAT_MODES, "exact"),
    surface: oneOf(raw.surface, SURFACES, "unspecified"),
    model: oneOf(raw.model, MODELS, "unspecified"),
    mode: oneOf(raw.mode, MODES, "unspecified"),
    requireAudio: raw.requireAudio !== false,
  };
  return json(validateText(text(body.text, MAX_PACKAGE), options));
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (!url.pathname.startsWith("/api/")) return env.ASSETS.fetch(request);
    if (request.method !== "POST") return fail("Method not allowed.", 405);

    try {
      switch (url.pathname) {
        case "/api/generate":
          return await handleGenerate(request);
        case "/api/models":
          return await handleModels(request);
        case "/api/validate":
          return await handleValidate(request);
        default:
          return fail("Not found.", 404);
      }
    } catch (error) {
      return fail(`Lỗi máy chủ: ${error instanceof Error ? error.message : String(error)}`, 500);
    }
  },
};
