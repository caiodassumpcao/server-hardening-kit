# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e
versionamento [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]

## [1.0.0] - 2026-10-22

### Adicionado
- Roles `common`, `users`, `ssh_hardening`, `ufw`, `fail2ban`, `unattended_upgrades`,
  `sysctl_hardening`, `auditd` e `lynis`.
- Modo auditoria (`make check`) com `--check --diff` e relatório JUnit.
- Migração de porta SSH em duas fases com *lockout guard* e validação pós-deploy.
- Matriz CIS × Lynis × MITRE ATT&CK (`docs/CIS_MAPPING.md`), ADRs e modelo de ameaças.
- Testes: Molecule (Ubuntu 22.04/24.04), ansible-lint (perfil `production`),
  pytest do gerador de relatório e E2E com Lynis em VM real no GitHub Actions.
