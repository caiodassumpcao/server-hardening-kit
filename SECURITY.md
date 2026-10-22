# Política de segurança

## Reportando uma vulnerabilidade

Se você encontrou um problema de segurança neste kit, por exemplo uma
configuração que **enfraquece** o host ou um cenário de lockout não coberto,
**não abra uma issue pública**.

Use o **Private vulnerability reporting** do GitHub (aba *Security → Report a
vulnerability*) com:

- versão/commit do kit e versão do Ubuntu alvo;
- passos para reproduzir;
- impacto esperado.

Resposta inicial em até 5 dias úteis.

## Escopo

| Dentro do escopo | Fora do escopo |
|---|---|
| Roles, playbooks, templates e scripts deste repositório | Vulnerabilidades no Ubuntu, OpenSSH, ufw, fail2ban, auditd ou Lynis (reporte ao upstream) |
| Defaults inseguros ou documentação que induza a erro | Configurações alteradas pelo usuário no inventário |

## Boas práticas para quem usa o kit

- Rode `make check` antes de `make harden` em qualquer host de produção.
- Mantenha um acesso fora de banda (console do provedor) antes da primeira execução.
- Nunca versione `inventories/<ambiente>/`, `vault.yml` sem criptografia ou `reports/`.
