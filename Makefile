.PHONY: validate lint new-skill new-agent new-stack-rule list install-plugin uninstall-plugin hash-manifests plugin-root test-behavior

SCOPE ?= user

# Check the structure of the whole harness (skills, agents, rules, templates, hooks).
lint validate:
	@scripts/validate.sh

# Check one filled-in artifact, for example:
#   make check KIND=task-spec FILE=.harness/tasks/TASK-001/spec.yaml
check:
	@scripts/validate.sh $(KIND) $(FILE)

new-skill:
	@scripts/new_skill.sh $(NAME) "$(DESC)"

new-agent:
	@scripts/new_agent.sh $(NAME) "$(DESC)"

new-stack-rule:
	@scripts/new_stack_rule.sh $(NAME) "$(DESC)"

# Recompute content_hash (a minimal lockfile, see scripts/hash_manifest.py)
# for EVERY agents/*/manifest.yaml and skills/*/manifest.yaml — run this
# after a manual edit to a manifest.yaml, before you commit. `make validate`
# fails if you forget to run this.
hash-manifests:
	@for f in agents/*/manifest.yaml skills/*/manifest.yaml; do scripts/hash_manifest.py write "$$f"; done

# Scaffold .gft/project.yaml for A PROJECT THAT USES the harness (not this harness itself).
#   make init-project TARGET=/path/to/project
init-project:
	@scripts/init_project_config.sh $(TARGET)

# Register gft-harness as a Claude Code plugin in settings.json.
#   make install-plugin                          # user scope (default): ~/.claude/settings.json
#   make install-plugin SCOPE=project TARGET=/path/to/project
install-plugin:
	@scripts/install_plugin.sh $(SCOPE) $(TARGET)

uninstall-plugin:
	@scripts/uninstall_plugin.sh $(SCOPE) $(TARGET)

# Find the real install path of a plugin (default 'gft') -- see scripts/README.md.
#   make plugin-root NAME=gft
plugin-root:
	@scripts/resolve_plugin_root.sh $(or $(NAME),gft) $(MARKETPLACE)

list:
	@echo "skills:"; ls skills
	@echo "agents:"; ls agents
	@echo "rules:";  ls rules
	@echo "templates:"; ls templates

# REAL behavior test: runs a headless `claude -p` with this plugin active,
# checks that each skill/agent announces the right id and reads the right
# rule file. DIFFERENT from `make validate`: it costs real money (calls the
# real model) and does not run in CI by default. See tests/skill-behavior/README.md.
#   make test-behavior                       # run all 18 cases
#   make test-behavior ONLY=developer,adr    # run only a few cases
test-behavior:
	@python3 tests/skill-behavior/run_behavior_probe.py $(if $(ONLY),--only $(ONLY),)
