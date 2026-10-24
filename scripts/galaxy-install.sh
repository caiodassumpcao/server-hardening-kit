#!/usr/bin/env bash
# Instala as coleções Ansible num único ponto (make install e CI):
#   1. requirements.yml via Ansible Galaxy, com retentativa e espera crescente;
#   2. se o Galaxy continuar fora (HTTP 5xx), requirements-fallback.yml direto
#      dos repositórios oficiais no GitHub, em versões fixas.
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

echo "Galaxy indisponível: instalando a partir do GitHub (requirements-fallback.yml)" >&2
# --no-deps: as dependências transitivas estão declaradas no próprio arquivo de
# fallback; sem isso o ansible-galaxy voltaria a buscá-las no Galaxy.
"$galaxy" collection install --no-deps -r requirements-fallback.yml
