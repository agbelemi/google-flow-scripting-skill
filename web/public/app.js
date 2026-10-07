// Flow Scripting Studio front end. Plain ES module, no build step.

const STORAGE = {
  key: "fss.geminiKey",
  model: "fss.textModel",
  form: "fss.form",
  output: "fss.output",
};
const DEFAULT_MODELS = [
  { id: "gemini-3-flash-preview", label: "Gemini 3 Flash (preview)" },
  { id: "gemini-3.1-pro-preview", label: "Gemini 3.1 Pro (preview)" },
  { id: "gemini-3.1-flash-lite", label: "Gemini 3.1 Flash-Lite" },
];
const CHECK_LABELS = {
  backward_references: "Tham chiếu ngược (as before, the same...)",
  text_bleed_tokens: "Ký hiệu dễ hiện thành chữ (5600K, #hex...)",
  em_dashes: "Dấu gạch dài (em dash)",
  text_policy: "Dòng chính sách chữ (NO TEXT...)",
  reference_handles: "Tên tham chiếu @PascalCase",
  storyboard_contract: "Quy tắc storyboard",
  beat_timeline: "Mốc thời gian từng đoạn",
  unsupported_specifications: "Thông số không hỗ trợ",
  model_duration: "Độ dài so với model/chế độ",
  veo_prompt_length: "Độ dài prompt Veo API",
  audio_direction: "Khối AUDIO",
};
const MARKER = /^[ \t]*(?:[#>*_\-]+[ \t]*)*(VIDEO PROMPT|STORYBOARD IMAGE PROMPT|STORYBOARD CONTACT SHEET PROMPT|IMAGE PROMPT|REFERENCE SHEET)\b.*$/i;

const $ = (selector) => document.querySelector(selector);
const form = $("#profile-form");
const editor = $("#editor");
const rendered = $("#rendered");
const statusLine = $("#status");
const settings = $("#settings");

let controller = null;
let lastResult = null;

// ---------- storage ----------

function load(name, fallback = null) {
  try {
    const value = localStorage.getItem(name);
    return value === null ? fallback : value;
  } catch {
    return fallback;
  }
}

function save(name, value) {
  try {
    if (value === null || value === undefined) localStorage.removeItem(name);
    else localStorage.setItem(name, value);
  } catch {
    // Storage can be unavailable (private mode); the app still works.
  }
}

const getKey = () => load(STORAGE.key, "");
const getTextModel = () => load(STORAGE.model, DEFAULT_MODELS[0].id);

// ---------- helpers ----------

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
}

function setStatus(message, isError = false) {
  statusLine.textContent = message;
  statusLine.classList.toggle("error", isError);
}

function profileFromForm() {
  const data = Object.fromEntries(new FormData(form).entries());
  data.segmentLength = Number(data.segmentLength);
  data.runtime = Number(data.runtime);
  return data;
}

function validatorOptions(profile) {
  return {
    segmentLength: profile.segmentLength,
    beatMode: profile.beatMode,
    surface: profile.surface,
    model: profile.model,
    mode: profile.mode,
    requireAudio: profile.audioPolicy !== "post",
  };
}

async function api(path, body, { key = getKey(), signal } = {}) {
  const headers = { "content-type": "application/json" };
  if (key) headers["x-gemini-key"] = key;
  const response = await fetch(path, { method: "POST", headers, body: JSON.stringify(body), signal });
  if (!response.ok) {
    let message = `Lỗi ${response.status}`;
    try {
      const payload = await response.json();
      if (payload.error) message = payload.error;
    } catch {
      // Keep the generic message.
    }
    throw new Error(message);
  }
  return response;
}

async function copy(text, button) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const area = document.createElement("textarea");
    area.value = text;
    document.body.append(area);
    area.select();
    document.execCommand("copy");
    area.remove();
  }
  if (button) {
    const original = button.textContent;
    button.textContent = "Đã chép";
    setTimeout(() => (button.textContent = original), 1200);
  }
}

// ---------- markdown rendering ----------

function inline(text) {
  return escapeHtml(text)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
}

function renderTable(rows) {
  const cells = (row) => row.trim().replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim());
  const isRule = (row) => /^\s*\|?\s*:?-{2,}/.test(row);
  const body = rows.filter((row) => !isRule(row));
  if (!body.length) return "";
  const [first, ...rest] = body;
  const hasHeader = rows.length > 1 && isRule(rows[1]);
  const headHtml = hasHeader ? `<thead><tr>${cells(first).map((c) => `<th>${inline(c)}</th>`).join("")}</tr></thead>` : "";
  const bodyRows = hasHeader ? rest : body;
  return `<table>${headHtml}<tbody>${bodyRows
    .map((row) => `<tr>${cells(row).map((c) => `<td>${inline(c)}</td>`).join("")}</tr>`)
    .join("")}</tbody></table>`;
}

function renderMarkdown(source) {
  const lines = source.replace(/\r\n?/g, "\n").split("\n");
  const html = [];
  const blocks = [];
  let paragraph = [];
  let list = null;
  let table = [];
  let lastMarker = "";

  const flushParagraph = () => {
    if (paragraph.length) html.push(`<p>${paragraph.map(inline).join("<br>")}</p>`);
    paragraph = [];
  };
  const flushList = () => {
    if (list) html.push(`<${list.tag}>${list.items.map((item) => `<li>${inline(item)}</li>`).join("")}</${list.tag}>`);
    list = null;
  };
  const flushTable = () => {
    if (table.length) html.push(renderTable(table));
    table = [];
  };
  const flushAll = () => {
    flushParagraph();
    flushList();
    flushTable();
  };

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const fence = line.match(/^\s*(```|~~~)/);
    if (fence) {
      flushAll();
      const body = [];
      index += 1;
      while (index < lines.length && !lines[index].trim().startsWith(fence[1])) {
        body.push(lines[index]);
        index += 1;
      }
      const text = body.join("\n");
      const id = blocks.push(text) - 1;
      const title = lastMarker || "Prompt";
      html.push(
        `<section class="prompt-card"><header><span>${escapeHtml(title)}</span>` +
          `<button type="button" class="btn small" data-copy="${id}">Sao chép</button></header>` +
          `<pre>${escapeHtml(text)}</pre></section>`,
      );
      lastMarker = "";
      continue;
    }

    const marker = line.match(MARKER);
    if (marker) {
      flushAll();
      lastMarker = line.replace(/^[\s#>*_\-]+/, "").replace(/\*+$/, "").trim();
      continue;
    }

    const heading = line.match(/^(#{1,4})\s+(.*)$/);
    if (heading) {
      flushAll();
      const level = heading[1].length;
      html.push(`<h${level}>${inline(heading[2])}</h${level}>`);
      continue;
    }

    if (/^\s*\|/.test(line)) {
      flushParagraph();
      flushList();
      table.push(line);
      continue;
    }
    flushTable();

    const item = line.match(/^\s*(?:([-*])|(\d+)[.)])\s+(.*)$/);
    if (item) {
      flushParagraph();
      const tag = item[1] ? "ul" : "ol";
      if (!list || list.tag !== tag) {
        flushList();
        list = { tag, items: [] };
      }
      list.items.push(item[3]);
      continue;
    }

    if (!line.trim()) {
      flushParagraph();
      flushList();
      continue;
    }

    flushList();
    paragraph.push(line);
  }
  flushAll();
  return { html: html.join("\n"), blocks };
}

let renderedBlocks = [];
let renderScheduled = false;

function renderOutput() {
  const text = editor.value;
  $("#empty").hidden = Boolean(text.trim());
  const { html, blocks } = renderMarkdown(text);
  rendered.innerHTML = html;
  renderedBlocks = blocks;
  const hasText = Boolean(text.trim());
  for (const id of ["#validate", "#copy-all", "#download"]) $(id).disabled = !hasText || Boolean(controller);
}

function scheduleRender() {
  if (renderScheduled) return;
  renderScheduled = true;
  requestAnimationFrame(() => {
    renderScheduled = false;
    renderOutput();
  });
}

rendered.addEventListener("click", (event) => {
  const button = event.target.closest("[data-copy]");
  if (button) copy(renderedBlocks[Number(button.dataset.copy)] ?? "", button);
});

// ---------- validation ----------

function formatFindings(result) {
  const lines = [];
  for (const [check, findings] of Object.entries(result.checks)) {
    for (const finding of findings) {
      lines.push(`- [${check}] line ${finding.line}: ${finding.snippet} - ${finding.reason}`);
    }
  }
  return lines.join("\n");
}

function showValidation(result) {
  lastResult = result;
  const badge = $("#check-badge");
  const total = Object.values(result.checks).reduce((sum, findings) => sum + findings.length, 0);
  badge.hidden = false;
  badge.className = `badge ${result.passed ? "ok" : "bad"}`;
  badge.textContent = result.passed ? "OK" : String(total);
  $("#revise").disabled = result.passed || Boolean(controller);

  const items = Object.entries(result.checks)
    .map(([check, findings]) => {
      const ok = findings.length === 0;
      const details = findings
        .slice(0, 25)
        .map((f) => `<li>Dòng ${f.line}: <code>${escapeHtml(f.snippet)}</code> - ${escapeHtml(f.reason)}</li>`)
        .join("");
      const more = findings.length > 25 ? `<li>... và ${findings.length - 25} lỗi khác</li>` : "";
      return `<li><div class="name"><span>${escapeHtml(CHECK_LABELS[check] ?? check)}</span>` +
        `<span class="${ok ? "pass" : "fail"}">${ok ? "Đạt" : `${findings.length} lỗi`}</span></div>` +
        (ok ? "" : `<ul>${details}${more}</ul>`) + "</li>";
    })
    .join("");
  const disabled = result.disabled_checks.length
    ? `<p class="hint">Đã tắt: ${result.disabled_checks.map((c) => escapeHtml(CHECK_LABELS[c] ?? c)).join(", ")}.</p>`
    : "";
  $("#check-results").innerHTML =
    `<div class="verdict ${result.passed ? "ok" : "bad"}">${
      result.passed
        ? "Đạt toàn bộ kiểm tra tự động. Hãy xem lại tính liên tục bằng mắt trước khi tạo video."
        : `Có ${total} lỗi. Chưa nên tạo video: bấm "AI sửa lỗi" hoặc sửa tay rồi kiểm tra lại.`
    }</div>` +
    `<ul class="check-list">${items}</ul>${disabled}` +
    `<p class="hint">Đây là bản chuyển sang TypeScript của scripts/validate.py, cho kết quả giống hệt bản gốc.</p>`;
}

async function runValidation() {
  if (!editor.value.trim()) return null;
  const response = await api("/api/validate", { text: editor.value, options: validatorOptions(profileFromForm()) }, { key: "" });
  const result = await response.json();
  showValidation(result);
  return result;
}

let warningTimer = null;
function checkProfile() {
  clearTimeout(warningTimer);
  warningTimer = setTimeout(async () => {
    const warning = $("#profile-warning");
    try {
      const response = await api("/api/validate", { text: "", options: validatorOptions(profileFromForm()) }, { key: "" });
      const result = await response.json();
      const issue = result.checks.model_duration?.[0];
      warning.hidden = !issue;
      if (issue) {
        warning.textContent = issue.reason.includes("not supported")
          ? "Model này không hỗ trợ chế độ tạo đã chọn trên nền tảng này (theo reference/FLOW-FEATURES.md)."
          : `Độ dài đoạn không hợp với model/chế độ này. Độ dài hỗ trợ: ${issue.reason.split(": ").pop()} giây.`;
      }
    } catch {
      warning.hidden = true;
    }
  }, 250);
}

// ---------- generation ----------

function setBusy(busy) {
  $("#generate").disabled = busy;
  $("#stop").hidden = !busy;
  editor.readOnly = busy;
  for (const id of ["#validate", "#revise", "#copy-all", "#download"]) $(id).disabled = busy || !editor.value.trim();
  if (!busy && lastResult) $("#revise").disabled = lastResult.passed;
}

async function generate({ revise = false } = {}) {
  const key = getKey();
  if (!key) {
    openSettings("Hãy nhập Gemini API key trước.");
    return;
  }
  const profile = profileFromForm();
  if (!profile.brief.trim()) {
    setStatus("Hãy nhập ý tưởng video.", true);
    form.brief.focus();
    return;
  }

  const body = { profile, model: getTextModel() };
  if (revise) {
    if (!lastResult || lastResult.passed) return;
    body.previous = editor.value;
    body.findings = formatFindings(lastResult);
  }

  controller = new AbortController();
  setBusy(true);
  switchTab("view");
  setStatus(revise ? "Đang nhờ AI sửa lỗi..." : `Đang tạo bằng ${body.model}... (có thể mất 1-3 phút)`);
  const previous = editor.value;
  editor.value = "";
  renderOutput();

  let text = "";
  let finishReason = "";
  try {
    const response = await api("/api/generate", body, { key, signal: controller.signal });
    const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
    let buffer = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += value;
      const events = buffer.split(/\r?\n\r?\n/);
      buffer = events.pop() ?? "";
      for (const event of events) {
        const data = event
          .split(/\r?\n/)
          .filter((line) => line.startsWith("data:"))
          .map((line) => line.slice(5).trim())
          .join("");
        if (!data) continue;
        const payload = JSON.parse(data);
        if (payload.error) throw new Error(payload.error.message ?? "Gemini API báo lỗi.");
        if (payload.promptFeedback?.blockReason) throw new Error(`Gemini từ chối yêu cầu: ${payload.promptFeedback.blockReason}`);
        const candidate = payload.candidates?.[0];
        for (const part of candidate?.content?.parts ?? []) {
          if (part.text && !part.thought) text += part.text;
        }
        if (candidate?.finishReason) finishReason = candidate.finishReason;
      }
      editor.value = text;
      scheduleRender();
      setStatus(`Đang nhận kết quả... ${text.length.toLocaleString("vi-VN")} ký tự`);
    }

    if (!text.trim()) throw new Error("Gemini không trả về nội dung. Thử lại hoặc đổi model trong Cài đặt.");
    editor.value = text;
    renderOutput();
    save(STORAGE.output, text);
    const result = await runValidation();
    const truncated = finishReason === "MAX_TOKENS" ? " Kết quả bị cắt vì quá dài: hãy giảm tổng thời lượng." : "";
    setStatus(
      (result?.passed ? "Xong. Đạt toàn bộ kiểm tra tự động." : "Xong. Còn lỗi kiểm tra: xem tab Kiểm tra hoặc bấm AI sửa lỗi.") + truncated,
      Boolean(truncated),
    );
  } catch (error) {
    if (error.name === "AbortError") {
      setStatus("Đã dừng.");
      if (!text.trim()) editor.value = previous;
    } else {
      setStatus(error.message, true);
      if (!text.trim()) editor.value = previous;
    }
    renderOutput();
  } finally {
    controller = null;
    setBusy(false);
    renderOutput();
  }
}

// ---------- tabs ----------

function switchTab(name) {
  for (const tab of document.querySelectorAll(".tab")) {
    const active = tab.dataset.tab === name;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", String(active));
  }
  $("#tab-view").hidden = name !== "view";
  $("#tab-edit").hidden = name !== "edit";
  $("#tab-check").hidden = name !== "check";
  if (name === "view") renderOutput();
}

for (const tab of document.querySelectorAll(".tab")) {
  tab.addEventListener("click", () => switchTab(tab.dataset.tab));
}

// ---------- settings ----------

function fillModels(models, selected) {
  const select = $("#text-model");
  const list = [...models];
  if (selected && !list.some((model) => model.id === selected)) list.unshift({ id: selected, label: selected });
  select.innerHTML = list
    .map((model) => `<option value="${escapeHtml(model.id)}">${escapeHtml(model.label)} (${escapeHtml(model.id)})</option>`)
    .join("");
  select.value = selected || list[0]?.id || "";
}

function updateKeyDot() {
  $("#key-dot").classList.toggle("ok", Boolean(getKey()));
}

function openSettings(message = "") {
  $("#api-key").value = getKey();
  fillModels(DEFAULT_MODELS, getTextModel());
  $("#settings-status").textContent = message;
  $("#settings-status").classList.remove("error");
  settings.showModal();
}

async function fetchModels() {
  const key = $("#api-key").value.trim();
  const statusEl = $("#settings-status");
  if (!key) {
    statusEl.textContent = "Nhập key trước.";
    statusEl.classList.add("error");
    return false;
  }
  statusEl.classList.remove("error");
  statusEl.textContent = "Đang kết nối Gemini...";
  try {
    const response = await api("/api/models", {}, { key });
    const { models } = await response.json();
    const current = $("#text-model").value;
    fillModels(models.length ? models : DEFAULT_MODELS, current);
    statusEl.textContent = `Key hợp lệ. Tìm thấy ${models.length} model Gemini.`;
    return true;
  } catch (error) {
    statusEl.textContent = error.message;
    statusEl.classList.add("error");
    return false;
  }
}

$("#open-settings").addEventListener("click", () => openSettings());
$("#toggle-key").addEventListener("click", (event) => {
  const input = $("#api-key");
  input.type = input.type === "password" ? "text" : "password";
  event.target.textContent = input.type === "password" ? "Hiện" : "Ẩn";
});
$("#load-models").addEventListener("click", fetchModels);
$("#test-key").addEventListener("click", fetchModels);
$("#clear-key").addEventListener("click", () => {
  save(STORAGE.key, null);
  $("#api-key").value = "";
  updateKeyDot();
  $("#settings-status").textContent = "Đã xóa key khỏi trình duyệt.";
});
$("#save-settings").addEventListener("click", () => {
  save(STORAGE.key, $("#api-key").value.trim() || null);
  save(STORAGE.model, $("#text-model").value || null);
  updateKeyDot();
});

// ---------- form persistence ----------

function restoreForm() {
  try {
    const saved = JSON.parse(load(STORAGE.form, "{}"));
    for (const [name, value] of Object.entries(saved)) {
      if (form.elements[name]) form.elements[name].value = value;
    }
  } catch {
    // Ignore corrupted saved state.
  }
}

function persistForm() {
  save(STORAGE.form, JSON.stringify(Object.fromEntries(new FormData(form).entries())));
  $("#intentional-text-field").hidden = form.textPolicy.value !== "intentional";
}

form.addEventListener("input", () => {
  persistForm();
  checkProfile();
});
form.addEventListener("change", () => {
  persistForm();
  checkProfile();
});
form.addEventListener("submit", (event) => {
  event.preventDefault();
  generate();
});

$("#stop").addEventListener("click", () => controller?.abort());
$("#revise").addEventListener("click", () => generate({ revise: true }));
$("#validate").addEventListener("click", async () => {
  try {
    const result = await runValidation();
    if (result) {
      switchTab("check");
      setStatus(result.passed ? "Đạt toàn bộ kiểm tra tự động." : "Còn lỗi kiểm tra.");
    }
  } catch (error) {
    setStatus(error.message, true);
  }
});
$("#copy-all").addEventListener("click", (event) => copy(editor.value, event.target));
$("#download").addEventListener("click", () => {
  const blob = new Blob([editor.value], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = Object.assign(document.createElement("a"), { href: url, download: "flow-production-package.md" });
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
editor.addEventListener("input", () => {
  save(STORAGE.output, editor.value);
  lastResult = null;
  $("#check-badge").hidden = true;
  $("#revise").disabled = true;
  renderOutput();
});

// ---------- start ----------

restoreForm();
persistForm();
editor.value = load(STORAGE.output, "");
renderOutput();
updateKeyDot();
checkProfile();
if (editor.value.trim()) runValidation().catch(() => {});
if (!getKey()) openSettings("Chào bạn! Dán Gemini API key để bắt đầu.");
