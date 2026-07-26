#!/usr/bin/env python3
"""Generate a contract-compliant visual storyboard package from a JSON specification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

CANONICAL_HANDLE = re.compile(r"^@[A-Za-z][A-Za-z0-9]*$")
HARD_STORYBOARD_RULE = "A storyboard-generation prompt must command image generation in its first sentence, declare the exact output count and layout, prohibit planning responses, and enumerate forbidden invented actions."
FIRST_SENTENCE = "GENERATE THE STORYBOARD IMAGE NOW."

DEFAULT_LAYOUTS = {
    4: (2, "2x1"),
    6: (3, "3x1"),
    8: (3, "3x1"),
    10: (4, "2x2"),
}

GRID_POSITIONS = {
    "2x1": ["left", "right"],
    "3x1": ["left", "centre", "right"],
    "2x2": ["top left", "top right", "bottom left", "bottom right"],
    "3x3": [
        "top left", "top centre", "top right",
        "middle left", "middle centre", "middle right",
        "bottom left", "bottom centre", "bottom right",
    ],
}


def clean_text(value: str) -> str:
    return value.replace(chr(0x2014), " - ").replace(chr(0x2013), " - ").strip()


def require_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return clean_text(value)


def validate_handle(value: str, field: str) -> str:
    handle = clean_text(value)
    if not CANONICAL_HANDLE.fullmatch(handle):
        raise ValueError(f"{field} must be a canonical handle such as @SidewalkCafe")
    return handle


def replace_bare_handles(text: str, handles: list[str]) -> str:
    result = clean_text(text)
    for handle in sorted(handles, key=len, reverse=True):
        name = handle[1:]
        result = re.sub(rf"(?<!@)\b{re.escape(name)}\b", handle, result)
    return result


def load_spec(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("specification root must be a JSON object")
    return data


def normalise_spec(data: dict[str, Any]) -> dict[str, Any]:
    segment_id = str(data.get("segment_id", "1"))
    length = data.get("segment_length")
    if not isinstance(length, int) or length not in DEFAULT_LAYOUTS:
        raise ValueError("segment_length must be 4, 6, 8, or 10")

    characters_raw = data.get("characters", [])
    if not isinstance(characters_raw, list):
        raise ValueError("characters must be a list of canonical @Handles")
    characters = [validate_handle(item, "characters entry") for item in characters_raw]
    location = validate_handle(require_string(data, "location"), "location")
    handles = [*characters, location]

    panels_raw = data.get("panels")
    if not isinstance(panels_raw, list) or not panels_raw:
        raise ValueError("panels must be a non-empty list")

    default_count, default_layout = DEFAULT_LAYOUTS[length]
    allow_nine = bool(data.get("allow_nine_panel"))
    if len(panels_raw) == 9:
        if not allow_nine:
            raise ValueError("nine panels require allow_nine_panel=true")
        panel_count, layout = 9, "3x3"
    else:
        panel_count = int(data.get("panel_count", default_count))
        layout = clean_text(str(data.get("layout", default_layout))).lower()
        if panel_count != default_count or layout != default_layout:
            raise ValueError(f"{length}s defaults to {default_count} panels in {default_layout}")
        if len(panels_raw) != panel_count:
            raise ValueError(f"panels contains {len(panels_raw)} entries, expected {panel_count}")

    panels: list[dict[str, str]] = []
    for index, panel in enumerate(panels_raw):
        if not isinstance(panel, dict):
            raise ValueError(f"panel {index + 1} must be an object")
        label = chr(ord("A") + index)
        moment = replace_bare_handles(require_string(panel, "moment"), handles)
        framing = replace_bare_handles(require_string(panel, "framing"), handles)
        action = replace_bare_handles(require_string(panel, "action"), handles)
        forbidden_raw = panel.get("forbidden_actions", [])
        if isinstance(forbidden_raw, str):
            forbidden_raw = [forbidden_raw]
        if not isinstance(forbidden_raw, list) or not all(isinstance(item, str) for item in forbidden_raw):
            raise ValueError(f"panel {label} forbidden_actions must be a list of strings")
        forbidden = "; ".join(replace_bare_handles(item, handles) for item in forbidden_raw) or "Do not invent any additional action."
        panels.append({
            "label": label,
            "position": GRID_POSITIONS[layout][index],
            "moment": moment,
            "framing": framing,
            "action": action,
            "forbidden": forbidden,
        })

    return {
        "segment_id": segment_id,
        "segment_length": length,
        "panel_count": panel_count,
        "layout": layout,
        "characters": characters,
        "location": location,
        "handles": handles,
        "style": replace_bare_handles(require_string(data, "style"), handles),
        "location_description": replace_bare_handles(require_string(data, "location_description"), handles),
        "lighting": replace_bare_handles(require_string(data, "lighting"), handles),
        "camera_plan": replace_bare_handles(require_string(data, "camera_plan"), handles),
        "continuity": [replace_bare_handles(str(item), handles) for item in data.get("continuity", [])],
        "operator_notes": [clean_text(str(item)) for item in data.get("operator_notes", [])],
        "approval_checks": [replace_bare_handles(str(item), handles) for item in data.get("approval_checks", [])],
        "panels": panels,
        "panel_aspect_ratio": clean_text(str(data.get("panel_aspect_ratio", "9:16"))),
    }


def render(spec: dict[str, Any]) -> str:
    characters = ", ".join(spec["characters"]) if spec["characters"] else "NONE"
    lines: list[str] = [
        f"SEGMENT {spec['segment_id']}",
        "",
        "INTERNAL OPERATOR NOTE",
        "Do not send this section to the image generator.",
        f"References to attach: {characters}, {spec['location']}",
        f"Segment length: {spec['segment_length']} seconds",
        f"Required contact sheet: {spec['panel_count']} panels in {spec['layout']}",
    ]
    for note in spec["operator_notes"]:
        lines.append(f"- {note}")

    lines.extend(
        [
            "",
            "STORYBOARD CONTACT SHEET PROMPT",
            "```",
            FIRST_SENTENCE,
            "",
            "Do not write a storyboard, scene breakdown, asset list, explanation, proposal, or follow-up question.",
            "",
            f"Create exactly ONE finished storyboard contact sheet containing exactly {spec['panel_count']} cinematic still-image panels arranged in a clean {spec['layout']} grid.",
            "Panel order: " + "; ".join(
                f"Panel {panel['label']} is {panel['position']}" for panel in spec["panels"]
            ) + ".",
            "",
            "Do not create additional panels.",
            *( ["All nine distinct frames were explicitly authored. Do not invent filler frames."] if spec["panel_count"] == 9 else [] ),
            "Do not invent additional actions.",
            "Do not ask for permission before generating.",
            "",
            "NO TEXT IN THE IMAGE: do not render any words, letters, numbers, panel labels, captions, subtitles, timecodes, logos, or watermarks.",
            "",
            f"CHARACTER REFERENCES: {characters}",
            f"LOCATION REFERENCE: {spec['location']}",
            "",
            "Use every attached reference as the authoritative visual source. Do not redesign any referenced character or location.",
            f"Each panel uses a {spec['panel_aspect_ratio']} cinematic composition.",
            "",
            f"VISUAL STYLE: {spec['style']}",
            f"LOCATION: {spec['location']}. {spec['location_description']}",
            f"LIGHTING: {spec['lighting']}",
            f"CAMERA PLAN FOR THE SEGMENT: {spec['camera_plan']}",
            "",
            "CONTINUITY REQUIREMENTS:",
        ]
    )
    continuity = spec["continuity"] or [
        "Keep every referenced face, hairstyle, body proportion, wardrobe item, prop, and location anchor consistent across all panels.",
        "The final panel must be suitable for cropping into a standalone handoff image.",
    ]
    lines.extend(f"- {item}" for item in continuity)

    for panel in spec["panels"]:
        lines.extend(
            [
                "",
                f"PANEL {panel['label']} - {panel['position'].upper()}:",
                f"MOMENT: {panel['moment']}",
                f"FRAMING: {panel['framing']}",
                f"ACTION AND VISIBLE STATE: {panel['action']}",
                f"FORBIDDEN INVENTED ACTIONS: {panel['forbidden']}",
            ]
        )

    lines.extend(
        [
            "",
            "Return only the completed storyboard contact sheet image.",
            "```",
            "",
            "DO NOT INCLUDE THIS CHECKLIST IN THE GENERATION PROMPT",
        ]
    )
    checks = spec["approval_checks"] or [
        "Every referenced face and location matches its approved image.",
        "Every character and location reference uses its canonical @Handle.",
        "No extra panel, action, character, prop, text, number, caption, logo, or watermark was invented.",
        "The final panel matches the required handoff state.",
    ]
    lines.extend(f"- [ ] {item}" for item in checks)
    result = "\n".join(lines).rstrip() + "\n"
    if chr(0x2014) in result:
        raise AssertionError("generated output contains an em dash")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="JSON storyboard specification")
    parser.add_argument("--output", type=Path, help="write to a file instead of stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        output = render(normalise_spec(load_spec(args.spec)))
    except (FileNotFoundError, ValueError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
