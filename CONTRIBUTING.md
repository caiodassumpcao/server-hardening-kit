# Contribuindo

Obrigado pelo interesse! Este guia resume como propor mudanças sem quebrar o
que já foi validado.

## Ambiente

```bash
make install && source .venv/bin/activate
pip install pre-commit && pre-commit install   # lint e gitleaks a cada commit
```

Testes de integração precisam de Docker (Linux, WSL2 ou o Dev Container).

## Antes de abrir um PR

```bash
make lint        # yamllint + ansible-lint (perfil production: precisa passar sem falhas)
make test-unit   # pytest do gerador de relatório
make test        # Molecule: converge + idempotência + verify
```

## Convenções

- **Tasks:** FQCN (`ansible.builtin.*`), nome em inglês e, quando aplicável,
  prefixo com o item do CIS: `CIS 5.1.20 | Disable root login`.
- **Variáveis:** prefixadas com o nome da role (`ssh_hardening_*`, `ufw_*`…).
  Valores compartilhados entre roles usam o prefixo global `hardening_*`.
- **Novo controle:** atualize também [`docs/CIS_MAPPING.md`](docs/CIS_MAPPING.md)
  e uma asserção em [`molecule/default/verify.yml`](molecule/default/verify.yml).
- **Mudança de comportamento ou trade-off:** registre um ADR em
  [`docs/DECISIONS.md`](docs/DECISIONS.md).
- **Modo `--check`:** toda task nova precisa funcionar em check mode sem falhar
  e sem reportar `changed` num host já conforme.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/pt-br/)
  (`feat:`, `fix:`, `docs:`, `test:`, `ci:`, `build:`).

## Dependências

- O Dependabot atualiza `requirements.txt` e as GitHub Actions (fixadas por SHA).
- **Não** cobre o [`requirements-fallback.yml`](requirements-fallback.yml) (coleções
  vindas do GitHub quando o Galaxy está fora): ao mudar versões em
  `requirements.yml`, atualize as tags dele também.

## Release

1. Mova o conteúdo de `## [Unreleased]` do `CHANGELOG.md` para `## [X.Y.Z] - AAAA-MM-DD`.
2. Após o merge na `main`: `git tag -a vX.Y.Z -m vX.Y.Z && git push origin vX.Y.Z`.
3. O workflow [`release.yml`](.github/workflows/release.yml) publica a GitHub
   Release com as notas dessa seção.

## Segurança

Não abra issue pública para vulnerabilidades: siga o [SECURITY.md](SECURITY.md).
