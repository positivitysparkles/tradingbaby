#!/usr/bin/env bash
# PostCompact hook — restore autoCompactThreshold after compaction completes.
#
# compact-threshold-stop.sh lowered the threshold to 1 to trigger compact.
# This hook puts it back to 197k so normal operation resumes.

set -euo pipefail

SETTINGS="$HOME/.claude/settings.json"
RESTORE_THRESHOLD=197000

if [[ ! -f "$SETTINGS" ]]; then
    echo "post-compact-restore: settings.json not found, cannot restore threshold." >&2
    exit 0
fi

CURRENT=$(jq -r '.autoCompactThreshold // empty' "$SETTINGS" 2>/dev/null)

# Only write if it needs changing (avoid unnecessary file churn)
if [[ "$CURRENT" != "$RESTORE_THRESHOLD" ]]; then
    TMPFILE=$(mktemp)
    jq ".autoCompactThreshold = $RESTORE_THRESHOLD" "$SETTINGS" > "$TMPFILE" && mv "$TMPFILE" "$SETTINGS"
    echo "post-compact-restore: autoCompactThreshold → ${RESTORE_THRESHOLD}" >&2
fi

exit 0
