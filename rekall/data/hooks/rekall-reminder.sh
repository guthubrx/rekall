#!/bin/bash
# Hook Stop pour rappeler de sauvegarder dans Rekall
# Detecte les patterns de resolution et injecte un rappel
#
# Installation: rekall hooks install --cli claude
# Configuration dans ~/.claude/settings.json:
# {
#   "hooks": {
#     "Stop": [
#       {
#         "matcher": "",
#         "hooks": [{"type": "command", "command": "~/.claude/hooks/rekall-reminder.sh"}]
#       }
#     ]
#   }
# }

# Lire le payload JSON depuis stdin
PAYLOAD=$(cat)

# Extraire le transcript_path et la derniere reponse
TRANSCRIPT_PATH=$(echo "$PAYLOAD" | jq -r '.transcript_path // empty')
STOP_HOOK_ACTIVE=$(echo "$PAYLOAD" | jq -r '.stop_hook_active // false')

# Si pas de transcript, sortir silencieusement
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
    exit 0
fi

# Lire les derniers messages du transcript (derniere reponse assistant)
LAST_RESPONSE=$(tail -20 "$TRANSCRIPT_PATH" 2>/dev/null | \
    jq -s '[.[] | select(.type == "assistant")] | last | .content // empty' 2>/dev/null | \
    tr -d '"')

# Si pas de reponse, sortir
if [ -z "$LAST_RESPONSE" ]; then
    exit 0
fi

# Convertir en minuscules pour la comparaison
LAST_RESPONSE_LOWER=$(echo "$LAST_RESPONSE" | tr '[:upper:]' '[:lower:]')

# Patterns de resolution (insensible a la casse)
RESOLUTION_PATTERNS=(
    "bug.*fix"
    "fix.*bug"
    "resolu"
    "resolved"
    "fixed"
    "corrected"
    "corrige"
    "probleme.*regle"
    "issue.*fixed"
    "working now"
    "ca marche"
    "fonctionne maintenant"
    "error.*gone"
    "erreur.*disparue"
    "successfully"
    "tests? pass"
)

# Patterns indiquant que Rekall a deja ete mentionne
REKALL_MENTIONED_PATTERNS=(
    "rekall"
    "/rekall"
    "rekall add"
    "rekall search"
)

# Verifier si Rekall est deja mentionne (evite le spam)
for pattern in "${REKALL_MENTIONED_PATTERNS[@]}"; do
    if echo "$LAST_RESPONSE_LOWER" | grep -qiE "$pattern"; then
        exit 0
    fi
done

# Verifier si un pattern de resolution est present
RESOLUTION_DETECTED=false
for pattern in "${RESOLUTION_PATTERNS[@]}"; do
    if echo "$LAST_RESPONSE_LOWER" | grep -qiE "$pattern"; then
        RESOLUTION_DETECTED=true
        break
    fi
done

# Si resolution detectee, injecter le rappel
if [ "$RESOLUTION_DETECTED" = true ]; then
    cat << 'EOF'
---
**Rekall Reminder**: Tu viens de resoudre un probleme. Pense a capturer cette connaissance avec `/rekall` ou propose a l'utilisateur de sauvegarder dans Rekall.
EOF
fi
