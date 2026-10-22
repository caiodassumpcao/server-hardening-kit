<div align="center">

# 🛡️ server-hardening-kit

**Automated, measurable hardening of Ubuntu servers with Ansible, mapped to the CIS Benchmark.**

[![CI](https://github.com/caiodassumpcao/server-hardening-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/caiodassumpcao/server-hardening-kit/actions/workflows/ci.yml)
[![E2E Lynis](https://github.com/caiodassumpcao/server-hardening-kit/actions/workflows/e2e-lynis.yml/badge.svg)](https://github.com/caiodassumpcao/server-hardening-kit/actions/workflows/e2e-lynis.yml)
![Ubuntu](https://img.shields.io/badge/Ubuntu-22.04%20%7C%2024.04-E95420?logo=ubuntu&logoColor=white)
![Ansible](https://img.shields.io/badge/ansible--core-2.17%2B-EE0000?logo=ansible&logoColor=white)
![ansible-lint](https://img.shields.io/badge/ansible--lint-production-success)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[🇧🇷 Português](README.md) | **🇺🇸 English**

</div>

The kit takes a stock Ubuntu install to a **verifiable** security baseline,
with three guarantees:

1. **It measures before and after.** Lynis audits the server before and after
   hardening, and the score is published in the README.
2. **It reports drift without changing anything.** In audit mode (`--check`)
   every non-compliant control shows up as a failure in a JUnit report.
3. **It won't lock you out.** The SSH port change runs in two phases, with a
   *lockout guard* and access validation from the controller.

---

## 🎯 In 30 seconds

| | |
|---|---|
| **Problem** | A fresh Ubuntu install accepts password logins and has no firewall or auditing. Hardening it by hand is slow, error-prone and hard to prove. |
| **Solution** | One command (`make harden`) applies **CIS Benchmark** controls to one or many servers, idempotently, and **Lynis** measures the security gain before/after. |
| **Stack** | Ansible · Ubuntu 22.04/24.04 · Molecule + Docker · GitHub Actions · Python (pytest) · Lynis · UFW · fail2ban · auditd · AppArmor |
| **Quality** | ansible-lint `production` profile with 0 failures · Molecule passing on Ubuntu 22.04 and 24.04 (converge, idempotence and verify) · pytest · E2E with Lynis on a real VM in CI |

**What this project demonstrates**

- **Infrastructure as code:** 9 reusable Ansible roles, configurable through variables, with secrets in Ansible Vault.
- **Applied security:** every control traces back to its CIS item, its Lynis test and the MITRE ATT&CK technique it mitigates ([matrix](docs/CIS_MAPPING.md), [threat model](docs/THREAT_MODEL.md)).
- **Safe changes in production:** an audit mode that only reports, and a two-phase SSH port migration that never locks the operator out.
- **Infrastructure testing:** a full test pyramid (lint → unit → integration in containers → E2E on a VM) running on GitHub Actions.
- **Documented decisions:** every trade-off recorded as an ADR ([DECISIONS.md](docs/DECISIONS.md)).

## 🚀 Quick start

```bash
git clone https://github.com/caiodassumpcao/server-hardening-kit.git && cd server-hardening-kit
make install                 # virtualenv + Ansible + collections
make lab-init                # creates your inventory from the example
make check                   # audit only: shows what is out of compliance
make bootstrap && make harden # applies the hardening
make test                    # (optional) runs the Molecule tests locally
```

## ✅ What gets applied

| Role | What it does |
|---|---|
| [`common`](roles/common) | Validates the OS, waits for cloud-init, removes legacy clients (telnet/rsh/nis), disables rare kernel modules and USB storage, restricts core dumps, enables AppArmor and a login banner |
| [`users`](roles/users) | Admins with **password-protected** sudo, key-only automation account, **restricted sudo** via command allowlist, `su` blocked, exclusive `authorized_keys`, NOPASSWD audit |
| [`ufw`](roles/ufw) | Default deny, loopback anti-spoofing, SSH rate limiting, port change without lockout |
| [`ssh_hardening`](roles/ssh_hardening) | Keys only, no root, configurable port, `AllowGroups`, modern crypto (including hybrid post-quantum KEX), moduli ≥ 3072 bits |
| [`fail2ban`](roles/fail2ban) | `sshd` jail (aggressive, journald) with progressive bans + `recidive` jail, banning through ufw |
| [`unattended_upgrades`](roles/unattended_upgrades) | Automatic **security** patches, explicit reboot policy |
| [`sysctl_hardening`](roles/sysctl_hardening) | ASLR, ptrace, kptr/dmesg, BPF, redirects, rp_filter, SYN cookies… with **runtime drift detection** |
| [`auditd`](roles/auditd) | All CIS 6.2.3 rules generated from data (multi-arch), host-discovered setuid binaries, immutable rules, `audit=1` at boot |
| [`lynis`](roles/lynis) | Installs Lynis from the signed official repository, runs the audit and fetches the report |

## 📚 Full documentation

The complete guide is in Portuguese in [README.md](README.md). It covers the
step-by-step walkthrough from clone to hardened server, variables, testing, the
lockout recovery guide and troubleshooting. Supporting docs:

- [`docs/CIS_MAPPING.md`](docs/CIS_MAPPING.md): control × CIS × Lynis × MITRE ATT&CK matrix
- [`docs/DECISIONS.md`](docs/DECISIONS.md): architecture decision records
- [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md): threat model
- [`SECURITY.md`](SECURITY.md): how to report vulnerabilities

## 📄 License

[MIT](LICENSE)
