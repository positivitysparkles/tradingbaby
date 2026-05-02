#!/usr/bin/env bash
# Stop hook — monitors context token usage and arms auto-compact at the exact moment
# Claude finishes its output (never mid-operation).
#
# Flow:
#   1. Read the JSONL transcript and get the latest context token count.
#   2. If tokens > TRIGGER_THRESHOLD, set autoCompactThreshold = 1 in settings.json.
#   3. On the user's next message, Claude Code sees "1 token used / 1 allowed" → fires
#      pre-compact hook → runs compact → fires post-compact hook which restores the threshold.

set -euo pipefail

INPUT=$(cat)

# Bail early on recursion (Stop hook calling Stop hook)
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
[[ "$STOP_HOOK_ACTIVE" == "true" ]] && exit 0

SETTINGS="$HOME/.claude/settings.json"
TRIGGER_THRESHOLD=180000
RESTORE_THRESHOLD=197000

# ── locate the transcript ───────────────────────────────────────────────────
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // empty')

if [[ -z "$TRANSCRIPT" || ! -f "$TRANSCRIPT" ]]; then
    # Fallback: find transcript via session file (most recently modified session)
    SESSION_ID=$(
        ls -t "$HOME/.claude/sessions/"*.json 2>/dev/null \
        | head -1 \
        | xargs -I{} jq -r '.sessionId // empty' {} 2>/dev/null
    )
    if [[ -n "$SESSION_ID" ]]; then
        TRANSCRIPT=$(
            find "$HOME/.claude/projects" -name "${SESSION_ID}.jsonl" 2>/dev/null \
            | head -1
        )
    fi
fi

[[ -z "$TRANSCRIPT" || ! -f "$TRANSCRIPT" ]] && exit 0

# ── read current token count ────────────────────────────────────────────────
TOKENS=$(python3 "$HOME/.claude/scripts/get-context-tokens.py" "$TRANSCRIPT" 2>/dev/null)
TOKENS="${TOKENS:-0}"

# ── guard: only act when we're above the trigger ────────────────────────────
if (( TOKENS <= TRIGGER_THRESHOLD )); then
    exit 0
fi

# ── guard: don't re-arm if already armed ───────────────────────────────────
CURRENT_THRESHOLD=$(jq -r '.autoCompactThreshold // empty' "$SETTINGS" 2>/dev/null)
if [[ "$CURRENT_THRESHOLD" == "1" ]]; then
    exit 0
fi

# ── arm compact: lower threshold to 1 so next message triggers auto-compact ─
TMPFILE=$(mktemp)
jq ".autoCompactThreshold = 1" "$SETTINGS" > "$TMPFILE" && mv "$TMPFILE" "$SETTINGS"

echo "compact-threshold-stop: context=${TOKENS} tokens (>${TRIGGER_THRESHOLD}). autoCompactThreshold → 1. Compact will fire on next user message." >&2

exit 0
