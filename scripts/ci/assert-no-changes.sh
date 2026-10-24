#!/usr/bin/env bash
# Falha se um log do ansible-playbook tiver qualquer task "changed" e publica
# cada uma como annotation do GitHub Actions (visível no resumo do PR sem abrir logs).
#   uso: assert-no-changes.sh <ansible.log> <título da annotation>
set -euo pipefail

log="$1"
title="${2:-Unexpected change}"

clean=$(sed 's/\x1b\[[0-9;]*m//g' "$log")

# Em tasks com loop, inclui o item (ex.: qual parâmetro do sysctl desviou).
changed_tasks=$(awk '
  /^TASK \[/ { task = $0; sub(/ \*+$/, "", task) }
  /^changed: / {
    item = ""
    if (match($0, /\(item=[^)]*\)/)) item = " " substr($0, RSTART, RLENGTH)
    print task item
  }' <<<"$clean" | sort -u)

if [ -n "$changed_tasks" ]; then
  while IFS= read -r task; do
    echo "::error title=${title}::${task}"
  done <<<"$changed_tasks"
  exit 1
fi

grep -Eq 'changed=0[[:space:]]+unreachable=0[[:space:]]+failed=0' <<<"$clean"
echo "ok: nenhuma task reportou changed"
