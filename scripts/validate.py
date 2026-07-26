#!/usr/bin/env python3
"""Mechanical checks for Google Flow, Veo and Gemini Omni scripts.

Checks include backward references, text-bleed tokens, em dashes, prompt text
policy, canonical @ReferenceHandles, storyboard contact-sheet contracts, timing,
model-duration compatibility, unsupported specifications, optional audio, and
an advisory Veo API prompt-length estimate.

Ordinary fenced blocks are validated. Deliberate examples can be excluded with
```example, ```counterexample, ```bad, ```dont, or ```avoid. An entire file can
opt out with <!-- validate:ignore-file -->.

Exit codes: 0 = all enabled checks passed; 1 = findings; 2 = bad input.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import sys
from pathlib import Path
from typing import Iterable

VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"
VERSION = VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.is_file() else "0.0.0"

BACKWARD_REFS = [
    (r"\bfrom (?:segment|seg|shot)\s+\d+", "refers back to another segment"),
    (r"\b(?:as|like) in (?:scene|segment|seg|shot)\s+\d+", "refers back to another shot"),
    (r"\bidentical to (?:scene|segment|seg|shot)\s+\d+", "refers back to another shot"),
    (r"\breturns? to (?:scene|segment|seg|shot)\s+\d+", "refers back to another shot"),
    (
        r"\bthe same (?:trader|vendor|man|woman|person|character|customer|dog|cat|child|guy|lady|prop|costume|vehicle|room|location)\b",
        '"the same X" assumes implicit memory',
    ),
    (r"\bas (?:before|established|previously|earlier)\b", "refers to earlier context"),
    (
        r"\bcontinuing from (?:before|the previous|earlier)\b",
        "vague continuation; describe the incoming frame in full",
    ),
    (
        r"\bstill (?:wet|dirty|torn|bleeding|holding|wearing|soaked|muddy)\b",
        '"still X" assumes memory; state the condition outright',
    ),
    (r"\bsame as (?:above|before|previous)\b", "refers to earlier content"),
    (r"\bpreviously (?:seen|shown|established)\b", "refers to earlier content"),
]

TOKEN_LEAKS = [
    (r"\b\d{3,5}\s?K\b", "colour-temperature value; use plain words"),
    (r"#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})\b", "hex colour code; use a colour name"),
    (
        r"#(?=[0-9A-Fa-f]{3,4}\b)(?=[0-9A-Fa-f]*[A-Fa-f])[0-9A-Fa-f]{3,4}\b",
        "short hex colour code; use a colour name",
    ),
    (
        r"\((?:[A-Z][A-Za-z']*\s+){1,4}(?:Lane|Market|Street|Room|Interior|Exterior|House|Shop|Studio|Stall|Path|Clearing)\)",
        "set name in brackets; it may be rendered as a caption",
    ),
]

SPEC_VIOLATIONS = [
    (
        r"\b(?:aspect ratio|ratio)\s*[:\-]?\s*(?:1:1|4:3|2\.39:1|21:9)\b",
        "this workflow targets native 16:9 or 9:16 output; crop other shapes in post",
    ),
    (
        r"\b(?:square 1:1|classic 4:3|cinemascope 2\.39:1)\b",
        "this workflow targets native 16:9 or 9:16 output; crop other shapes in post",
    ),
]

IGNORE_FILE = re.compile(r"<!--\s*validate:ignore-file\s*-->", re.I)
EXAMPLE_FENCE = re.compile(
    r"^```(?:example|counterexample|bad|dont|avoid)\b.*?^```", re.S | re.M | re.I
)

TEXT_POLICY_MARKER = re.compile(
    r"^(?:NO TEXT IN THE IMAGE\b|INTENTIONAL TEXT(?: IN THE IMAGE)?\s*:)", re.I
)
PROMPT_MARKER = re.compile(
    r"^[ \t]*(?:[#>*_\-]+[ \t]*)*(?:VIDEO PROMPT|STORYBOARD IMAGE PROMPT|STORYBOARD CONTACT SHEET PROMPT|IMAGE PROMPT|REFERENCE SHEET)",
    re.I | re.M,
)
VIDEO_PROMPT_MARKER = re.compile(r"^[ \t]*(?:[#>*_\-]+[ \t]*)*VIDEO PROMPT", re.I | re.M)
STORYBOARD_PROMPT_MARKER = re.compile(
    r"^[ \t]*(?:[#>*_\-]+[ \t]*)*(?:STORYBOARD IMAGE PROMPT|STORYBOARD CONTACT SHEET PROMPT)",
    re.I | re.M,
)
SEGMENT_MARKER = re.compile(r"^[ \t]*(?:[#>*_\-]+[ \t]*)*(?:SEGMENT|SEG)\s+([\d.]+)", re.I | re.M)
BEAT_LINE = re.compile(r"^[ \t]*\[?(\d+)\s*-\s*(\d+)\s*s\]?\s*:", re.I | re.M)
AUDIO_MARKER = re.compile(r"^[ \t]*AUDIO\s*:", re.I | re.M)
FENCE_LINE = re.compile(r"^(?:```|~~~)")
CANONICAL_HANDLE = re.compile(r"^@[A-Za-z][A-Za-z0-9]*$")
ANY_AT_TOKEN = re.compile(r"@[A-Za-z0-9_-]+")

REFERENCE_FIELD = re.compile(
    r"^[ \t]*(?:CHARACTER REFERENCES?|LOCATION REFERENCES?|LOCATION REFERENCE|REFERENCE HANDLE|REFERENCES TO ATTACH|SOURCE REFERENCES|OTHER ATTACHED REFERENCES|ATTACH|CAST|WHO IS IN THIS SHOT|WHO IS IN THIS FRAME|REFERENCED SUBJECTS)\s*:\s*(.+)$",
    re.I | re.M,
)
LOCATION_FIELD = re.compile(r"^[ \t]*LOCATION\s*:\s*(.+)$", re.I | re.M)
ALSO_ENTRY = re.compile(r"^[ \t]+([^\s].*?)\s+-\s+", re.M)

RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BOLD = "\033[1m"

Issue = tuple[int, str, str]

FLOW_DURATIONS = {
    "veo-3.1": {4, 6, 8},
    "veo-3.1-lite": {4, 6, 8},
    "veo-3.1-fast": {4, 6, 8},
    "veo-3.1-quality": {8},
    "omni-flash": {4, 6, 8, 10},
}
API_DURATIONS = {
    "veo-3.1": {4, 6, 8},
    "veo-3.1-lite": {4, 6, 8},
    "veo-3.1-fast": {4, 6, 8},
    "veo-3.1-quality": {4, 6, 8},
    "omni-flash": set(range(3, 11)),
}

# Duration sets are based on the documented surface, model, and mode profiles
# reviewed in reference/FLOW-FEATURES.md. An empty set means unsupported.
MODE_DURATIONS = {
    "flow": {
        "veo-3.1": {
            "text-to-video": {4, 6, 8},
            "first-frame": {4, 6, 8},
            "first-last-frame": {4, 6, 8},
            "references-to-video": {8},
            "video-edit": set(),
            "extend": set(),
        },
        "veo-3.1-lite": {
            "text-to-video": {4, 6, 8},
            "first-frame": {4, 6, 8},
            "first-last-frame": {4, 6, 8},
            "references-to-video": {8},
            "video-edit": set(),
            "extend": {8},
        },
        "veo-3.1-fast": {
            "text-to-video": {4, 6, 8},
            "first-frame": {4, 6, 8},
            "first-last-frame": {4, 6, 8},
            "references-to-video": {8},
            "video-edit": set(),
            "extend": set(),
        },
        "veo-3.1-quality": {
            "text-to-video": {8},
            "first-frame": {8},
            "first-last-frame": {8},
            "references-to-video": set(),
            "video-edit": set(),
            "extend": set(),
        },
        "omni-flash": {
            "text-to-video": {4, 6, 8, 10},
            "first-frame": {4, 6, 8, 10},
            "first-last-frame": set(),
            "references-to-video": {4, 6, 8, 10},
            "video-edit": {4, 6, 8, 10},
            "extend": set(),
        },
    },
    "gemini-api": {
        "veo-3.1": {
            "text-to-video": {4, 6, 8},
            "first-frame": {4, 6, 8},
            "first-last-frame": {8},
            "references-to-video": {8},
            "video-edit": set(),
            "extend": {8},
        },
        "veo-3.1-lite": {
            "text-to-video": {4, 6, 8},
            "first-frame": {4, 6, 8},
            "first-last-frame": {8},
            "references-to-video": {8},
            "video-edit": set(),
            "extend": {8},
        },
        "veo-3.1-fast": {
            "text-to-video": {4, 6, 8},
            "first-frame": {4, 6, 8},
            "first-last-frame": {8},
            "references-to-video": {8},
            "video-edit": set(),
            "extend": {8},
        },
        "veo-3.1-quality": {
            "text-to-video": {4, 6, 8},
            "first-frame": {4, 6, 8},
            "first-last-frame": {8},
            "references-to-video": {8},
            "video-edit": set(),
            "extend": {8},
        },
        "omni-flash": {
            "text-to-video": set(range(3, 11)),
            "first-frame": set(range(3, 11)),
            "first-last-frame": set(),
            "references-to-video": set(range(3, 11)),
            "video-edit": set(range(3, 11)),
            "extend": set(),
        },
    },
}


def colour(text: str, code: str, use_colour: bool) -> str:
    return f"{code}{text}{RESET}" if use_colour else text


def line_of(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def blank_example_fences(text: str) -> str:
    return EXAMPLE_FENCE.sub(lambda match: "\n" * match.group(0).count("\n"), text)


def blocks_between(text: str, marker: re.Pattern[str]) -> Iterable[tuple[int, str]]:
    starts = [match.start() for match in marker.finditer(text)]
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(text)
        yield start, text[start:end]


def first_semantic_line(block: str) -> tuple[int, str] | None:
    lines = block.splitlines(keepends=True)
    offset = len(lines[0]) if lines else 0
    for line in lines[1:]:
        stripped = line.strip()
        if stripped and not FENCE_LINE.match(stripped) and not stripped.startswith("<!--"):
            return offset, stripped
        offset += len(line)
    return None


def semantic_lines(block: str) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    lines = block.splitlines(keepends=True)
    offset = len(lines[0]) if lines else 0
    for line in lines[1:]:
        stripped = line.strip()
        if stripped and not FENCE_LINE.match(stripped) and not stripped.startswith("<!--"):
            result.append((offset, stripped))
        offset += len(line)
    return result


def check_patterns(text: str, patterns: list[tuple[str, str]]) -> list[Issue]:
    findings: list[Issue] = []
    for pattern, reason in patterns:
        for match in re.finditer(pattern, text, re.I):
            findings.append((line_of(text, match.start()), match.group(0).strip(), reason))
    return sorted(findings)


def check_em_dashes(text: str) -> list[Issue]:
    return [
        (line_of(text, match.start()), "em dash", "em dashes are prohibited; use other punctuation")
        for match in re.finditer(chr(0x2014), text)
    ]


def check_text_policy(text: str) -> list[Issue]:
    findings: list[Issue] = []
    for start, block in blocks_between(text, PROMPT_MARKER):
        header = block.strip().split("\n")[0].strip() or "(prompt)"
        is_storyboard = STORYBOARD_PROMPT_MARKER.match(header) is not None
        lines = semantic_lines(block)
        if not lines:
            findings.append((line_of(text, start), header[:60], "prompt has no content"))
            continue

        if is_storyboard:
            if lines[0][1] != "GENERATE THE STORYBOARD IMAGE NOW.":
                findings.append(
                    (
                        line_of(text, start + lines[0][0]),
                        lines[0][1][:60],
                        "storyboard prompt must begin exactly with GENERATE THE STORYBOARD IMAGE NOW.",
                    )
                )
            early = lines[:25]
            if not any(TEXT_POLICY_MARKER.match(value) for _, value in early):
                findings.append(
                    (
                        line_of(text, start),
                        header[:60],
                        "storyboard prompt must place an explicit text policy near the top",
                    )
                )
        else:
            if not TEXT_POLICY_MARKER.match(lines[0][1]):
                findings.append(
                    (
                        line_of(text, start + lines[0][0]),
                        lines[0][1][:60],
                        "the first semantic prompt line must declare NO TEXT or INTENTIONAL TEXT",
                    )
                )
    return findings


def check_storyboard_contract(text: str, segment_length: int | None) -> list[Issue]:
    findings: list[Issue] = []
    expected_by_length = {4: (2, "2x1"), 6: (3, "3x1"), 8: (3, "3x1"), 10: (4, "2x2")}

    for start, block in blocks_between(text, STORYBOARD_PROMPT_MARKER):
        header = block.strip().split("\n")[0].strip() or "(storyboard prompt)"
        lower = block.lower()
        required = [
            ("do not write a storyboard", "must prohibit a written storyboard response"),
            ("storyboard contact sheet", "must request one finished storyboard contact sheet"),
            ("do not invent additional actions", "must prohibit invented actions"),
            ("return only the completed", "must require only the completed image output"),
            ("do not ask for permission", "must prohibit permission questions"),
        ]
        for phrase, reason in required:
            if phrase not in lower:
                findings.append((line_of(text, start), header[:60], reason))

        count_match = re.search(r"exactly\s+(\d+)\s+(?:cinematic\s+still-image\s+)?panels?", block, re.I)
        layout_match = re.search(r"\b(2x1|3x1|2x2|3x3)\b", block, re.I)
        if not count_match:
            findings.append((line_of(text, start), header[:60], "must declare the exact numeric panel count"))
        if not layout_match:
            findings.append((line_of(text, start), header[:60], "must declare a supported grid layout"))

        panel_labels = re.findall(r"^[ \t]*PANEL\s+([A-I])(?:\s|:|-)", block, re.I | re.M)
        normalised_labels = [label.upper() for label in panel_labels]
        duplicate_labels = sorted(label for label, count in Counter(normalised_labels).items() if count > 1)
        if duplicate_labels:
            findings.append((line_of(text, start), ", ".join(duplicate_labels), "duplicate storyboard panel labels"))
        if count_match:
            declared_count = int(count_match.group(1))
            expected_labels = [chr(ord("A") + index) for index in range(declared_count)]
            if normalised_labels != expected_labels:
                findings.append(
                    (
                        line_of(text, start),
                        ", ".join(normalised_labels) or "no panel labels",
                        "panel sections must appear once each in declared order: " + ", ".join(expected_labels),
                    )
                )

        if segment_length in expected_by_length and count_match and layout_match:
            expected_count, expected_layout = expected_by_length[segment_length]
            actual_count = int(count_match.group(1))
            actual_layout = layout_match.group(1).lower()
            is_explicit_nine = actual_count == 9 and actual_layout == "3x3" and "nine distinct" in lower
            if not is_explicit_nine and (actual_count, actual_layout) != (expected_count, expected_layout):
                findings.append(
                    (
                        line_of(text, start),
                        f"{actual_count} panels in {actual_layout}",
                        f"{segment_length}s defaults to {expected_count} panels in {expected_layout}",
                    )
                )
    return findings


def split_top_level_commas(value: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    depth = 0
    for char in value:
        if char in "([{" :
            depth += 1
        elif char in ")]}" and depth:
            depth -= 1
        if char == "," and depth == 0:
            items.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        items.append("".join(current).strip())
    return items


def check_reference_handles(text: str) -> list[Issue]:
    findings: list[Issue] = []

    for match in ANY_AT_TOKEN.finditer(text):
        token = match.group(0)
        if not CANONICAL_HANDLE.match(token):
            findings.append(
                (
                    line_of(text, match.start()),
                    token[:60],
                    "reference handles must be @PascalCase with letters and numbers only",
                )
            )

    for match in REFERENCE_FIELD.finditer(text):
        field_value = match.group(1).strip()
        field_name = match.group(0).split(":", 1)[0].strip()
        value = re.split(r"\bNo other named characters\b", field_value, flags=re.I)[0].strip()
        if value.upper() in {"NONE", "N/A"}:
            continue
        items = split_top_level_commas(value)
        for item in items:
            stripped = re.sub(r"^\[\d+\]\s*", "", item).strip()
            if not stripped or stripped.upper() in {"NONE", "N/A"}:
                continue
            if not stripped.startswith("@"):
                findings.append(
                    (
                        line_of(text, match.start()),
                        stripped[:60],
                        f"{field_name} contains a reference without a leading @",
                    )
                )
            elif re.match(r"^@[A-Za-z][A-Za-z0-9]*\s+[A-Z][A-Za-z0-9]*", stripped):
                findings.append(
                    (
                        line_of(text, match.start()),
                        stripped[:60],
                        "reference handles cannot contain spaces; convert the name to PascalCase",
                    )
                )

    for match in LOCATION_FIELD.finditer(text):
        value = match.group(1).strip()
        if value and not value.startswith("@"):
            findings.append(
                (
                    line_of(text, match.start()),
                    value[:60],
                    "LOCATION must begin with a canonical @LocationHandle",
                )
            )

    # Once a canonical handle is declared, the same exact asset name must not
    # appear bare inside prompt blocks.
    handles = sorted({token[1:] for token in ANY_AT_TOKEN.findall(text) if CANONICAL_HANDLE.match(token)})
    if handles:
        for prompt_start, block in blocks_between(text, PROMPT_MARKER):
            for handle in handles:
                pattern = re.compile(rf"(?<!@)\b{re.escape(handle)}\b")
                for match in pattern.finditer(block):
                    findings.append(
                        (
                            line_of(text, prompt_start + match.start()),
                            handle,
                            f"referenced asset must be written as @{handle}",
                        )
                    )

    return sorted(set(findings))


def check_audio(text: str) -> list[Issue]:
    findings: list[Issue] = []
    for start, block in blocks_between(text, VIDEO_PROMPT_MARKER):
        if not AUDIO_MARKER.search(block):
            header = block.strip().split("\n")[0].strip()
            findings.append(
                (
                    line_of(text, start),
                    header[:60] or "(video prompt)",
                    "no AUDIO block; use AUDIO: Intentional silence. when silence is deliberate",
                )
            )
    return findings


def _format_intervals(intervals: Iterable[tuple[int, int]], limit: int = 4) -> str:
    shown = list(intervals)[:limit]
    return ", ".join(f"{start}-{end}s" for start, end in shown)


def video_prompt_region(segment_block: str) -> str:
    video_match = VIDEO_PROMPT_MARKER.search(segment_block)
    if video_match is None:
        return segment_block
    end = len(segment_block)
    for marker_match in PROMPT_MARKER.finditer(segment_block, video_match.end()):
        end = marker_match.start()
        break
    return segment_block[video_match.start():end]


def interval_problems(raw: list[tuple[int, int]], segment_length: int, mode: str) -> list[str]:
    problems: list[str] = []
    counts = Counter(raw)
    duplicates = [interval for interval, count in counts.items() if count > 1]
    if duplicates:
        problems.append(f"duplicate interval(s): {_format_intervals(duplicates)}")

    if raw != sorted(raw):
        problems.append("intervals are out of chronological order")

    reversed_intervals = [interval for interval in raw if interval[1] <= interval[0]]
    if reversed_intervals:
        problems.append(f"reversed or zero-length interval(s): {_format_intervals(reversed_intervals)}")

    out_of_range = [interval for interval in raw if interval[0] < 0 or interval[1] > segment_length]
    if out_of_range:
        problems.append(f"out-of-range interval(s): {_format_intervals(out_of_range)}")

    if mode == "loose":
        return problems

    ordered = raw
    if ordered:
        if ordered[0][0] != 0:
            problems.append(f"timeline starts at {ordered[0][0]}s, expected 0s")
        if ordered[-1][1] != segment_length:
            problems.append(f"timeline ends at {ordered[-1][1]}s, expected {segment_length}s")

    for left, right in zip(ordered, ordered[1:]):
        if left[1] < right[0]:
            problems.append(f"gap between {left[1]}s and {right[0]}s")
        elif left[1] > right[0]:
            problems.append(f"overlap between {right[0]}s and {left[1]}s")

    if mode == "exact":
        expected = [(second, second + 1) for second in range(segment_length)]
        bad_length = [interval for interval in raw if interval[1] - interval[0] != 1]
        if bad_length:
            problems.append(f"non-one-second interval(s): {_format_intervals(bad_length)}")
        missing = [interval for interval in expected if interval not in counts]
        unexpected = [interval for interval in raw if interval not in set(expected)]
        if len(raw) != segment_length:
            problems.append(f"{len(raw)} beat lines, expected {segment_length}")
        if missing:
            problems.append(f"missing expected interval(s): {_format_intervals(missing)}")
        if unexpected:
            problems.append(f"unexpected interval(s): {_format_intervals(unexpected)}")

    return problems


def check_beats(text: str, segment_length: int, mode: str) -> list[Issue]:
    if mode == "off":
        return []

    findings: list[Issue] = []
    for start, block in blocks_between(text, SEGMENT_MARKER):
        segment_match = SEGMENT_MARKER.search(block)
        segment_id = segment_match.group(1) if segment_match else "?"
        video_prompt_found = VIDEO_PROMPT_MARKER.search(block) is not None
        beat_region = video_prompt_region(block)
        raw = [(int(a), int(b)) for a, b in BEAT_LINE.findall(beat_region)]
        if not raw:
            if video_prompt_found:
                findings.append(
                    (
                        line_of(text, start),
                        f"segment {segment_id}",
                        "recognized VIDEO PROMPT contains no beat timeline",
                    )
                )
            continue

        problems = interval_problems(raw, segment_length, mode)
        if problems:
            findings.append((line_of(text, start), f"segment {segment_id}", "; ".join(problems)))
    return findings


def check_model_duration(
    surface: str,
    model: str,
    mode: str,
    segment_length: int | None,
) -> list[Issue]:
    if not segment_length or surface == "unspecified" or model in {"unspecified", "other"}:
        return []

    supported: set[int] | None
    if mode != "unspecified":
        supported = MODE_DURATIONS.get(surface, {}).get(model, {}).get(mode)
    else:
        matrix = FLOW_DURATIONS if surface == "flow" else API_DURATIONS
        supported = matrix.get(model)

    if supported is None:
        return []
    profile = f"{surface}/{model}/{mode}" if mode != "unspecified" else f"{surface}/{model}"
    if not supported:
        return [(1, profile, "this generation mode is not supported by the selected profile")]
    if segment_length in supported:
        return []
    choices = ", ".join(str(value) for value in sorted(supported))
    return [
        (
            1,
            f"{profile}/{segment_length}s",
            f"unsupported duration for this profile; supported integer lengths: {choices}",
        )
    ]


def approximate_tokens(text: str) -> int:
    return len(re.findall(r"\w+|[^\w\s]", text, re.UNICODE))


def check_veo_prompt_length(text: str, surface: str, model: str) -> list[Issue]:
    if surface != "gemini-api" or not model.startswith("veo-3.1"):
        return []
    findings: list[Issue] = []
    for start, block in blocks_between(text, VIDEO_PROMPT_MARKER):
        estimate = approximate_tokens(block)
        if estimate > 1024:
            findings.append(
                (
                    line_of(text, start),
                    f"approximately {estimate} tokens",
                    "Veo 3.1 publishes a 1,024-token text-input limit; local estimate may differ from the service tokenizer",
                )
            )
    return findings


def report(name: str, issues: list[Issue], use_colour: bool, quiet: bool) -> bool:
    passed = not issues
    status = colour("PASS", GREEN, use_colour) if passed else colour(f"FAIL ({len(issues)})", RED, use_colour)
    print(f"  {name:.<34} {status}")
    if issues and not quiet:
        for line, snippet, reason in issues[:25]:
            print(f"      line {line}: {colour(snippet, YELLOW, use_colour)}  -  {reason}")
        if len(issues) > 25:
            print(f"      ... and {len(issues) - 25} more")
    return passed


def validate_file(
    path: Path,
    segment_length: int | None,
    beat_mode: str,
    surface: str,
    model: str,
    mode: str,
    require_audio: bool,
    use_colour: bool,
    quiet: bool,
    emit_text: bool,
    collected: list[dict],
) -> bool:
    raw = path.read_text(encoding="utf-8", errors="replace")

    if IGNORE_FILE.search(raw):
        if emit_text and not quiet:
            print(f"\n{colour(str(path), BOLD, use_colour)}")
            print("  skipped - marked validate:ignore-file (documentation, not a script)")
        collected.append({"file": str(path), "skipped": True, "disabled_checks": [], "checks": {}})
        return True

    text = blank_example_fences(raw)
    if emit_text:
        print(f"\n{colour(str(path), BOLD, use_colour)}")

    findings: dict[str, list[Issue]] = {
        "backward_references": check_patterns(text, BACKWARD_REFS),
        "text_bleed_tokens": check_patterns(text, TOKEN_LEAKS),
        "em_dashes": check_em_dashes(text),
        "text_policy": check_text_policy(text),
        "reference_handles": check_reference_handles(text),
        "storyboard_contract": check_storyboard_contract(text, segment_length),
        "unsupported_specifications": check_patterns(text, SPEC_VIOLATIONS),
        "model_duration": check_model_duration(surface, model, mode, segment_length),
        "veo_prompt_length": check_veo_prompt_length(text, surface, model),
    }
    disabled_checks: list[str] = []

    if segment_length is not None and beat_mode != "off":
        findings["beat_timeline"] = check_beats(text, segment_length, beat_mode)
    else:
        disabled_checks.append("beat_timeline")

    if require_audio:
        findings["audio_direction"] = check_audio(text)
    else:
        disabled_checks.append("audio_direction")

    labels = {
        "backward_references": "Backward references",
        "text_bleed_tokens": "Text-bleed tokens",
        "em_dashes": "Em dashes",
        "text_policy": "Text policy",
        "reference_handles": "Reference handles",
        "storyboard_contract": "Storyboard contract",
        "beat_timeline": "Beat timeline",
        "unsupported_specifications": "Unsupported specifications",
        "model_duration": "Model duration",
        "veo_prompt_length": "Veo prompt length estimate",
        "audio_direction": "Audio direction",
    }

    all_passed = True
    for key, issues in findings.items():
        if emit_text:
            all_passed = report(labels[key], issues, use_colour, quiet) and all_passed
        else:
            all_passed = not issues and all_passed

    if emit_text and disabled_checks and not quiet:
        print(f"  disabled checks: {', '.join(disabled_checks)}")

    collected.append(
        {
            "file": str(path),
            "skipped": False,
            "passed": all_passed,
            "disabled_checks": disabled_checks,
            "checks": {
                key: [
                    {"line": line, "snippet": snippet, "reason": reason}
                    for line, snippet, reason in issues
                ]
                for key, issues in findings.items()
            },
        }
    )
    return all_passed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Markdown or text scripts to validate")
    parser.add_argument("--segment-length", type=int, help="segment duration in whole seconds")
    parser.add_argument(
        "--beat-mode",
        choices=["exact", "coverage", "loose", "off"],
        default="exact",
        help="timeline policy: exact one-second beats, full coverage, loose intervals, or off",
    )
    parser.add_argument(
        "--surface",
        choices=["unspecified", "flow", "gemini-api"],
        default="unspecified",
    )
    parser.add_argument(
        "--model",
        choices=[
            "unspecified",
            "veo-3.1",
            "veo-3.1-lite",
            "veo-3.1-fast",
            "veo-3.1-quality",
            "omni-flash",
            "other",
        ],
        default="unspecified",
    )
    parser.add_argument(
        "--mode",
        choices=[
            "unspecified",
            "text-to-video",
            "first-frame",
            "first-last-frame",
            "references-to-video",
            "video-edit",
            "extend",
        ],
        default="unspecified",
        help="generation mode for model-specific compatibility checks",
    )
    parser.add_argument("--no-require-audio", action="store_true")
    parser.add_argument("--json", action="store_true", help="emit pure JSON")
    parser.add_argument("--quiet", action="store_true", help="hide individual issue details")
    parser.add_argument("--no-colour", action="store_true")
    parser.add_argument("--version", action="version", version=VERSION)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.segment_length is not None and not 3 <= args.segment_length <= 10:
        print("error: --segment-length must be between 3 and 10", file=sys.stderr)
        return 2

    missing = [str(path) for path in args.paths if not path.is_file()]
    if missing:
        print(f"error: file not found: {', '.join(missing)}", file=sys.stderr)
        return 2

    collected: list[dict] = []
    emit_text = not args.json
    use_colour = not args.no_colour and sys.stdout.isatty() and emit_text
    all_passed = True

    if emit_text:
        print(f"Flow Script Validator {VERSION}")
        print(
            f"settings: segment_length={args.segment_length}, beat_mode={args.beat_mode}, "
            f"surface={args.surface}, model={args.model}, mode={args.mode}, require_audio={not args.no_require_audio}"
        )

    for path in args.paths:
        all_passed = validate_file(
            path=path,
            segment_length=args.segment_length,
            beat_mode=args.beat_mode,
            surface=args.surface,
            model=args.model,
            mode=args.mode,
            require_audio=not args.no_require_audio,
            use_colour=use_colour,
            quiet=args.quiet,
            emit_text=emit_text,
            collected=collected,
        ) and all_passed

    payload = {
        "version": VERSION,
        "passed": all_passed,
        "settings": {
            "segment_length": args.segment_length,
            "beat_mode": args.beat_mode,
            "surface": args.surface,
            "model": args.model,
            "mode": args.mode,
            "require_audio": not args.no_require_audio,
        },
        "files": collected,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    elif all_passed:
        print("\nVERDICT: enabled mechanical checks passed.")
    else:
        print("\nVERDICT: do not generate. Fix the failed checks and run again.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
