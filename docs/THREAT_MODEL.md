# Modelo de ameaças

## Escopo

Servidor Ubuntu LTS (22.04/24.04) exposto à internet ou a uma rede corporativa,
administrado via SSH e gerenciado por Ansible. Exemplos: VPS de aplicação,
bastion host, nó de CI self-hosted.

**Fora do escopo:** segurança da aplicação hospedada, do hypervisor/provedor de
nuvem, da cadeia de build e da estação de trabalho do administrador.

## Ativos

| Ativo | Por que importa |
|---|---|
| Acesso root/sudo | Controle total do host |
| Chaves SSH (host e usuários) | Identidade do servidor e dos operadores |
| Trilha de auditoria | Capacidade de detectar e investigar incidentes |
| Dados e segredos da aplicação | Alvo final da maioria dos ataques |

## Adversários considerados

| Adversário | Capacidade | Exemplo |
|---|---|---|
| **Botnet / scanner oportunista** | Varredura em massa, credential stuffing, exploits públicos | Brute force de SSH na porta 22 minutos após a VM subir |
| **Atacante com credencial de baixo privilégio** | Shell como usuário comum (app comprometida, chave vazada) | Tenta escalar para root e se esconder |
| **Insider / operador descuidado** | Acesso legítimo | `sysctl -w`, NOPASSWD "temporário", chave pessoal esquecida |

## Ameaças → controles (STRIDE)

| STRIDE | Ameaça | Controles do kit | Risco residual |
|---|---|---|---|
| **S**poofing | Login com senha adivinhada/vazada | Só chave pública, `MaxAuthTries 3`, fail2ban + `ufw limit`, `AllowGroups` | Roubo da chave privada do operador |
| **S**poofing | Login direto como root | `PermitRootLogin no`, `su` restrito | — |
| **T**ampering | Alterar sudoers, contas, sshd_config | auditd (`scope`, `identity`, `sshd_config`), `authorized_keys` exclusivo, `make check` periódico | Root pode alterar arquivos; a trilha registra (imutável até reboot) |
| **T**ampering | MITM/downgrade de criptografia SSH | KEX/ciphers/MACs modernos, moduli ≥ 3072 bits | Primeiro contato (TOFU) sem SSHFP/CA |
| **R**epudiation | "Não fui eu que rodei esse comando" | `sudo` com `use_pty` + `logfile`, auditd `user_emulation`/`privileged` com `auid` | Logs locais podem ser perdidos com o host → enviar para SIEM (roadmap) |
| **I**nformation disclosure | Leitura de memória/credenciais | `ptrace_scope=1`, `suid_dumpable=0`, core dumps desligados, `kptr_restrict`, `dmesg_restrict` | Root lê qualquer coisa |
| **I**nformation disclosure | Serviços expostos sem necessidade | ufw default deny + allowlist explícita | Portas liberadas para a aplicação |
| **D**enial of service | Flood de conexões/SYN | `MaxStartups`, `LoginGraceTime`, SYN cookies, `ufw limit` | Ataques volumétricos (precisam de mitigação upstream) |
| **D**enial of service | Disco de auditoria cheio | `max_log_file`/`num_logs`, `space_left_action` | `single` derruba o serviço (decisão consciente — ADR-005) |
| **E**levation of privilege | Exploit de CVE conhecida | unattended-upgrades (security), ASLR, AppArmor, módulos de kernel raros desabilitados | Zero-days; janela até o próximo ciclo do apt |
| **E**levation of privilege | Abuso de sudo amplo | Sudo com senha para humanos, allowlist de comandos para contas de serviço, auditoria de NOPASSWD | Conta de automação é NOPASSWD (ADR-003) |
| **E**levation of privilege | Desligar a auditoria para agir sem rastro | Regras imutáveis (`-e 2`), `audit=1` no boot | Reboot reseta para as regras em disco (que também são auditadas) |

## Premissas

- O controller (máquina que roda o Ansible) e a chave da conta de automação são
  confiáveis e protegidos.
- O provedor de nuvem oferece console fora de banda para recuperação (ver
  *Recuperação de lockout* no README).
- Relógio sincronizado (systemd-timesyncd padrão do Ubuntu), essencial para
  correlacionar eventos de auditoria.
