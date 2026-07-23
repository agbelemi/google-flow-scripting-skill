#!/usr/bin/env bash
# Install the Google Flow Scripting & Prompting Skill as a native SKILL.md package.

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_NAME="google-flow-scripting"

TOOL=""
DIVISION="all"
TARGET=""
DRY=0
FORCE=0
INSTALL_SUBAGENTS=0

usage() {
  cat <<'USAGE'
Install the Google Flow Scripting & Prompting Skill.

  ./scripts/install.sh --tool claude-code
  ./scripts/install.sh --tool cursor
  ./scripts/install.sh --tool windsurf
  ./scripts/install.sh --tool generic
  ./scripts/install.sh --tool cursor --dry-run
  ./scripts/install.sh --tool claude-code --install-subagents
  ./scripts/install.sh --tool cursor --target /custom/path

Native Skill destinations
  claude-code   ~/.claude/skills/google-flow-scripting/       global
  cursor        ./.cursor/skills/google-flow-scripting/       project
  windsurf      ./.windsurf/skills/google-flow-scripting/     project
  generic       ./flow-skill/google-flow-scripting/           project

Divisions
  all       install core and format resources
  core      install core resources only
  formats   install formats and their required core resources

Options
  --target PATH         override the destination directory
  --dry-run             show what would happen; write nothing
  --force               replace without asking (an automatic backup is kept)
  --install-subagents   Claude Code only: also install specialist subagents
  -h, --help            show this help

Non-interactive reinstall
  When no TTY is available, an existing Skill cannot be confirmed interactively.
  Pass --force to replace it predictably; the previous Skill is still backed up.
USAGE
}

require_value() {
  if [[ -z "${2:-}" || "${2:-}" == --* ]]; then
    printf 'Error: %s requires a value\n\n' "$1" >&2
    usage >&2
    exit 2
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tool) require_value "$1" "${2:-}"; TOOL="$2"; shift 2 ;;
    --division) require_value "$1" "${2:-}"; DIVISION="$2"; shift 2 ;;
    --target) require_value "$1" "${2:-}"; TARGET="$2"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    --force) FORCE=1; shift ;;
    --install-subagents) INSTALL_SUBAGENTS=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$TOOL" ]]; then
  echo "Where should this Skill be installed?"
  echo "  1) Claude Code   (global native Skill)"
  echo "  2) Cursor        (project native Skill)"
  echo "  3) Windsurf      (project native Skill)"
  echo "  4) Generic       (portable Skill folder)"
  read -rp "Choice [1]: " choice
  case "${choice:-1}" in
    1) TOOL="claude-code" ;;
    2) TOOL="cursor" ;;
    3) TOOL="windsurf" ;;
    4) TOOL="generic" ;;
    *) echo "Invalid choice." >&2; exit 2 ;;
  esac
fi

case "$TOOL" in
  claude-code)
    DEFAULT_DEST="$HOME/.claude/skills/$SKILL_NAME"
    SCOPE="global"
    INVOCATION="/$SKILL_NAME"
    ;;
  cursor)
    DEFAULT_DEST="./.cursor/skills/$SKILL_NAME"
    SCOPE="project-local"
    INVOCATION="/$SKILL_NAME"
    ;;
  windsurf)
    DEFAULT_DEST="./.windsurf/skills/$SKILL_NAME"
    SCOPE="project-local"
    INVOCATION="@$SKILL_NAME"
    ;;
  generic)
    DEFAULT_DEST="./flow-skill/$SKILL_NAME"
    SCOPE="project-local portable folder"
    INVOCATION="open SKILL.md in your agent"
    ;;
  *) printf 'Unknown tool: %s\n' "$TOOL" >&2; exit 2 ;;
esac

DEST="${TARGET:-$DEFAULT_DEST}"

case "$DIVISION" in
  all) INCLUDE_CORE=1; INCLUDE_FORMATS=1 ;;
  core) INCLUDE_CORE=1; INCLUDE_FORMATS=0 ;;
  formats)
    # Format specialists depend on the orchestrator, asset manager and auditor.
    INCLUDE_CORE=1; INCLUDE_FORMATS=1
    ;;
  *) printf 'Unknown division: %s (use all, core or formats)\n' "$DIVISION" >&2; exit 2 ;;
esac

if [[ $INSTALL_SUBAGENTS -eq 1 && "$TOOL" != "claude-code" ]]; then
  echo "Error: --install-subagents is available only for --tool claude-code." >&2
  exit 2
fi

echo
echo "Installing native Skill to: $DEST"
echo "Scope:                     $SCOPE"
echo "Requested division:        $DIVISION"
[[ "$DIVISION" == "formats" ]] && echo "Dependency resolution:     core included because formats require it"
[[ $INSTALL_SUBAGENTS -eq 1 ]] && echo "Claude subagents:           enabled"
[[ $DRY -eq 1 ]] && echo "Mode:                       dry run; nothing will be written"
echo

echo "Package contents:"
echo "  + SKILL.md"
echo "  + README.md, LICENSE, CHANGELOG.md, divisions.json"
echo "  + reference/"
echo "  + scripts/validate.py"
echo "  + examples/"
[[ $INCLUDE_CORE -eq 1 ]] && echo "  + core/"
[[ $INCLUDE_FORMATS -eq 1 ]] && echo "  + formats/"

if [[ $DRY -eq 1 ]]; then
  if [[ -e "$DEST" ]]; then
    echo "  ! existing destination would be backed up before replacement"
  fi
  if [[ $INSTALL_SUBAGENTS -eq 1 ]]; then
    echo "  + Claude subagents would be installed under ~/.claude/agents/"
  fi
  echo
  echo "Dry run complete."
  exit 0
fi

if [[ -e "$DEST" && $FORCE -eq 0 ]]; then
  echo
  echo "A Skill already exists at $DEST."
  echo "It will be moved to a timestamped backup before replacement."
  read -rp "Continue? [y/N]: " answer
  case "${answer:-N}" in
    [Yy]*) ;;
    *) echo "Cancelled. Nothing was written."; exit 0 ;;
  esac
fi

PARENT="$(dirname "$DEST")"
mkdir -p "$PARENT"
STAGING_ROOT="$(mktemp -d "$PARENT/.flow-install.XXXXXX")"
STAGE="$STAGING_ROOT/$SKILL_NAME"
cleanup() { rm -rf "$STAGING_ROOT"; }
trap cleanup EXIT
mkdir -p "$STAGE"

cp "$ROOT/SKILL.md" "$ROOT/README.md" "$ROOT/LICENSE" "$ROOT/CHANGELOG.md" "$ROOT/divisions.json" "$STAGE/"
cp -R "$ROOT/reference" "$ROOT/examples" "$STAGE/"
mkdir -p "$STAGE/scripts"
cp "$ROOT/scripts/validate.py" "$STAGE/scripts/"
chmod +x "$STAGE/scripts/validate.py"
[[ $INCLUDE_CORE -eq 1 ]] && cp -R "$ROOT/core" "$STAGE/"
[[ $INCLUDE_FORMATS -eq 1 ]] && cp -R "$ROOT/formats" "$STAGE/"

BACKUP=""
if [[ -e "$DEST" ]]; then
  stamp="$(date +%Y%m%d-%H%M%S)"
  BACKUP="${DEST}.bak-${stamp}-$$"
  mv "$DEST" "$BACKUP"
fi
mv "$STAGE" "$DEST"

if [[ $INSTALL_SUBAGENTS -eq 1 ]]; then
  AGENT_DEST="$HOME/.claude/agents"
  mkdir -p "$AGENT_DEST"
  for dir in "$ROOT/core" "$ROOT/formats"; do
    for file in "$dir"/*.md; do
      [[ -e "$file" ]] || continue
      target="$AGENT_DEST/$(basename "$file")"
      if [[ -e "$target" ]]; then
        mv "$target" "${target}.bak-$(date +%Y%m%d-%H%M%S)-$$"
      fi
      cp "$file" "$target"
    done
  done
fi

trap - EXIT
rm -rf "$STAGING_ROOT"

echo
echo "Installed $SKILL_NAME as a native Skill."
[[ -n "$BACKUP" ]] && echo "Previous installation backed up to: $BACKUP"
[[ $INSTALL_SUBAGENTS -eq 1 ]] && echo "Claude specialist subagents installed to: $HOME/.claude/agents"
echo "Invoke with: $INVOCATION"
echo
echo "Validate a finished script with:"
echo "  python $DEST/scripts/validate.py your-script.md --segment-length 8"
echo "For visual-only or post-audio workflows add: --no-require-audio"
