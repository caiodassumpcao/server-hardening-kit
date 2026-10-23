# Matriz de controles: CIS Benchmark × Lynis × MITRE ATT&CK

Cada controle aplicado pelo kit, com **onde** ele é implementado, **qual item do CIS**
ele atende, **qual teste do Lynis** ele influencia, **qual técnica do ATT&CK** ele
mitiga ou detecta, e **como verificar** manualmente no servidor.

> **Referência:** *CIS Ubuntu Linux 24.04 LTS Benchmark v1.0.0* (para 22.04 a
> numeração das seções 5 e 6 difere ligeiramente). O PDF é gratuito em
> [cisecurity.org](https://www.cisecurity.org/benchmark/ubuntu_linux) mediante
> cadastro. A numeração muda entre versões do benchmark: sempre confira o ID
> contra a versão que sua auditoria usa.
>
> **Legenda (tipo):** 🛡️ prevenção · 🔎 detecção · ♻️ correção/manutenção

## 1. Acesso remoto — `roles/ssh_hardening`

| Controle | CIS | Lynis | ATT&CK | Tipo | Verificação |
|---|---|---|---|---|---|
| Somente chave pública (`PasswordAuthentication no`, `AuthenticationMethods publickey`, `KbdInteractiveAuthentication no`) | 5.1.x | SSH-7408 | T1110 Brute Force | 🛡️ | `sshd -T \| grep -E 'passwordauth\|kbdinteractive'` |
| Login de root desabilitado (`PermitRootLogin no`) | 5.1.20 | SSH-7408 | T1078.003 Local Accounts | 🛡️ | `sshd -T \| grep permitrootlogin` |
| Porta configurável (padrão 2222) | — | SSH-7408 | T1046 Network Service Discovery (só reduz ruído) | 🛡️ | `ss -tlnp \| grep sshd` |
| Acesso restrito por grupo (`AllowGroups sshusers`) | 5.1.4 | SSH-7408 | T1078 Valid Accounts | 🛡️ | `sshd -T \| grep allowgroups` |
| Banner legal (`Banner /etc/issue.net`) | 5.1.5 | BANN-7130 | — | 🛡️ | `cat /etc/issue.net` |
| Ciphers fortes (AEAD/CTR) | 5.1.6 | SSH-7408 | T1557 Adversary-in-the-Middle | 🛡️ | `sshd -T \| grep ^ciphers` |
| `ClientAliveInterval 300` / `ClientAliveCountMax 2` | 5.1.7 | SSH-7408 | T1563 Remote Service Session Hijacking | 🛡️ | `sshd -T \| grep clientalive` |
| `DisableForwarding yes` (X11, agent, TCP) | 5.1.8 | SSH-7408 | T1572 Protocol Tunneling · T1090 Proxy | 🛡️ | `sshd -T \| grep disableforwarding` |
| `GSSAPIAuthentication no` | 5.1.9 | — | — | 🛡️ | `sshd -T \| grep gssapi` |
| `HostbasedAuthentication no` | 5.1.10 | — | T1078 | 🛡️ | `sshd -T \| grep hostbased` |
| `IgnoreRhosts yes` | 5.1.11 | — | T1078 | 🛡️ | `sshd -T \| grep ignorerhosts` |
| KEX moderno (incl. pós-quântico híbrido `sntrup761x25519`) | 5.1.12 | SSH-7408 | T1557 | 🛡️ | `sshd -T \| grep kexalgorithms` |
| `LoginGraceTime 60` | 5.1.13 | SSH-7408 | T1499 Endpoint DoS | 🛡️ | `sshd -T \| grep logingracetime` |
| `LogLevel VERBOSE` (registra fingerprint da chave) | 5.1.14 | SSH-7408 | — (suporta investigação) | 🔎 | `sshd -T \| grep loglevel` |
| MACs apenas *encrypt-then-MAC* | 5.1.15 | SSH-7408 | T1557 | 🛡️ | `sshd -T \| grep ^macs` |
| `MaxAuthTries 3` | 5.1.16 | SSH-7408 | T1110 | 🛡️ | `sshd -T \| grep maxauthtries` |
| `MaxSessions 4` | 5.1.17 | SSH-7408 | — | 🛡️ | `sshd -T \| grep maxsessions` |
| `MaxStartups 10:30:60` | 5.1.18 | — | T1499 | 🛡️ | `sshd -T \| grep maxstartups` |
| `PermitEmptyPasswords no` | 5.1.19 | — | T1078 | 🛡️ | `sshd -T \| grep permitempty` |
| `PermitUserEnvironment no` | 5.1.21 | SSH-7408 | T1574 Hijack Execution Flow | 🛡️ | `sshd -T \| grep permituserenv` |
| `UsePAM yes` | 5.1.22 | — | — | 🛡️ | `sshd -T \| grep usepam` |
| `sshd_config` 0600 root:root | 5.1.1 | — | T1222.002 | 🛡️ | `stat -c '%a %U' /etc/ssh/sshd_config` |
| Chaves de host privadas 0600 / públicas 0644 | 5.1.2 / 5.1.3 | — | T1552.004 Private Keys | 🛡️ | `ls -l /etc/ssh/ssh_host_*` |
| Remoção de módulos DH < 3071 bits em `/etc/ssh/moduli` | — (ssh-audit) | — | T1557 | 🛡️ | `awk '$5 < 3071' /etc/ssh/moduli \| wc -l` → 0 |

## 2. Firewall — `roles/ufw`

| Controle | CIS | Lynis | ATT&CK | Tipo | Verificação |
|---|---|---|---|---|---|
| ufw instalado | 4.1.1 | FIRE-4590 | — | 🛡️ | `dpkg -l ufw` |
| `iptables-persistent` ausente | 4.1.2 | — | — | 🛡️ | `dpkg -l iptables-persistent` |
| Serviço ufw habilitado e ativo | 4.1.3 | FIRE-4590 | T1562.004 Disable or Modify System Firewall | 🛡️ | `ufw status verbose` |
| Loopback permitido; 127.0.0.0/8 e ::1 bloqueados nas demais interfaces | 4.1.4 | — | T1090 (spoofing) | 🛡️ | `ufw status numbered` |
| Saída configurada (padrão `allow`, ajustável) | 4.1.5 | — | T1041 Exfiltration over C2 (se `deny`) | 🛡️ | `ufw status verbose` |
| Regra explícita para cada porta aberta | 4.1.6 | — | T1190 Exploit Public-Facing Application | 🛡️ | `ss -tlnp` × `ufw status` |
| Política padrão de entrada `deny` | 4.1.7 | FIRE-4590 | T1046 · T1190 | 🛡️ | `grep DEFAULT_INPUT /etc/default/ufw` |
| Rate limit nativo no SSH (`ufw limit`) | — | — | T1110 | 🛡️ | `ufw status \| grep LIMIT` |
| `IPT_SYSCTL=/etc/sysctl.conf` (ufw não sobrescreve CIS 3.3.9) | 3.3.9 (indireto) | KRNL-6000 | — | 🛡️ | `sysctl net.ipv4.conf.all.log_martians` → 1 |

## 3. Proteção contra brute force — `roles/fail2ban`

| Controle | CIS | Lynis | ATT&CK | Tipo | Verificação |
|---|---|---|---|---|---|
| Jail `sshd` (modo aggressive, journald) banindo via ufw | — (defesa em profundidade; complementa 5.1.16) | DEB-0880 | T1110.001 Password Guessing · T1110.003 Password Spraying | 🛡️🔎 | `fail2ban-client status sshd` |
| Banimento progressivo (`bantime.increment`) | — | — | T1110 | 🛡️ | `fail2ban-client get sshd bantime` |
| Jail `recidive` (1 semana, todas as portas) | — | — | T1110 · T1595 Active Scanning | 🛡️ | `fail2ban-client status recidive` |

## 4. Atualizações — `roles/unattended_upgrades`

| Controle | CIS | Lynis | ATT&CK | Tipo | Verificação |
|---|---|---|---|---|---|
| Patches de segurança automáticos (`-security`, ESM) | 1.2.2.1 | PKGS-7420 | T1190 · T1068 Exploitation for Privilege Escalation · T1203 | ♻️ | `apt-config dump \| grep Allowed-Origins` |
| Remoção de kernels/dependências não usados | — | — | — | ♻️ | `apt-config dump \| grep Remove-Unused` |
| Política de reboot explícita (padrão: não reiniciar sozinho) | — | — | — | ♻️ | `apt-config dump \| grep Automatic-Reboot` |

## 5. Auditoria — `roles/auditd`

| Controle | CIS | Lynis | ATT&CK | Tipo | Verificação |
|---|---|---|---|---|---|
| auditd instalado, habilitado e ativo | 6.2.1.1 / 6.2.1.2 | ACCT-9628 | T1562.012 Disable or Modify Linux Audit System | 🔎 | `systemctl is-active auditd` |
| `audit=1` no kernel (processos anteriores ao auditd) | 6.2.1.3 | — | T1562.012 | 🔎 | `grep -o 'audit=1' /proc/cmdline` |
| `audit_backlog_limit=8192` | 6.2.1.4 | — | — | 🔎 | `grep -o 'audit_backlog_limit=[0-9]*' /proc/cmdline` |
| Retenção: `max_log_file`, `keep_logs`, ações de disco cheio | 6.2.2.1–6.2.2.4 | — | T1070.002 Clear Linux Logs | 🔎 | `grep -E 'max_log\|space_left\|disk_' /etc/audit/auditd.conf` |
| Alterações em sudoers (`scope`) | 6.2.3.1 | ACCT-9630 | T1548.003 Sudo and Sudo Caching | 🔎 | `ausearch -k scope` |
| Execução como outro usuário (`user_emulation`) | 6.2.3.2 | ACCT-9630 | T1548.003 | 🔎 | `ausearch -k user_emulation` |
| Log do sudo (`sudo_log_file`) | 6.2.3.3 | — | T1070 Indicator Removal | 🔎 | `ausearch -k sudo_log_file` |
| Alteração de data/hora (`time-change`) | 6.2.3.4 | — | T1070.006 Timestomp | 🔎 | `ausearch -k time-change` |
| Hostname/rede (`system-locale`) | 6.2.3.5 | — | T1565 Data Manipulation | 🔎 | `ausearch -k system-locale` |
| Execução de binários setuid/setgid (`privileged`, gerado dinamicamente) | 6.2.3.6 | — | T1548.001 Setuid and Setgid | 🔎 | `ausearch -k privileged` |
| Acesso negado a arquivos (`access`) | 6.2.3.7 | — | T1083 File and Directory Discovery | 🔎 | `ausearch -k access` |
| Usuários e grupos (`identity`) | 6.2.3.8 | — | T1136 Create Account · T1098 Account Manipulation | 🔎 | `ausearch -k identity` |
| Permissões/donos/xattrs (`perm_mod`) | 6.2.3.9 | — | T1222.002 Linux File Permissions Modification | 🔎 | `ausearch -k perm_mod` |
| Montagens (`mounts`) | 6.2.3.10 | — | T1052 Exfiltration over Physical Medium | 🔎 | `ausearch -k mounts` |
| Sessões e logins (`session`, `logins`) | 6.2.3.11 / 6.2.3.12 | — | T1078 | 🔎 | `ausearch -k logins` |
| Remoção/renomeação de arquivos (`delete`) | 6.2.3.13 | — | T1070.004 File Deletion | 🔎 | `ausearch -k delete` |
| Política AppArmor (`MAC-policy`) | 6.2.3.14 | — | T1562.001 Disable or Modify Tools | 🔎 | `ausearch -k MAC-policy` |
| `chcon`, `setfacl`, `chacl`, `usermod` | 6.2.3.15–6.2.3.18 | — | T1222.002 · T1098 | 🔎 | `ausearch -k perm_chng` |
| Módulos de kernel (`kernel_modules`) | 6.2.3.19 | — | T1547.006 Kernel Modules and Extensions | 🔎 | `ausearch -k kernel_modules` |
| Regras imutáveis (`-e 2`) | 6.2.3.20 | — | T1562.012 | 🛡️🔎 | `auditctl -s \| grep enabled` → 2 |
| Mudanças no `sshd_config` (extra) | — | — | T1098.004 SSH Authorized Keys / T1556 | 🔎 | `ausearch -k sshd_config` |

## 6. Kernel e rede — `roles/sysctl_hardening`

| Controle | CIS | Lynis | ATT&CK | Tipo | Verificação |
|---|---|---|---|---|---|
| ASLR completo (`kernel.randomize_va_space=2`) | 1.5.1 | KRNL-6000 | T1203 Exploitation for Client Execution | 🛡️ | `sysctl kernel.randomize_va_space` |
| `kernel.yama.ptrace_scope=1` | 1.5.2 | KRNL-6000 | T1055.008 Ptrace System Calls | 🛡️ | `sysctl kernel.yama.ptrace_scope` |
| Core dumps restritos (`fs.suid_dumpable=0` + limits + coredump.conf) | 1.5.3 | KRNL-5820 | T1003.007 Proc Filesystem (credenciais em memória) | 🛡️ | `sysctl fs.suid_dumpable` |
| `dmesg_restrict`, `kptr_restrict=2`, `sysrq=0`, BPF restrito | — | KRNL-6000 | T1082 System Information Discovery · T1068 | 🛡️ | `sysctl -a \| grep -E 'dmesg\|kptr\|bpf'` |
| `fs.protected_*` (hard/symlinks, fifos, regular) | — | KRNL-6000 | T1574 Hijack Execution Flow | 🛡️ | `sysctl -a \| grep fs.protected` |
| IP forwarding desligado (v4/v6) | 3.3.1 | KRNL-6000 | T1090 Proxy · T1599 Network Boundary Bridging | 🛡️ | `sysctl net.ipv4.ip_forward` |
| Não enviar redirects | 3.3.2 | KRNL-6000 | T1557 | 🛡️ | `sysctl net.ipv4.conf.all.send_redirects` |
| Ignorar ICMP bogus/broadcast | 3.3.3 / 3.3.4 | KRNL-6000 | T1498 Network DoS | 🛡️ | `sysctl net.ipv4.icmp_echo_ignore_broadcasts` |
| Não aceitar ICMP redirects (inclusive "secure") | 3.3.5 / 3.3.6 | KRNL-6000 | T1557 | 🛡️ | `sysctl net.ipv4.conf.all.accept_redirects` |
| Reverse path filtering | 3.3.7 | KRNL-6000 | T1498 (IP spoofing) | 🛡️ | `sysctl net.ipv4.conf.all.rp_filter` |
| Não aceitar source routing | 3.3.8 | KRNL-6000 | T1557 | 🛡️ | `sysctl net.ipv4.conf.all.accept_source_route` |
| Logar pacotes marcianos | 3.3.9 | KRNL-6000 | — | 🔎 | `sysctl net.ipv4.conf.all.log_martians` |
| SYN cookies | 3.3.10 | KRNL-6000 | T1499.002 Service Exhaustion Flood | 🛡️ | `sysctl net.ipv4.tcp_syncookies` |
| Não aceitar IPv6 router advertisements | 3.3.11 | KRNL-6000 | T1557.002 (rogue RA) | 🛡️ | `sysctl net.ipv6.conf.all.accept_ra` |
| Detecção de drift em runtime (valor ≠ arquivo) | — | — | T1562 Impair Defenses | 🔎♻️ | `make check` |

## 7. Usuários e privilégios — `roles/users`

| Controle | CIS | Lynis | ATT&CK | Tipo | Verificação |
|---|---|---|---|---|---|
| sudo instalado | 5.2.1 | — | — | 🛡️ | `dpkg -l sudo` |
| `Defaults use_pty` | 5.2.2 | — | T1548.003 | 🛡️ | `sudo -V \| grep -i pty` |
| `Defaults logfile=/var/log/sudo.log` | 5.2.3 | — | — | 🔎 | `ls -l /var/log/sudo.log` |
| Admins precisam de senha no sudo | 5.2.4 | — | T1548.003 | 🛡️ | `sudo -l -U <admin>` |
| Auditoria de `NOPASSWD` / `!authenticate` não gerenciados | 5.2.4 / 5.2.5 | — | T1548.003 | 🔎 | saída da task *Report unmanaged passwordless sudo rules* |
| `timestamp_timeout=15` | 5.2.6 | — | T1548.003 | 🛡️ | `sudo -V \| grep timeout` |
| `su` restrito a grupo vazio (`pam_wheel`) | 5.2.7 | — | T1548 | 🛡️ | `grep pam_wheel /etc/pam.d/su` |
| **Sudo restrito**: allowlist de comandos por conta de serviço | — | — | T1548.003 · T1078 | 🛡️ | `sudo -l -U deployer` |
| `authorized_keys` exclusivo (chaves não declaradas são removidas) | — | — | T1098.004 SSH Authorized Keys | 🛡️♻️ | `make check` (diff) |
| Chave de automação restrita por origem (`from="..."`) | — | — | T1078 · T1021.004 | 🛡️ | `cat ~ansible/.ssh/authorized_keys` |
| Remoção de contas desativadas | — | — | T1078 | ♻️ | `getent passwd <user>` |

## 8. Baseline do sistema — `roles/common`

| Controle | CIS | Lynis | ATT&CK | Tipo | Verificação |
|---|---|---|---|---|---|
| Filesystems raros desabilitados (cramfs, hfs, jffs2...) | 1.1.1.x | — | T1068 (superfície do kernel) | 🛡️ | `modprobe -n -v cramfs` → `install /bin/false` |
| `usb-storage` desabilitado | 1.1.1.x | USB-1000 | T1052.001 Exfiltration over USB · T1091 | 🛡️ | `modprobe -n -v usb-storage` |
| Protocolos raros desabilitados (dccp, sctp, rds, tipc) | 3.2.x | NETW-3200 | T1068 | 🛡️ | `modprobe -n -v dccp` |
| AppArmor ativo | 1.3.1.x | MACF-6208 | T1068 (contenção) | 🛡️ | `aa-status` |
| apport desativado e mascarado (no boot ele reescrevia `fs.suid_dumpable=2`) | 1.5.5 | — | T1003.007 Proc Filesystem | 🛡️ | `systemctl is-enabled apport` → `masked` |
| Banner de login local | 1.6.x | BANN-7126 | — | 🛡️ | `cat /etc/issue` |
| Clientes legados removidos (telnet, rsh, nis, talk, ftp) | 2.2.x | — | T1040 Network Sniffing (protocolos em texto claro) | 🛡️ | `dpkg -l telnet rsh-client` |
| `debsums`, `apt-show-versions`, `libpam-tmpdir` | — | PKGS-7370 · PKGS-7394 · DEB-0280 | T1036 (integridade de pacotes) | 🔎 | `dpkg -l debsums` |

## Fora de escopo (decisão consciente)

Itens do CIS que o kit **não** aplica por terem alto risco de quebrar ambientes
genéricos, ou por dependerem de decisões de infraestrutura:

| Item | CIS | Por quê |
|---|---|---|
| Partições separadas (`/tmp`, `/var`, `/var/log/audit` com `nodev,nosuid,noexec`) | 1.1.2.x | Definido no provisionamento (imagem/Terraform), não depois. |
| Senha do GRUB | 1.4.1 | Em VM de nuvem o console é do provedor; a senha quebra reboot não assistido. |
| AIDE (integridade de arquivos) | 6.3.x | Útil, mas gera ruído sem um processo de revisão; previsto no roadmap. |
| Complexidade de senha / `pam_faillock` | 5.3.x | O kit elimina login por senha no SSH; regras de PAM ficam para ambientes com login local. |
| Envio de logs para servidor remoto | 6.1.x | Depende do SIEM da organização (roadmap: role de journald/rsyslog remoto). |
