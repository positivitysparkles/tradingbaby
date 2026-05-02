#!/usr/bin/env bash
# PreCompact hook — lightweight vault memory preservation before compaction.
#
# Backs up vault.json (the session memory file) to ~/.claude/backups/ with a
# timestamp so nothing is ever lost across compaction cycles.
# Also writes the vault contents to stdout so Claude Code can inject them into
# the compacted summary as preserved memories.

set -euo pipefail

VAULT="$HOME/tradingbaby/.claude/memory/vault.json"
BACKUP_DIR="$HOME/.claude/backups"
TIMESTAMP=$(date +%s)

mkdir -p "$BACKUP_DIR"

if [[ -f "$VAULT" ]]; then
    BACKUP_PATH="${BACKUP_DIR}/vault-pre-compact-${TIMESTAMP}.json"
    cp "$VAULT" "$BACKUP_PATH"
    echo "pre-compact-vault-backup: saved ${VAULT} → ${BACKUP_PATH}" >&2

    # Emit vault contents as preserved context so the compact summary includes it.
    # Claude Code passes PreCompact stdout to the compaction prompt.
    echo "=== VAULT MEMORY (preserve across compact) ==="
    cat "$VAULT"
    echo ""
    echo "=== END VAULT MEMORY ==="
else
    echo "pre-compact-vault-backup: vault.json not found at ${VAULT}, skipping backup." >&2
fi

exit 0
