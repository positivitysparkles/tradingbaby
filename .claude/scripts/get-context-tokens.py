#!/usr/bin/env python3
"""
Parse a Claude Code JSONL transcript and return the context token count
from the most recent assistant turn.

Context window usage = input_tokens + cache_creation_input_tokens + cache_read_input_tokens
(these are all "tokens that were in the context" for that API call)

Usage: get-context-tokens.py <transcript_path>
Prints an integer to stdout; exits 0 always so callers get 0 on any failure.
"""
import json, sys

def main():
    if len(sys.argv) < 2:
        print(0)
        return

    path = sys.argv[1]
    latest_context = 0

    try:
        with open(path, "r") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    entry = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                if entry.get("type") != "assistant":
                    continue

                usage = entry.get("message", {}).get("usage", {})
                if not usage:
                    continue

                # These three fields together = everything that was in the context window
                context = (
                    usage.get("input_tokens", 0)
                    + usage.get("cache_creation_input_tokens", 0)
                    + usage.get("cache_read_input_tokens", 0)
                )
                if context > 0:
                    latest_context = context  # last assignment wins = most recent turn

    except Exception as e:
        print(f"get-context-tokens error: {e}", file=sys.stderr)

    print(latest_context)


if __name__ == "__main__":
    main()
