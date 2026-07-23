#!/usr/bin/env python3
"""Mechanical checks for Google Flow and Veo production scripts.

The validator checks only conditions that can be found by pattern or structure:
backward references, text-bleed tokens, prompt text policy, beat timelines,
unsupported specifications, and optional audio direction.

Ordinary fenced blocks are validated. Deliberate examples can be excluded with
```` ```example ```` (also counterexample, bad, dont, avoid), or an entire file
can opt out with ``<!-- validate:ignore-file -->``.

Every prompt must start with an explicit text policy as its first semantic line:

    NO TEXT IN THE IMAGE: do not render labels, captions or watermarks.

or, when text is intentional:

    INTENTIONAL TEXT IN THE IMAGE: package reads "ACME" only.

Audio direction is required by default. ``AUDIO: Intentional silence.`` is valid.
Use ``--no-require-audio`` for visual-only previs or sound added entirely in post.

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

VERSION = "1.3.1"

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
        "vague continuation - describe the incoming frame in full",
    ),
    (
        r"\bstill (?:wet|dirty|torn|bleeding|holding|wearing|soaked|muddy)\b",
        '"still X" assumes memory - state the condition outright',
    ),
    (r"\bsame as (?:above|before|previous)\b", "refers to earlier content"),
    (r"\bpreviously (?:seen|shown|established)\b", "refers to earlier content"),
]

TOKEN_LEAKS = [
    (r"\b\d{3,5}\s?K\b", "colour temperature value - use plain words"),
    (
        r"#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})\b",
        "hex colour code - use a colour name",
    ),
    (
        r"#(?=[0-9A-Fa-f]{3,4}\b)(?=[0-9A-Fa-f]*[A-Fa-f])[0-9A-Fa-f]{3,4}\b",
        "short hex colour code - use a colour name",
    ),
    (
        r"\((?:[A-Z][A-Za-z']*\s+){1,4}(?:Lane|Market|Street|Room|Interior|Exterior|House|Shop|Studio|Stall|Path|Clearing)\)",
        "set name in brackets - may be rendered as a caption",
    ),
]

SPEC_VIOLATIONS = [
    (r"\b10\s*-?\s*second\s+(?:segment|clip|shot)", "ten-second segments are not supported by this workflow - use 4, 6 or 8"),
    (r"\bten\s*-?\s*second\s+(?:segment|clip|shot)", "ten-second segments are not supported by this workflow - use 4, 6 or 8"),
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
    r"^[ \t]*(?:VIDEO PROMPT|STORYBOARD IMAGE PROMPT|IMAGE PROMPT|REFERENCE SHEET)",
    re.I | re.M,
)
VIDEO_PROMPT_MARKER = re.compile(r"^[ \t]*VIDEO PROMPT", re.I | re.M)
SEGMENT_MARKER = re.compile(r"^[ \t]*(?:SEGMENT|SEG)\s+([\d.]+)", re.I | re.M)
BEAT_LINE = re.compile(r"^[ \t]*(\d+)\s*-\s*(\d+)\s*s\s*:", re.I | re.M)
AUDIO_MARKER = re.compile(r"^[ \t]*AUDIO\s*:", re.I | re.M)
FENCE_LINE = re.compile(r"^(?:```|~~~)")

RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BOLD = "\033[1m"

Issue = tuple[int, str, str]


def colour(text: str, code: str, use_colour: bool) -> str:
    return f"{code}{text}{RESET}" if use_colour else text


def line_of(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def blank_example_fences(text: str) -> str:
    """Blank only fences explicitly tagged as counterexamples.

    Newlines are retained so issue locations still match the source file.
    """
    return EXAMPLE_FENCE.sub(lambda match: "\n" * match.group(0).count("\n"), text)


def blocks_between(text: str, marker: re.Pattern[str]) -> Iterable[tuple[int, str]]:
    starts = [match.start() for match in marker.finditer(text)]
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(text)
        yield start, text[start:end]


def first_semantic_line(block: str) -> tuple[int, str] | None:
    """Return the offset and text of the first meaningful line after a prompt header."""
    lines = block.splitlines(keepends=True)
    offset = len(lines[0]) if lines else 0
    for line in lines[1:]:
        stripped = line.strip()
        if stripped and not FENCE_LINE.match(stripped) and not stripped.startswith("<!--"):
            return offset, stripped
        offset += len(line)
    return None


def check_patterns(text: str, patterns: list[tuple[str, str]]) -> list[Issue]:
    findings: list[Issue] = []
    for pattern, reason in patterns:
        for match in re.finditer(pattern, text, re.I):
            findings.append((line_of(text, match.start()), match.group(0).strip(), reason))
    return sorted(findings)


def check_text_policy(text: str) -> list[Issue]:
    findings: list[Issue] = []
    for start, block in blocks_between(text, PROMPT_MARKER):
        header = block.strip().split("\n")[0].strip() or "(prompt)"
        semantic = first_semantic_line(block)
        if semantic is None:
            findings.append(
                (line_of(text, start), header[:60], "prompt has no content or explicit text policy")
            )
            continue
        relative_offset, first_line = semantic
        if not TEXT_POLICY_MARKER.match(first_line):
            findings.append(
                (
                    line_of(text, start + relative_offset),
                    first_line[:60],
                    "the first semantic prompt line must declare NO TEXT or INTENTIONAL TEXT",
                )
            )
    return findings


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
    """Return the VIDEO PROMPT sub-block, or the segment if no marker exists.

    A recognized VIDEO PROMPT is never replaced by storyboard content merely
    because it is empty or malformed. Its region ends at the next prompt marker.
    """
    video_match = VIDEO_PROMPT_MARKER.search(segment_block)
    if video_match is None:
        return segment_block
    end = len(segment_block)
    for marker_match in PROMPT_MARKER.finditer(segment_block, video_match.end()):
        end = marker_match.start()
        break
    return segment_block[video_match.start():end]


def check_beats(text: str, segment_length: int) -> list[Issue]:
    """Require the exact ordered timeline 0-1s, 1-2s ... N-1-Ns.

    Raw order and duplicates are deliberately preserved. Normalising with
    ``sorted(set(...))`` would hide two dangerous classes of malformed script.
    """
    findings: list[Issue] = []
    expected = [(second, second + 1) for second in range(segment_length)]
    expected_set = set(expected)

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
        if raw == expected:
            continue

        problems: list[str] = []
        counts = Counter(raw)
        duplicates = [interval for interval, count in counts.items() if count > 1]
        unique_chronological = sorted(counts)

        if duplicates:
            problems.append(f"duplicate beat interval(s): {_format_intervals(duplicates)}")

        if raw != sorted(raw):
            problems.append("beat lines are out of chronological order")

        bad_length = [interval for interval in raw if interval[1] - interval[0] != 1]
        if bad_length:
            problems.append(
                f"{len(bad_length)} beat line(s) are not one second long ({_format_intervals(bad_length)})"
            )

        reversed_intervals = [interval for interval in raw if interval[1] <= interval[0]]
        if reversed_intervals:
            problems.append(f"{len(reversed_intervals)} reversed or zero-length beat(s)")

        if unique_chronological and unique_chronological[0][0] != 0:
            problems.append(
                f"timeline starts at {unique_chronological[0][0]}s, expected 0s"
            )

        gaps = [
            (unique_chronological[index][1], unique_chronological[index + 1][0])
            for index in range(len(unique_chronological) - 1)
            if unique_chronological[index][1] < unique_chronological[index + 1][0]
        ]
        if gaps:
            problems.append(f"{len(gaps)} gap(s) in the timeline ({_format_intervals(gaps)})")

        overlaps = [
            (unique_chronological[index], unique_chronological[index + 1])
            for index in range(len(unique_chronological) - 1)
            if unique_chronological[index][1] > unique_chronological[index + 1][0]
        ]
        if overlaps:
            problems.append(f"{len(overlaps)} overlapping beat interval(s)")

        if len(raw) != segment_length:
            problems.append(f"{len(raw)} beat lines, expected {segment_length}")

        if len(unique_chronological) != segment_length:
            problems.append(
                f"{len(unique_chronological)} distinct beats, expected {segment_length}"
            )

        missing = [interval for interval in expected if interval not in counts]
        unexpected = [interval for interval in unique_chronological if interval not in expected_set]
        if missing:
            problems.append(f"missing expected interval(s): {_format_intervals(missing)}")
        if unexpected:
            problems.append(f"unexpected interval(s): {_format_intervals(unexpected)}")

        if unique_chronological and unique_chronological[-1][1] != segment_length:
            problems.append(
                f"timeline ends at {unique_chronological[-1][1]}s, expected {segment_length}s"
            )

        if not problems:
            problems.append("timeline does not exactly match the expected ordered intervals")

        findings.append(
            (line_of(text, start), f"segment {segment_id}", "; ".join(problems))
        )
    return findings


def report(name: str, issues: list[Issue], use_colour: bool, quiet: bool) -> bool:
    passed = not issues
    status = (
        colour("PASS", GREEN, use_colour)
        if passed
        else colour(f"FAIL ({len(issues)})", RED, use_colour)
    )
    print(f"  {name:.<34} {status}")
    if issues and not quiet:
        for line, snippet, reason in issues[:25]:
            print(
                f"      line {line}: {colour(snippet, YELLOW, use_colour)}  -  {reason}"
            )
        if len(issues) > 25:
            print(f"      ... and {len(issues) - 25} more")
    return passed


def validate_file(
    path: Path,
    segment_length: int | None,
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
        collected.append(
            {"file": str(path), "skipped": True, "disabled_checks": [], "checks": {}}
        )
        return True

    text = blank_example_fences(raw)
    if emit_text:
        print(f"\n{colour(str(path), BOLD, use_colour)}")

    findings: dict[str, list[Issue]] = {
        "backward_references": check_patterns(text, BACKWARD_REFS),
        "text_bleed_tokens": check_patterns(text, TOKEN_LEAKS),
        "text_policy": check_text_policy(text),
        "unsupported_specifications": check_patterns(text, SPEC_VIOLATIONS),
        "audio_direction": check_audio(text) if require_audio else [],
    }
    if segment_length is not None:
        findings["beat_timeline"] = check_beats(text, segment_length)

    labels = [
        ("1. Backward references", "backward_references", True),
        ("2. Text-bleed tokens", "text_bleed_tokens", True),
        ("3. Text policy", "text_policy", True),
        (
            "4. Beat timeline" + (f" (expect {segment_length})" if segment_length else ""),
            "beat_timeline",
            segment_length is not None,
        ),
        ("5. Unsupported specifications", "unsupported_specifications", True),
        ("6. Audio direction", "audio_direction", require_audio),
    ]

    enabled_results: list[bool] = []
    if emit_text:
        for label, key, enabled in labels:
            if not enabled:
                why = "pass --segment-length" if key == "beat_timeline" else "disabled by --no-require-audio"
                print(f"  {label:.<34} SKIPPED ({why})")
                continue
            enabled_results.append(report(label, findings[key], use_colour, quiet))
    else:
        enabled_results = [not findings[key] for _, key, enabled in labels if enabled]

    disabled_checks = [key for _, key, enabled in labels if not enabled]
    collected.append(
        {
            "file": str(path),
            "skipped": False,
            "disabled_checks": disabled_checks,
            "checks": {
                key: [
                    {"line": line, "match": match, "reason": reason}
                    for line, match, reason in issues
                ]
                for key, issues in findings.items()
            },
        }
    )
    return all(enabled_results)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mechanical checks for a Google Flow production script.",
        epilog=(
            "Exclude deliberate counterexamples with <!-- validate:ignore-file --> "
            "or a fence tagged ```example."
        ),
    )
    parser.add_argument("path", help="script file, or a directory of Markdown scripts")
    parser.add_argument(
        "--segment-length",
        type=int,
        default=None,
        choices=[4, 6, 8],
        help="seconds per segment; enables exact beat-timeline checking",
    )
    audio_group = parser.add_mutually_exclusive_group()
    audio_group.add_argument(
        "--require-audio",
        dest="require_audio",
        action="store_true",
        default=True,
        help="require an AUDIO block in each video prompt (default)",
    )
    audio_group.add_argument(
        "--no-require-audio",
        dest="require_audio",
        action="store_false",
        help="skip the AUDIO-block check for visual-only or post-audio workflows",
    )
    parser.add_argument("--quiet", action="store_true", help="show pass/fail only")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON only")
    parser.add_argument("--no-colour", action="store_true")
    parser.add_argument("--version", action="version", version=f"validate.py {VERSION}")
    args = parser.parse_args()

    use_colour = sys.stdout.isatty() and not args.no_colour and not args.json
    root = Path(args.path)
    if not root.exists():
        print(f"not found: {root}", file=sys.stderr)
        return 2

    files = sorted(
        path
        for path in (root.rglob("*.md") if root.is_dir() else [root])
        if path.is_file()
    )
    if not files:
        print("no files to check", file=sys.stderr)
        return 2

    collected: list[dict] = []
    if not args.json:
        print(colour(f"\nGoogle Flow script validation (v{VERSION})", BOLD, use_colour))

    all_passed = True
    for file_path in files:
        if not validate_file(
            file_path,
            args.segment_length,
            args.require_audio,
            use_colour,
            args.quiet,
            not args.json,
            collected,
        ):
            all_passed = False

    if args.json:
        print(
            json.dumps(
                {
                    "version": VERSION,
                    "passed": all_passed,
                    "settings": {
                        "segment_length": args.segment_length,
                        "require_audio": args.require_audio,
                    },
                    "files": collected,
                },
                indent=2,
            )
        )
        return 0 if all_passed else 1

    print()
    if all_passed:
        print(colour("VERDICT: enabled mechanical checks passed.", GREEN, use_colour))
        print("Now run the flow-continuity-auditor for judgement checks:")
        print("  final-frame chain, handoff classification, reference coverage, state continuity.")
    else:
        print(colour("VERDICT: DO NOT GENERATE. Fix the findings and re-run.", RED, use_colour))
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
