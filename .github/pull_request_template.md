## O que muda

<!-- Resumo da mudança e motivação. Linke a issue, se houver (Closes #123). -->

## Tipo

- [ ] Novo controle de hardening
- [ ] Correção
- [ ] Testes / CI
- [ ] Documentação

## Checklist

- [ ] `make lint` passa (ansible-lint perfil `production`)
- [ ] `make test` passa (Molecule: check, converge, idempotência, verify)
- [ ] Funciona em `--check` sem falhar e sem `changed` num host já conforme
- [ ] Controle novo: `docs/CIS_MAPPING.md` e `molecule/default/verify.yml` atualizados
- [ ] Trade-off relevante: ADR em `docs/DECISIONS.md`
- [ ] `CHANGELOG.md` atualizado na seção `[Unreleased]`
