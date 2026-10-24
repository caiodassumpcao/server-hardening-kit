SHELL := /bin/bash
.DEFAULT_GOAL := help

# ----------------------------------------------------------------------------
# Configuração (sobrescreva na linha de comando: make harden LIMIT=lab-01)
# ----------------------------------------------------------------------------
PYTHON         ?= python3
VENV           ?= .venv
BIN            := $(VENV)/bin
INVENTORY      ?= inventories/lab/hosts.yml
LIMIT          ?=
TAGS           ?=
ARGS           ?=
# Credenciais "de fábrica" usadas antes do hardening (ubuntu na AWS/Multipass, root na DigitalOcean/Hetzner)
BOOTSTRAP_USER ?= ubuntu
BOOTSTRAP_PORT ?= 22
BOOTSTRAP      ?= 0

VAULT_ARGS     := $(if $(wildcard .vault_pass),--vault-password-file .vault_pass,)
BOOTSTRAP_ARGS := $(if $(filter 1,$(BOOTSTRAP)),-e ansible_user=$(BOOTSTRAP_USER) -e ansible_port=$(BOOTSTRAP_PORT),)
COMMON_ARGS     = -i $(INVENTORY) $(if $(LIMIT),--limit $(LIMIT),) $(if $(TAGS),--tags $(TAGS),) $(VAULT_ARGS) $(BOOTSTRAP_ARGS) $(ARGS)
PLAYBOOK        = $(BIN)/ansible-playbook $(COMMON_ARGS)

export ANSIBLE_FORCE_COLOR := 1

.PHONY: help install lab-init ping lint test-unit test converge verify destroy \
        audit-before check bootstrap harden audit-after report reboot clean

help: ## Lista os comandos disponíveis
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------- setup -----
install: ## Cria o virtualenv e instala Ansible, lint, Molecule e coleções
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt
	bash scripts/galaxy-install.sh $(BIN)/ansible-galaxy

lab-init: ## Cria inventories/lab/ a partir do exemplo (não versionado)
	@if [ -d inventories/lab ]; then echo "inventories/lab já existe"; else \
	  cp -r inventories/example inventories/lab && \
	  cp inventories/lab/group_vars/hardening/vault.yml.example inventories/lab/group_vars/hardening/vault.yml && \
	  echo "Criado inventories/lab/ — edite hosts.yml, main.yml e vault.yml"; fi

ping: ## Testa conectividade Ansible com os hosts (use BOOTSTRAP=1 antes do hardening)
	$(BIN)/ansible hardening -m ansible.builtin.ping $(COMMON_ARGS)

# ------------------------------------------------------------ qualidade -----
lint: ## yamllint + ansible-lint (perfil production)
	$(BIN)/yamllint .
	$(BIN)/ansible-lint

test-unit: ## Testes unitários do gerador de relatório
	$(BIN)/pytest -q tests

test: ## Molecule completo: create → converge → idempotence → verify → destroy
	$(BIN)/molecule test

converge: ## Molecule: sobe o container e aplica o playbook (iteração rápida)
	$(BIN)/molecule converge

verify: ## Molecule: roda apenas as asserções
	$(BIN)/molecule verify

destroy: ## Molecule: remove os containers de teste
	$(BIN)/molecule destroy

# ------------------------------------------------------------- execução -----
audit-before: ## Lynis ANTES do hardening (use com BOOTSTRAP=1)
	$(PLAYBOOK) playbooks/audit.yml -e lynis_label=before

check: ## Modo auditoria: --check --diff, gera JUnit em reports/compliance/
	ANSIBLE_CALLBACKS_ENABLED=ansible.posix.profile_tasks,ansible.builtin.junit \
	JUNIT_OUTPUT_DIR=reports/compliance JUNIT_FAIL_ON_CHANGE=true \
	JUNIT_TASK_CLASS=true JUNIT_HIDE_TASK_ARGUMENTS=true \
	$(PLAYBOOK) playbooks/site.yml --check --diff

bootstrap: ## 1ª execução: conecta com BOOTSTRAP_USER na porta BOOTSTRAP_PORT
	$(MAKE) harden BOOTSTRAP=1

harden: ## Aplica o hardening (steady state: conta de automação na porta nova)
	$(PLAYBOOK) playbooks/site.yml

audit-after: ## Lynis DEPOIS do hardening
	$(PLAYBOOK) playbooks/audit.yml -e lynis_label=after

report: ## Compara before/after e atualiza README + docs/reports/
	$(BIN)/python scripts/lynis_report.py --reports-dir reports \
	  --output docs/reports/lynis-comparison.md --update-readme README.md

reboot: ## Reinicia os hosts e espera voltarem
	$(BIN)/ansible hardening -b -m ansible.builtin.reboot -a "reboot_timeout=600" $(COMMON_ARGS)

clean: ## Remove venv, caches e relatórios locais
	rm -rf $(VENV) .pytest_cache reports
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
