# Registro de decisões de arquitetura (ADRs)

Hardening é feito de trade-offs entre segurança, disponibilidade e
operabilidade. Este arquivo registra **por que** o kit faz o que faz.

---

## ADR-001 — Drop-in `00-hardening.conf` em vez de substituir o `sshd_config`

**Contexto.** O `sshd` usa o **primeiro** valor encontrado para cada diretiva. O
Ubuntu inclui `/etc/ssh/sshd_config.d/*.conf` no topo do arquivo principal, e
imagens de nuvem trazem drop-ins como `50-cloud-init.conf`, que costumam
**reativar** `PasswordAuthentication yes`.

**Decisão.** Gerenciar só `/etc/ssh/sshd_config.d/00-hardening.conf`. O prefixo
`00-` garante precedência sobre o arquivo principal e sobre os drop-ins de terceiros.

**Consequências.** O `sshd_config` do pacote continua intocado, então upgrades
do OpenSSH não geram conflito de conffile. A validação é feita em duas camadas:
`sshd -t -f` no drop-in isolado, durante o `template`, e `sshd -t` na
configuração completa antes do restart. O teste do Molecule confere o resultado
**efetivo** com `sshd -T`, e não o conteúdo do arquivo.

---

## ADR-002 — Desativar o socket activation do SSH

**Contexto.** A partir do 22.10 o Ubuntu sobe o SSH via `ssh.socket`. No 24.04
a porta passa a ser derivada do `sshd_config` por um *generator* do systemd, e
trocar `Port` exige `daemon-reload` + `restart ssh.socket`. No 22.04 o modelo
ainda é o `ssh.service` tradicional.

**Decisão.** Desabilitar `ssh.socket` e usar `ssh.service` nas duas versões,
seguindo o procedimento documentado no Ubuntu Server Guide.

**Consequências.** Um único caminho de código e de handler. O `ssh.service` é
iniciado **imediatamente** após parar o socket, para que nunca exista uma janela
sem processo escutando enquanto o Ansible está conectado.

---

## ADR-003 — Conta de automação com `NOPASSWD` (exceção ao CIS 5.2.4)

**Contexto.** O CIS 5.2.4 exige senha para escalar privilégio. O Ansible
precisa de `become` não interativo para ser reexecutável (drift, CI, cron).

**Alternativas consideradas.**
1. `--ask-become-pass` em toda execução: inviável em pipelines.
2. Senha do become no Vault: a senha passa a existir em mais um lugar e pode
   vazar em logs/CI.
3. **Conta dedicada, apenas chave, sem senha, `NOPASSWD`, opcionalmente
   restrita por origem (`from=` no authorized_keys).**

**Decisão.** Opção 3. Humanos (`users_admins`) continuam com sudo **com senha**.

**Consequências.** A chave da automação vira credencial de alto valor: deve
ficar em cofre/agente, ser restrita com `users_automation.allowed_from` e ser
rotacionada. A exceção fica visível no arquivo `20-hardening-automation` e no
relatório de auditoria de sudoers.

---

## ADR-004 — Migração de porta SSH em duas fases (sem lockout)

**Contexto.** Trocar a porta do SSH na mesma execução em que o firewall é ativado
é a forma clássica de se trancar fora de um servidor.

**Decisão.**
1. O `ufw` roda **antes** do `ssh_hardening` e libera tanto a porta nova quanto a
   **porta da conexão atual** (`ansible_port`).
2. Antes de desligar senha/root, um *lockout guard* garante que existe ao menos
   um membro de `AllowGroups` com `authorized_keys` não vazio.
3. Após os handlers, o playbook abre, **a partir do controller**, uma sessão SSH
   nova na porta nova com a conta de automação. Se ela falhar, a execução falha
   enquanto a sessão antiga ainda está aberta.
4. Portas antigas (`ufw_ssh_legacy_ports`) só são removidas do firewall quando a
   conexão atual **já não passa por elas**, ou seja, na segunda execução
   (*steady state*).

**Consequências.** O bootstrap deixa a porta 22 aberta até a próxima execução.
Isso é intencional: é a rota de retorno caso a porta nova esteja bloqueada pelo
firewall do provedor de nuvem.

---

## ADR-005 — auditd imutável e ações de falha do CIS

**Contexto.** O CIS 6.2.3.20 pede `-e 2` (regras imutáveis até o reboot) e o
6.2.2.3/6.2.2.4 pede `single`/`halt` quando o disco de auditoria enche.

**Decisão.** Os defaults seguem o CIS: `-e 2`, `admin_space_left_action = single`
e `disk_full_action = single`.

**Consequências.**
- Alterar regras de auditoria exige reboot. O handler detecta o modo imutável e
  marca `/run/reboot-required` em vez de falhar.
- Se o disco de logs encher, o host entra em modo monousuário. Isso prioriza a
  integridade da trilha de auditoria sobre a disponibilidade. Em serviços sem
  redundância, avalie `auditd_conf.admin_space_left_action: suspend` e
  monitore o espaço em disco.
- O `auditd.service` tem `RefuseManualStop=yes`, então mudanças no `auditd.conf`
  são aplicadas com `SIGHUP` e não com `systemctl restart`.

---

## ADR-006 — Quem manda nos parâmetros de kernel

**Contexto.** O ufw aplica `/etc/ufw/sysctl.conf` ao iniciar, e esse arquivo
define `log_martians=0`, desfazendo o CIS 3.3.9 após cada boot. Além disso,
arquivos em `/etc/sysctl.d` são aplicados em ordem lexical, e o
`99-sysctl.conf` (→ `/etc/sysctl.conf`) pode sobrescrever valores.

**Decisão.**
- `IPT_SYSCTL=/etc/sysctl.conf` em `/etc/default/ufw`, para que o ufw não reaplique os
  seus próprios valores.
- O arquivo do kit é `99-zz-hardening.conf`, o último na ordem.
- Aplicação via `systemctl restart systemd-sysctl`, que entende o prefixo `-`
  (chave opcional) e não falha em kernels sem `unprivileged_bpf_disabled`.
- Uma task compara o valor **em runtime** com o esperado. Em `--check`, isso
  expõe drift causado por `sysctl -w` manual.

---

## ADR-007 — Regras de auditoria como dados

**Contexto.** As regras do CIS listam syscalls como `open`, `creat` e `chmod`,
que **não existem** em aarch64. Uma regra inválida faz o `augenrules` falhar.

**Decisão.** As regras ficam como dados em `roles/auditd/defaults/main.yml`. O
template cruza cada lista de syscalls com a tabela real da arquitetura
(`ausyscall --dump`) e omite caminhos inexistentes. Os binários setuid/setgid do
CIS 6.2.3.6 são descobertos no próprio host.

**Consequências.** O mesmo inventário funciona em x86_64 e ARM (Graviton/Ampere).
Para adicionar uma regra, basta acrescentar um item à lista, sem editar template.

---

## ADR-008 — Atualizações automáticas só de segurança, sem reboot automático

**Decisão.** `Allowed-Origins` contém apenas `-security` e ESM, e `#clear`
descarta as origens herdadas do `50unattended-upgrades`. `Automatic-Reboot` é `false`.

**Consequências.** Patches críticos chegam em até 24h sem intervenção. Reboots
continuam sendo uma decisão operacional: o `motd` e o próprio playbook avisam
quando há reboot pendente. Em frotas atrás de load balancer, ative
`unattended_upgrades_automatic_reboot`.

**Ordem de execução.** A role roda **por último**. Ao ativar os timers, o
`apt-daily` dispara na hora e segura `/var/cache/apt/archives/lock`, que o
`lock_timeout` do apt não cobre. Se rodasse antes, as instalações das roles
seguintes falhariam de forma intermitente; o E2E em VM real pegou exatamente
esse caso. Pelo mesmo motivo, a role `common` espera jobs do apt em andamento
antes de instalar qualquer pacote.

---

## ADR-009 — Testes em três camadas

| Camada | Ferramenta | Pergunta que responde | Onde roda |
|---|---|---|---|
| Estática | yamllint, ansible-lint (perfil `production`) | O código segue boas práticas? | todo push/PR |
| Integração | Molecule + Docker (22.04 e 24.04) | O playbook converge, é idempotente e o **estado efetivo** está correto? | todo push/PR |
| Ponta a ponta | GitHub Actions em VM real + Lynis | O score de segurança **realmente** sobe numa VM com kernel, systemd e auditd reais? | push na `main`, semanal |

Containers não têm auditd, GRUB nem netfilter próprio. Por isso essas partes são
verificadas no nível de arquivo no Molecule e no nível de comportamento no E2E.
