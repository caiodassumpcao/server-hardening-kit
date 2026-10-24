#!/usr/bin/env bash
# Instala as coleções do requirements.yml com retentativa e espera crescente.
# O Ansible Galaxy tem instabilidades (HTTP 5xx) que derrubariam o CI à toa.
#   uso: scripts/galaxy-install.sh [caminho/do/ansible-galaxy]
set -uo pipefail

galaxy="${1:-ansible-galaxy}"
attempts=4

for i in $(seq 1 "$attempts"); do
  "$galaxy" collection install -r requirements.yml && exit 0
  wait_s=$((i * 20))
  echo "ansible-galaxy falhou (tentativa $i/$attempts); nova tentativa em ${wait_s}s..." >&2
  [ "$i" -lt "$attempts" ] && sleep "$wait_s"
done
exit 1
