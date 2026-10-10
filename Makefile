# Wire this repo into a skills directory, and keep it inside its budgets.
#
# The repo is the single source of truth: each coding-* directory is symlinked
# individually into every installed CLI's skills directory (claude, codex,
# agy), so each of those directories keeps whatever else it already carries.

REPO       := $(CURDIR)
CLAUDE_DIR ?= $(HOME)/.claude/skills
CODEX_DIR  ?= $(HOME)/.codex/skills
AGY_DIR    ?= $(HOME)/.gemini/antigravity-cli/skills

# Every CLI reading a SKILL.md gets the same working tree. A host is only
# written to when it is installed here, and its own home — the parent of the
# skills directory — is what says so: judging by the skills directory itself
# would skip a host that has one but has never been given a skill.
# Each one is quoted on its own, so a home directory with a space in it is one
# path rather than two.
HOST_DIRS  := "$(CLAUDE_DIR)" "$(CODEX_DIR)" "$(AGY_DIR)"

.DEFAULT_GOAL := help
.PHONY: help check validate test figures drift engines refute render hooks link unlink status

help:
	@echo "make check     validate + test + figures + render drift (what CI runs)"
	@echo "make validate  static rules over the corpus"
	@echo "make test      prove every rule still fires, and test the tools"
	@echo "make figures   re-run the git behaviour the reference layer states"
	@echo "make refute CLAIMS=claims.json RUNNING=claude   put each claim to the engines that did not make it"
	@echo "make engines   ask each checker engine for one object; reports what is unreachable"
	@echo "make drift     re-render the delivered blocks; fail if any were stale"
	@echo "make render    write the delivered blocks back into every SKILL.md"
	@echo "make hooks     install the pre-commit hook"
	@echo "make link      symlink the skills into claude / codex / agy"
	@echo "make unlink    remove those symlinks"
	@echo "make status    show what is linked"

check: validate test figures drift

validate:
	@python3 coding-tools/validate.py

test:
	@python3 coding-tools/test_validate.py
	@python3 coding-tools/test_tools.py

# The delivered blocks in every SKILL.md match their source. A stale block is
# re-rendered in place and the target fails, so the fix is the resulting diff.
drift:
	@before=$$(cat skills/*/SKILL.md | cksum); \
	python3 coding-tools/render.py >/dev/null || exit 1; \
	[ "$$before" = "$$(cat skills/*/SKILL.md | cksum)" ] || { \
		echo "SKILL.md delivery blocks were stale and have been re-rendered; review and commit"; exit 1; }
	@echo "delivered blocks current"

figures:
	@python3 coding-tools/figures_check.py

engines:
	@python3 coding-tools/engine.py --selftest

refute:
	@test -n "$(CLAIMS)" || { echo "usage: make refute CLAIMS=claims.json RUNNING=claude"; exit 2; }
	@python3 coding-tools/refute.py --running "$(or $(RUNNING),claude)" "$(CLAIMS)"

render:
	@python3 coding-tools/render.py

# `--git-path` resolves the hooks directory in a worktree and under
# core.hooksPath, where `.git` is a file or the hooks live elsewhere.
hooks:
	@hooks=$$(git rev-parse --git-path hooks) && mkdir -p "$$hooks" && \
	cp coding-tools/githooks/pre-commit "$$hooks/pre-commit" && \
	chmod +x "$$hooks/pre-commit" && echo "pre-commit installed in $$hooks"

# A skill is a directory holding a SKILL.md, under skills/ where the plugin
# format expects it. The prefix alone is not the test: coding-registry/ and
# coding-tools/ share it and must never be installed.
SKILL_DIRS := $(patsubst %/SKILL.md,%,$(wildcard skills/coding-*/SKILL.md))

# A link is this repo's only when it points at this repo's skill. Another
# checkout's link with the same name is left alone by every target here.
link:
	@for dir in $(HOST_DIRS); do \
		if [ ! -d "$$(dirname "$$dir")" ]; then echo "skip $$dir (host not installed here)"; continue; fi; \
		mkdir -p "$$dir"; \
		echo "$$dir"; \
		for path in $(SKILL_DIRS); do \
			name=$$(basename "$$path"); target="$$dir/$$name"; want="$(REPO)/$$path"; \
			if [ -L "$$target" ] && [ "$$(readlink "$$target")" != "$$want" ]; then \
				echo "  skip $$name (links to $$(readlink "$$target"), not this repo)"; \
			elif [ -e "$$target" ] && [ ! -L "$$target" ]; then \
				echo "  skip $$name (a real path is already there)"; \
			else \
				ln -sfn "$$want" "$$target"; echo "  link $$name"; \
			fi; \
		done; \
	done

unlink:
	@for dir in $(HOST_DIRS); do \
		[ -d "$$dir" ] || continue; \
		echo "$$dir"; \
		for path in $(SKILL_DIRS); do \
			name=$$(basename "$$path"); target="$$dir/$$name"; \
			if [ -L "$$target" ] && [ "$$(readlink "$$target")" = "$(REPO)/$$path" ]; then \
				rm "$$target"; echo "  unlink $$name"; \
			elif [ -L "$$target" ]; then echo "  keep $$name (links elsewhere)"; fi; \
		done; \
	done

status:
	@for dir in $(HOST_DIRS); do \
		echo "$$dir"; \
		for path in $(SKILL_DIRS); do \
			name=$$(basename "$$path"); target="$$dir/$$name"; \
			if [ -L "$$target" ] && [ "$$(readlink "$$target")" = "$(REPO)/$$path" ]; then \
				if [ -e "$$target" ]; then echo "  linked   $$name"; else echo "  dangling $$name"; fi; \
			elif [ -L "$$target" ]; then echo "  foreign  $$name -> $$(readlink "$$target")"; \
			elif [ -e "$$target" ]; then echo "  occupied $$name (a real path)"; \
			else echo "  unlinked $$name"; fi; \
		done; \
	done
