# Guia completo

Passo a passo do `git clone` até um servidor endurecido e medido, mais receitas
de uso, recuperação de lockout e troubleshooting. Para a visão geral do projeto,
veja o [README](../README.md).

> ⏱️ Cerca de 30 minutos na primeira vez. Os comandos rodam no **controller**
> (sua máquina), exceto onde estiver indicado "no servidor".

## Sumário

**Passo a passo**

| Etapa | O que você faz | Comando principal |
|---|---|---|
| [0. Pré-requisitos](#0-pré-requisitos) | Prepara a máquina que roda o Ansible | — |
| [1. Ambiente](#1-clonar-e-preparar-o-ambiente) | Clona e instala as ferramentas | `make install` |
| [2. Chave SSH](#2-criar-uma-chave-ssh-dedicada) | Cria uma chave só para o laboratório | `ssh-keygen` |
| [3. Servidor](#3-provisionar-o-servidor-alvo) | Cria a VM (nuvem ou Multipass) | — |
| [4. Inventário](#4-configurar-o-inventário) | Diz ao Ansible onde e como agir | `make lab-init` |
| [5. Segredos](#5-guardar-segredos-com-ansible-vault) | Guarda o hash da senha criptografado | `ansible-vault encrypt` |
| [6. Conectividade](#6-testar-a-conectividade) | Confirma o acesso inicial | `make ping BOOTSTRAP=1` |
| [7. Lynis "antes"](#7-medir-o-baseline-lynis-antes) | Mede a nota de segurança inicial | `make audit-before BOOTSTRAP=1` |
| [8. Auditoria](#8-rodar-o-modo-auditoria---check) | Vê o que mudaria, sem mudar nada | `make check BOOTSTRAP=1` |
| [9. Bootstrap](#9-aplicar-o-hardening-bootstrap) | Aplica o hardening pela primeira vez | `make bootstrap` |
| [10. Validação](#10-validar-o-acesso-manualmente) | Confere os acessos na mão | `ssh -p 2222 ...` |
| [11. Steady state](#11-segunda-execução-steady-state-e-idempotência) | Fecha a porta 22 e prova a idempotência | `make harden` |
| [12. Reboot](#12-reboot) | Ativa parâmetros de kernel e auditd imutável | `make reboot` |
| [13. Lynis "depois"](#13-medir-o-resultado-lynis-depois-e-publicar) | Mede e publica o resultado | `make audit-after && make report` |

**Referência:** [Receitas](#receitas) · [Recuperação de lockout](#-recuperação-de-lockout) · [Troubleshooting](#-troubleshooting)

---

## 0. Pré-requisitos

**Controller (onde o Ansible roda)**

| Item | Versão | Observação |
|---|---|---|
| Linux, macOS **ou Windows com WSL2** | — | O Ansible **não** roda nativamente no Windows |
| Python | 3.11+ | `python3 --version` |
| `git`, `make`, `ssh`, `openssl` | — | Já vêm no Ubuntu/WSL; no macOS, `xcode-select --install` |
| Docker | 24+ | **Só** para os testes com Molecule |

<details>
<summary><b>🪟 Usando Windows? Clique aqui</b></summary>

Use uma das duas opções:

**Opção 1: WSL2 (recomendado)**

```powershell
# PowerShell como administrador
wsl --install -d Ubuntu-24.04
```

Depois, dentro do Ubuntu (WSL):

```bash
sudo apt update && sudo apt install -y python3-venv python3-pip make git openssh-client
```

> ⚠️ **Clone o repositório dentro do filesystem do Linux (`~/`), não em
> `/mnt/c/...`.** Em `/mnt/c` todos os diretórios aparecem como *world-writable*,
> e por segurança o Ansible **ignora o `ansible.cfg`** do projeto (você verá o
> aviso `Ansible is being run in a world writable directory`). As chaves SSH
> também ficariam com permissões que o `ssh` recusa.

**Opção 2: Dev Container**

Com Docker Desktop e a extensão *Dev Containers* do VS Code, abra o projeto e
escolha **"Reopen in Container"**. O ambiente sobe com Ansible, Molecule e lint
instalados (ver [`.devcontainer/`](../.devcontainer/devcontainer.json)), e
todos os comandos `make` deste guia rodam no terminal do VS Code.

Dois cuidados, ambos causados pelas permissões `777` que pastas do Windows
recebem dentro do container:

- O `ANSIBLE_CONFIG` já vem configurado no Dev Container; sem ele, o Ansible
  ignoraria o `ansible.cfg` do projeto.
- **Crie a chave SSH do passo 2 dentro do container** (em `~/.ssh`, que é do
  Linux), e não na pasta do projeto: o `ssh` recusa chaves privadas com permissão aberta.

</details>

**Servidor alvo**

| Item | Requisito |
|---|---|
| SO | Ubuntu Server **22.04** ou **24.04** LTS (x86_64 ou ARM64) |
| Acesso inicial | SSH por chave com um usuário que tenha sudo sem senha (`ubuntu` na AWS/Multipass) ou `root` (DigitalOcean/Hetzner) |
| Recursos | 1 vCPU, 1 GB RAM, 10 GB disco |
| Saída para internet | Para `apt` e para o repositório do Lynis |
| **Console de emergência** | Console web do provedor ou `multipass shell`, para o caso de lockout |

> 🚫 **Não use um servidor de produção como primeiro alvo.** Use uma VM descartável.

## 1. Clonar e preparar o ambiente

```bash
git clone https://github.com/caiodassumpcao/server-hardening-kit.git
cd server-hardening-kit

make install                 # cria .venv, instala ansible-core, ansible-lint, molecule e as coleções
source .venv/bin/activate    # ativa o ambiente (repita a cada novo terminal)

ansible --version            # deve mostrar ansible-core 2.17+ e o config file ./ansible.cfg
make help                    # lista todos os comandos
make test-unit               # sanity check: testes do gerador de relatório
```

<details>
<summary>O que o <code>make install</code> faz, passo a passo</summary>

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt               # ferramentas Python
.venv/bin/ansible-galaxy collection install -r requirements.yml   # ansible.posix, community.general
```

</details>

## 2. Criar uma chave SSH dedicada

Uma chave só para o laboratório evita misturar acessos e facilita a rotação:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/hardening_lab -C "hardening-lab"
ssh-add ~/.ssh/hardening_lab          # opcional: carrega no agente
cat ~/.ssh/hardening_lab.pub          # você vai colar isto no inventário
```

## 3. Provisionar o servidor alvo

Escolha **uma** opção.

### Opção A: VPS na nuvem (recomendado; é o "deploy de verdade")

Crie uma VM **Ubuntu 24.04** em qualquer provedor e cadastre a chave
`~/.ssh/hardening_lab.pub` na criação.

| Provedor | Usuário inicial (`BOOTSTRAP_USER`) | Firewall do provedor |
|---|---|---|
| AWS EC2 / Lightsail | `ubuntu` | Security Group / aba Networking |
| Azure | definido na criação (ex.: `azureuser`) | Network Security Group |
| GCP | definido pela chave (ex.: `seu_usuario`) | VPC firewall rules |
| Oracle Cloud | `ubuntu` | Security List |
| DigitalOcean | `root` | Cloud Firewall (opcional) |
| Hetzner | `root` | Firewall (opcional) |

> ⚠️ **Antes do bootstrap, libere a porta TCP `2222` (e mantenha a `22`) no
> firewall do provedor.** O ufw controla o firewall *dentro* da VM; Security
> Groups e afins ficam *fora* dela. Se a 2222 estiver bloqueada no provedor, a
> validação pós-deploy falha (de propósito) e a porta 22 continua aberta para você
> corrigir.

### Opção B: VM local com Multipass

[Multipass](https://multipass.run) roda no Windows, macOS e Linux:

```bash
cp lab/cloud-init.yml.example lab/cloud-init.yml
# edite lab/cloud-init.yml e cole sua chave pública (cat ~/.ssh/hardening_lab.pub)

multipass launch 24.04 --name hardening-lab --cpus 2 --memory 2G --disk 10G \
  --cloud-init lab/cloud-init.yml
multipass info hardening-lab | grep IPv4      # anote o IP
```

> 💡 **WSL2 + Multipass no Windows:** se o WSL não alcançar o IP da VM, ative o
> modo de rede espelhado criando `%UserProfile%\.wslconfig` com
> `[wsl2]` / `networkingMode=mirrored` e rode `wsl --shutdown`.

**Confirme o acesso inicial** (troque usuário e IP):

```bash
ssh -i ~/.ssh/hardening_lab ubuntu@203.0.113.10 'lsb_release -ds && sudo -n true && echo SUDO_OK'
```

## 4. Configurar o inventário

```bash
make lab-init      # copia inventories/example → inventories/lab (ignorado pelo Git)
```

Edite **`inventories/lab/hosts.yml`**:

```yaml
lab-01:
  ansible_host: 203.0.113.10                          # ← IP do servidor
# ...
ansible_ssh_private_key_file: ~/.ssh/hardening_lab    # ← descomente
```

Edite **`inventories/lab/group_vars/hardening/main.yml`**:

```yaml
hardening_ssh_port: 2222
hardening_trusted_networks: ["198.51.100.7/32"]   # seu IP público (curl -s ifconfig.me): nunca será banido

users_automation:
  enabled: true
  name: ansible
  ssh_keys:
    - "ssh-ed25519 AAAA... hardening-lab"          # ← conteúdo de ~/.ssh/hardening_lab.pub

users_admins:
  - name: caio                                     # ← seu usuário pessoal
    ssh_keys:
      - "ssh-ed25519 AAAA... hardening-lab"
    password_hash: "{{ vault_admin_password_hash }}"
```

> Por que duas contas? `ansible` é a **automação** (sudo sem senha, apenas chave).
> `caio` é o **humano** (sudo com senha, como pede o CIS). Ver
> [ADR-003](DECISIONS.md#adr-003--conta-de-automação-com-nopasswd-exceção-ao-cis-524).

## 5. Guardar segredos com Ansible Vault

A senha do sudo do administrador vai para o inventário apenas como **hash**, e
o hash fica **criptografado**:

```bash
# 1) gere o hash SHA-512 da senha que você usará no sudo
openssl passwd -6
# Password: ********
# $6$Qx1...                                   ← copie

# 2) cole em inventories/lab/group_vars/hardening/vault.yml
#    vault_admin_password_hash: "$6$Qx1..."

# 3) crie a senha do cofre (arquivo ignorado pelo Git) e criptografe
read -rs -p "Senha do vault: " VP && echo "$VP" > .vault_pass && unset VP && chmod 600 .vault_pass
ansible-vault encrypt inventories/lab/group_vars/hardening/vault.yml

ansible-vault view inventories/lab/group_vars/hardening/vault.yml   # conferir
```

O `Makefile` passa `--vault-password-file .vault_pass` automaticamente quando o
arquivo existe.

## 6. Testar a conectividade

Antes do hardening o servidor ainda está "de fábrica", então usamos as
credenciais de **bootstrap** (`BOOTSTRAP=1`):

```bash
make ping BOOTSTRAP=1                         # AWS / Multipass (usuário ubuntu)
make ping BOOTSTRAP=1 BOOTSTRAP_USER=root     # DigitalOcean / Hetzner
```

Saída esperada: `lab-01 | SUCCESS => { "ping": "pong" }`.

## 7. Medir o baseline (Lynis "antes")

```bash
make audit-before BOOTSTRAP=1
```

O Lynis é instalado a partir do repositório oficial **assinado** da CISOfy, a
auditoria roda e o relatório é baixado para `reports/lab-01/before/`. Exemplo
de saída (o valor depende da imagem):

```
TASK [lynis : Show hardening index]
ok: [lab-01] => msg: 'Lynis hardening index (before) on lab-01: 61'
```

> `reports/` está no `.gitignore`: o relatório bruto contém hostname, IPs e a
> lista de pacotes do servidor. O que vai para o Git é só o resumo sanitizado.

## 8. Rodar o modo auditoria (`--check`)

Antes de alterar qualquer coisa, veja **o que** seria alterado:

```bash
make check BOOTSTRAP=1
```

- Nada é modificado no servidor (`--check`).
- Cada task reportada como **`changed`** é um controle **fora de conformidade**.
  O nome da task traz o ID do CIS (ex.: `CIS 5.1.20 | ...`).
- `--diff` mostra a linha exata que mudaria em cada arquivo.
- Um relatório **JUnit** é gerado em `reports/compliance/`. Cada controle não
  conforme vira um *test failure*, o que permite publicar o resultado no CI,
  em um dashboard ou anexar a uma evidência de auditoria.

```
TASK [ssh_hardening : CIS 5.1.x | Deploy hardened sshd drop-in (first match wins → 00- prefix)]
--- before
+++ after: /etc/ssh/sshd_config.d/00-hardening.conf
+Port 2222
+PermitRootLogin no
...
changed: [lab-01]
```

## 9. Aplicar o hardening (bootstrap)

> 💡 Deixe **outro terminal com uma sessão SSH aberta** no servidor durante a
> primeira execução. É uma boa prática em qualquer mudança de SSH ou firewall.

```bash
make bootstrap                          # usuário ubuntu, porta 22
make bootstrap BOOTSTRAP_USER=root      # DigitalOcean / Hetzner
```

O que acontece, na ordem:

1. **common**: valida o SO, espera o cloud-init, instala e remove pacotes,
   módulos de kernel, banners.
2. **users**: cria `sysadmins`, `sshusers` e `sugroup`, a conta `ansible`, o
   seu admin e as `authorized_keys`, além dos sudoers validados com `visudo`.
3. **ufw**: libera **2222 e 22**, aplica default deny e ativa o firewall.
4. **ssh_hardening**: verifica o *lockout guard*, aplica o drop-in validado
   com `sshd -t` e reinicia o `sshd`.
5. **fail2ban**, **sysctl_hardening**, **auditd** e, por último, **unattended_upgrades** (ativar os timers do apt antes faria o `apt-daily` disputar o lock com as instalações).
6. **Validação**: o controller abre uma sessão **nova** com
   `ansible@IP -p 2222`. Se ela falhar, o playbook falha e a porta 22 continua aberta.

Final esperado (os números variam conforme a imagem):

```
PLAY RECAP *********************************************************************
lab-01   : ok=118  changed=61  unreachable=0  failed=0  skipped=9  rescued=0  ignored=0
TASK [Warn about pending reboot] ***********************************************
ok: [lab-01] => msg: Reboot required to activate kernel boot parameters / immutable audit rules...
```

## 10. Validar o acesso manualmente

```bash
IP=203.0.113.10; KEY=~/.ssh/hardening_lab

# ✅ conta de automação na porta nova
ssh -i $KEY -p 2222 ansible@$IP 'sudo -n true && echo "automação OK (sudo sem senha)"'

# ✅ seu admin: entra com chave, sudo PEDE senha
ssh -i $KEY -p 2222 caio@$IP 'sudo -k; sudo -v && echo "admin OK"'

# ❌ senha não é aceita, nem para usuário válido
ssh -p 2222 -o PubkeyAuthentication=no -o PreferredAuthentications=password caio@$IP
# → Permission denied (publickey).

# ❌ root não entra
ssh -i $KEY -p 2222 root@$IP
# → Permission denied (publickey).
```

**No servidor** (via `ssh -p 2222 caio@IP`):

```bash
sudo sshd -T | grep -E '^(port|permitrootlogin|passwordauthentication|allowgroups)'
sudo ufw status verbose
sudo fail2ban-client status sshd
sudo auditctl -s | grep enabled          # 2 = imutável (após o reboot, ver passo 12)
sudo sysctl net.ipv4.conf.all.log_martians kernel.yama.ptrace_scope
```

## 11. Segunda execução: steady state e idempotência

Agora o inventário "normal" (usuário `ansible`, porta 2222) passa a valer:

```bash
make harden
```

- A regra da **porta 22 é removida** do ufw, porque a conexão atual já usa a 2222.
- O `90-cloud-init-users` (NOPASSWD do usuário `ubuntu`) é removido.

Rode **mais uma vez**. O esperado é **`changed=0`**, ou seja, o playbook é
idempotente:

```bash
make harden
# lab-01 : ok=112  changed=0  unreachable=0  failed=0 ...
```

## 12. Reboot

O `audit=1` no kernel e as regras imutáveis do auditd só valem após o reboot:

```bash
make reboot
ssh -i ~/.ssh/hardening_lab -p 2222 caio@203.0.113.10 \
  'grep -o "audit=1" /proc/cmdline; sudo auditctl -s | grep enabled'
# audit=1
# enabled 2
```

## 13. Medir o resultado (Lynis "depois") e publicar

```bash
make audit-after          # → reports/lab-01/after/
make report               # compara, gera docs/reports/lynis-comparison.md e atualiza este README
```

```
wrote docs/reports/lynis-comparison.md
updated README.md
```

Confira a tabela na seção [Resultados](../README.md#-resultados) e faça o commit:

```bash
git add README.md docs/reports/lynis-comparison.md
git commit -m "docs: publish Lynis before/after results"
git push
```

🎉 **Pronto.** O servidor está endurecido, auditável e com o resultado medido.

---

## Receitas

<details>
<summary><b>Adicionar um administrador</b></summary>

```yaml
# inventories/lab/group_vars/hardening/main.yml
users_admins:
  - name: maria
    comment: "Maria - SRE"
    ssh_keys: ["ssh-ed25519 AAAA... maria@notebook"]
    password_hash: "{{ vault_maria_password_hash }}"
```

```bash
ansible-vault edit inventories/lab/group_vars/hardening/vault.yml   # adicione vault_maria_password_hash
make harden TAGS=users
```

Para **revogar**, mova o nome para `users_absent: [maria]`. Como o
`authorized_keys` é **exclusivo**, remover uma chave da lista também a remove do
servidor.
</details>

<details>
<summary><b>Conta de deploy com sudo restrito</b></summary>

```yaml
users_restricted:
  - name: deployer
    ssh_keys: ["ssh-ed25519 AAAA... github-actions"]
    sudo_commands:
      - /usr/bin/systemctl restart myapp
      - /usr/bin/systemctl reload nginx
```

Resultado em `/etc/sudoers.d/30-hardening-restricted`:

```
Cmnd_Alias DEPLOYER_CMDS = /usr/bin/systemctl restart myapp, /usr/bin/systemctl reload nginx
deployer ALL=(root) NOPASSWD: DEPLOYER_CMDS
```
</details>

<details>
<summary><b>Abrir portas da aplicação</b></summary>

```yaml
ufw_rules:
  - { rule: allow, port: "80",   proto: tcp, comment: "http" }
  - { rule: allow, port: "443",  proto: tcp, comment: "https" }
  - { rule: allow, port: "9100", proto: tcp, from_ip: "10.0.0.0/8", comment: "node_exporter (rede interna)" }
```
</details>

<details>
<summary><b>Restringir SSH ao seu IP / VPN (maior ganho contra brute force)</b></summary>

```yaml
ufw_ssh_allowed_sources: ["198.51.100.7/32", "10.8.0.0/24"]
users_automation:
  allowed_from: ["198.51.100.7"]     # a chave da automação só funciona a partir daqui
```
</details>

<details>
<summary><b>Host com Docker / Kubernetes</b></summary>

```yaml
sysctl_hardening_ip_forward: true   # containers precisam de forwarding
ufw_default_routed: allow           # ou regras "route allow" específicas
```

> O Docker manipula o iptables diretamente e **ignora o ufw** para portas
> publicadas (`-p 8080:80`). Publique só em `127.0.0.1` ou use
> [ufw-docker](https://github.com/chaifeng/ufw-docker).
</details>

<details>
<summary><b>Detecção contínua de drift</b></summary>

Rode `make check` em um agendamento (cron no bastion, ou um workflow agendado com
runner self-hosted). Qualquer `changed` (ou *failure* no JUnit) significa que
alguém alterou o servidor fora do Ansible: um `sysctl -w`, uma chave SSH
adicionada à mão, um NOPASSWD "temporário".
</details>

---

## 🆘 Recuperação de lockout

Se, apesar das proteções, você perder o acesso:

1. Abra o **console fora de banda** (console web do provedor, `multipass shell
   hardening-lab`, serial console).
2. Desfaça só o necessário:

```bash
sudo rm /etc/ssh/sshd_config.d/00-hardening.conf   # volta o sshd ao padrão
sudo systemctl restart ssh
sudo ufw allow 22/tcp                              # reabre a 22
sudo fail2ban-client unban --all                   # remove banimentos
```

3. Corrija a causa (chave errada no inventário, porta bloqueada no provedor…) e
   rode `make bootstrap` de novo. O playbook é idempotente.

---

## 🔧 Troubleshooting

| Sintoma | Causa provável | Solução |
|---|---|---|
| `Ansible is being run in a world writable directory ... ignoring it as an ansible.cfg source` | Repositório em `/mnt/c` no WSL, ou pasta do Windows montada no Docker | WSL: clone em `~/`. Docker: `export ANSIBLE_CONFIG=$PWD/ansible.cfg` (o Dev Container já faz isso) |
| `Permissions 0777 for '...' are too open` | Chave privada em pasta do Windows | Gere/copie a chave para `~/.ssh` do Linux e rode `chmod 600` |
| `UNREACHABLE` / timeout na porta 2222 após o bootstrap | Firewall **do provedor** bloqueando a 2222 | Libere a 2222 no Security Group/Cloud Firewall; a 22 continua aberta |
| `LOCKOUT GUARD: no members in ['sshusers']` | Nenhum usuário com chave definido | Preencha `users_automation`/`users_admins` com `ssh_keys` |
| Falha em *Open a fresh SSH session as the steady-state user* | A chave do inventário não corresponde à sua chave privada | Confira `ansible_ssh_private_key_file` e `users_automation.ssh_keys` |
| `Permission denied (publickey)` no `make harden` | Ainda conectando com o usuário/porta do bootstrap | Pós-bootstrap use `make harden` **sem** `BOOTSTRAP=1` |
| Fui banido pelo fail2ban | Muitas tentativas a partir do seu IP | Pelo console: `sudo fail2ban-client set sshd unbanip SEU_IP`; adicione o IP em `hardening_trusted_networks` |
| `Could not get lock /var/lib/dpkg/lock-frontend` | apt/cloud-init de primeiro boot | O kit já espera até 600s; aumente `hardening_apt_lock_timeout` se preciso |
| Docker/containers sem rede após o hardening | `ip_forward=0` | `sysctl_hardening_ip_forward: true` |
| Handler avisa "audit rules are immutable" | `-e 2` já carregado | Esperado: `make reboot` para aplicar as novas regras |
| `sudo` pede senha e você não sabe qual é | Admin sem `password_hash` | Defina o hash no vault (passo 5) e rode `make harden TAGS=users` |
| Molecule falha ao subir o container | Docker sem suporte a cgroup v2/systemd | Use Docker Engine recente (Linux/WSL2) ou o Dev Container |
| `make check` mostra `changed` em host já endurecido | **Drift**: alguém alterou o servidor | Leia o `--diff`; rode `make harden` para reconciliar |
