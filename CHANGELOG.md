# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e
versionamento [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Alterado
- README reorganizado como visão geral; passo a passo, receitas, recuperação de
  lockout e troubleshooting movidos para `docs/GUIA.md`. README em inglês com a
  mesma estrutura.
- Início rápido corrigido: comandos anteriores ao hardening usam `BOOTSTRAP=1`.
- `ansible-core` aceito até 2.21.x; Dependabot com `increase-if-necessary` e PRs agrupados.

### Adicionado
- `CONTRIBUTING.md`.

### Corrigido
- Dev Container: `ANSIBLE_CONFIG` explícito. Pastas do Windows montadas no
  container são *world-writable*, e o Ansible ignorava o `ansible.cfg`.

## [1.0.0] - 2026-10-22

### Adicionado
- Roles `common`, `users`, `ssh_hardening`, `ufw`, `fail2ban`, `unattended_upgrades`,
  `sysctl_hardening`, `auditd` e `lynis`.
- Modo auditoria (`make check`) com `--check --diff` e relatório JUnit.
- Migração de porta SSH em duas fases com *lockout guard* e validação pós-deploy.
- Matriz CIS × Lynis × MITRE ATT&CK (`docs/CIS_MAPPING.md`), ADRs e modelo de ameaças.
- Testes: Molecule (Ubuntu 22.04/24.04), ansible-lint (perfil `production`),
  pytest do gerador de relatório e E2E com Lynis em VM real no GitHub Actions.
