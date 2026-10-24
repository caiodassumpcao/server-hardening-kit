# Lynis — comparação antes/depois

| Host | SO | Lynis | Score antes | Score depois | Δ | Warnings | Sugestões |
|---|---|---|:-:|:-:|:-:|:-:|:-:|
| `ubuntu-22.04` | Ubuntu 22.04 | 3.1.7 | **61** | **80** | +19 | 2 → 1 | 27 → 15 |
| `ubuntu-24.04` | Ubuntu 24.04 | 3.1.7 | **61** | **79** | +18 | 2 → 1 | 26 → 14 |

## `ubuntu-22.04`

Hardening index: **61 → 80** (+19)

### Warnings resolvidos (1)
- `FIRE-4512` — iptables module(s) loaded, but no rules active

### Sugestões resolvidas (14)
- `ACCT-9622` — Enable process accounting
- `ACCT-9626` — Enable sysstat to collect accounting (no results)
- `ACCT-9628` — Enable auditd to collect audit information
- `AUTH-9230` — Configure password hashing rounds in /etc/login.defs
- `AUTH-9262` — Install a PAM module for password strength testing like pam_cracklib or pam_passwdqc or libpam-passwdqc
- `AUTH-9286` — Configure minimum password age in /etc/login.defs
- `AUTH-9328` — Default umask in /etc/login.defs could be more strict like 027
- `BANN-7126` — Add a legal banner to /etc/issue, to warn unauthorized users
- `BANN-7130` — Add legal banner to /etc/issue.net, to warn unauthorized users
- `KRNL-5820` — If not required, consider explicit disabling of core dump in /etc/security/limits.conf file
- `NETW-3200` — Determine if protocol 'dccp' is really needed on this system
- `PKGS-7370` — Install debsums utility for the verification of packages with known good database.
- `PKGS-7394` — Install package apt-show-versions for patch management purposes
- `USB-1000` — Disable drivers like USB storage when not used, to prevent unauthorized storage or data theft

### Sugestões remanescentes (15)

Itens que o kit **não** aplica por decisão consciente (particionamento, senha de
GRUB, AIDE, `kernel.modules_disabled`, `MaxSessions 2`...) ficam aqui, com a
justificativa em [Fora de escopo](../CIS_MAPPING.md#fora-de-escopo-decisão-consciente).

- `AUTH-9229` — Check PAM configuration, add rounds if applicable and expire passwords to encrypt with new values
- `AUTH-9284` — Look at the locked accounts and consider removing them
- `BOOT-5122` — Set a password on GRUB boot loader to prevent altering boot configuration (e.g. boot in single user mode without password)
- `BOOT-5264` — Consider hardening system services
- `FILE-6310` — To decrease the impact of a full /home file system, place /home on a separate partition
- `FILE-7524` — Consider restricting file permissions
- `FINT-4350` — Install a file integrity tool to monitor changes to critical and sensitive files
- `FIRE-4513` — Check iptables rules to see which rules are currently not used
- `HRDN-7222` — Harden compilers like restricting access to root user only
- `HRDN-7230` — Harden the system by installing at least one malware scanner, to perform periodic file system scans
- `KRNL-6000` — One or more sysctl values differ from the scan profile and could be tweaked
- `LOGG-2154` — Enable logging to an external logging host for archiving purposes and additional protection
- `NAME-4404` — Add the IP name and FQDN to /etc/hosts for proper name resolving
- `PKGS-7392` — Update your system with apt-get update, apt-get upgrade, apt-get dist-upgrade and/or unattended-upgrades
- `SSH-7408` — Consider hardening SSH configuration

## `ubuntu-24.04`

Hardening index: **61 → 79** (+18)

### Warnings resolvidos (1)
- `FIRE-4512` — iptables module(s) loaded, but no rules active

### Sugestões resolvidas (14)
- `ACCT-9622` — Enable process accounting
- `ACCT-9626` — Enable sysstat to collect accounting (disabled)
- `ACCT-9628` — Enable auditd to collect audit information
- `AUTH-9230` — Configure password hashing rounds in /etc/login.defs
- `AUTH-9262` — Install a PAM module for password strength testing like pam_cracklib or pam_passwdqc or libpam-passwdqc
- `AUTH-9286` — Configure minimum password age in /etc/login.defs
- `AUTH-9328` — Default umask in /etc/login.defs could be more strict like 027
- `BANN-7126` — Add a legal banner to /etc/issue, to warn unauthorized users
- `BANN-7130` — Add legal banner to /etc/issue.net, to warn unauthorized users
- `KRNL-5820` — If not required, consider explicit disabling of core dump in /etc/security/limits.conf file
- `NETW-3200` — Determine if protocol 'dccp' is really needed on this system
- `PKGS-7370` — Install debsums utility for the verification of packages with known good database.
- `PKGS-7394` — Install package apt-show-versions for patch management purposes
- `USB-1000` — Disable drivers like USB storage when not used, to prevent unauthorized storage or data theft

### Sugestões remanescentes (14)

Itens que o kit **não** aplica por decisão consciente (particionamento, senha de
GRUB, AIDE, `kernel.modules_disabled`, `MaxSessions 2`...) ficam aqui, com a
justificativa em [Fora de escopo](../CIS_MAPPING.md#fora-de-escopo-decisão-consciente).

- `AUTH-9229` — Check PAM configuration, add rounds if applicable and expire passwords to encrypt with new values
- `AUTH-9284` — Look at the locked accounts and consider removing them
- `BOOT-5122` — Set a password on GRUB boot loader to prevent altering boot configuration (e.g. boot in single user mode without password)
- `BOOT-5264` — Consider hardening system services
- `FILE-6310` — To decrease the impact of a full /home file system, place /home on a separate partition
- `FILE-7524` — Consider restricting file permissions
- `FINT-4350` — Install a file integrity tool to monitor changes to critical and sensitive files
- `FIRE-4513` — Check iptables rules to see which rules are currently not used
- `HRDN-7230` — Harden the system by installing at least one malware scanner, to perform periodic file system scans
- `KRNL-6000` — One or more sysctl values differ from the scan profile and could be tweaked
- `LOGG-2154` — Enable logging to an external logging host for archiving purposes and additional protection
- `NAME-4404` — Add the IP name and FQDN to /etc/hosts for proper name resolving
- `PKGS-7392` — Update your system with apt-get update, apt-get upgrade, apt-get dist-upgrade and/or unattended-upgrades
- `SSH-7408` — Consider hardening SSH configuration
