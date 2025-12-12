#!/bin/bash
# Hook PostToolUse pour capturer les URLs WebFetch dans rekall
#
# Installation automatique: rekall sources setup-hook
# Ou manuellement: Ajouter dans ~/.claude/settings.json:
#   "hooks": {
#     "PostToolUse": [
#       { "matcher": "WebFetch", "hooks": [{"type": "command", "command": "~/.claude/hooks/rekall-webfetch.sh"}] }
#     ]
#   }

# Read JSON from stdin
INPUT=$(cat)

# Extract tool name and check if it's WebFetch
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

if [ "$TOOL_NAME" != "WebFetch" ]; then
    exit 0
fi

# Extract URL from tool_input
URL=$(echo "$INPUT" | jq -r '.tool_input.url // empty')

if [ -z "$URL" ]; then
    exit 0
fi

# Extract project context if available (from session_id or working directory)
PROJECT=$(echo "$INPUT" | jq -r '.session.project // empty')
if [ -z "$PROJECT" ]; then
    # Fallback: use current directory name
    PROJECT=$(basename "$(pwd)")
fi

# Extract conversation_id if available
CONV_ID=$(echo "$INPUT" | jq -r '.session.conversation_id // empty')

# Add to rekall inbox (fire and forget, don't block Claude)
# Use --quiet to suppress output, run in background
(
    rekall sources inbox add "$URL" \
        --cli claude \
        ${PROJECT:+--project "$PROJECT"} \
        ${CONV_ID:+--conversation "$CONV_ID"} \
        --quiet 2>/dev/null
) &

exit 0
