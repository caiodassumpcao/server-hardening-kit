# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e
versionamento [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]

## [1.1.0] - 2026-10-26

Destaques: E2E do fluxo SSH completo em VMs Ubuntu reais, Lynis **61 → 80**
(22.04) e **61 → 79** (24.04), role `password_policy` e segurança da cadeia de
suprimentos do repositório (Actions por SHA, gitleaks, OpenSSF Scorecard).

### Alterado
- README reorganizado como visão geral; passo a passo, receitas, recuperação de
  lockout e troubleshooting movidos para `docs/GUIA.md`. README em inglês com a
  mesma estrutura.
- Início rápido corrigido: comandos anteriores ao hardening usam `BOOTSTRAP=1`.
- `ansible-core` aceito até 2.21.x; Dependabot com `increase-if-necessary` e PRs agrupados.
- Coleções instaladas num único ponto (`scripts/galaxy-install.sh`, usado pelo
  `make install` e pelo CI): retentativa com espera crescente e, se o Ansible
  Galaxy seguir fora (HTTP 5xx), fallback para os repositórios oficiais no GitHub
  em versões fixas (`requirements-fallback.yml`). ansible-lint em modo `offline`
  e Molecule sem dependência própria do Galaxy; `community.docker` (driver do
  Molecule) passou a ser declarado.

### Adicionado
- E2E em **VM real** (LXD/KVM no runner do GitHub) cobrindo o fluxo completo do
  README por SSH: Lynis antes, `--check` em host de fábrica, bootstrap pela 22,
  steady state na 2222, idempotência, reboot, `--check` conforme, Lynis depois e
  testes negativos (root, senha, porta 22).
- Role `password_policy` (CIS 5.3/5.4): `pam_pwquality`, envelhecimento de senha,
  hash yescrypt e `umask 027`; validade aplicada também aos admins existentes.
- CIS 1.5.5: apport desativado (no boot ele reescrevia `fs.suid_dumpable=2`).
- `acct`, `sysstat` e verificação semanal do `debsums`; sysctls
  `dev.tty.ldisc_autoload=0` e `kernel.core_uses_pid=1`; `AllowTcpForwarding no` explícito.
- Molecule roda `--check` num host "de fábrica" antes do converge.
- `CONTRIBUTING.md`.
- Segurança da cadeia de suprimentos: Actions fixadas por SHA de commit,
  `persist-credentials: false` nos checkouts, varredura de segredos com gitleaks
  em todo o histórico e OpenSSF Scorecard (badge e Code scanning).
- Workflow de release: tag `vX.Y.Z` publica a GitHub Release com as notas do CHANGELOG.
- Templates de issue (bug e melhoria), de pull request e `CODEOWNERS`.

### Corrigido
- Dev Container: `ANSIBLE_CONFIG` explícito. Pastas do Windows montadas no
  container são *world-writable*, e o Ansible ignorava o `ansible.cfg`.
- `--check` falhava em host de fábrica (cache do apt vazio; `/etc/fail2ban` e
  `/etc/ssh` inexistentes antes da instalação).
- `--check` acusava drift falso num host conforme ao simular a remoção de regra
  ufw já inexistente.
- Falhas intermitentes de `apt` na 1ª execução: o `apt-daily` disparado ao ativar
  os timers segurava o lock. `unattended_upgrades` passou a ser a última role e a
  `common` espera jobs do apt em andamento.

## [1.0.0] - 2026-10-22

### Adicionado
- Roles `common`, `users`, `ssh_hardening`, `ufw`, `fail2ban`, `unattended_upgrades`,
  `sysctl_hardening`, `auditd` e `lynis`.
- Modo auditoria (`make check`) com `--check --diff` e relatório JUnit.
- Migração de porta SSH em duas fases com *lockout guard* e validação pós-deploy.
- Matriz CIS × Lynis × MITRE ATT&CK (`docs/CIS_MAPPING.md`), ADRs e modelo de ameaças.
- Testes: Molecule (Ubuntu 22.04/24.04), ansible-lint (perfil `production`),
  pytest do gerador de relatório e E2E com Lynis em VM real no GitHub Actions.
