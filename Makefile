# Front door for the harness — everything you need is a `make` target. No
# PYTHONPATH, no aliases, no remembering subcommands.
#
#   make flow ID=13418                     run the cycle for one issue
#   make flow CSV="engine/….csv"           batch: one Plan session may brief
#                                          SEVERAL issues, all built unattended
#                                          then signed off cheap-first via the queue
#                   Runs Plan → Do → Check → sign-off → publish (on an accept it
#                   opens a DRAFT PR; NO_PUBLISH=1 skips that). Plan/sign-off/publish
#                   open Claude in your terminal — use a real terminal (the Do gate
#                   runs the live gramps suite in Docker). Optional: ACT=1 also runs
#                   the cross-cycle Act review; BY=<name> overrides the §9 attribution
#                   (defaults to the project author).
#   make batch IDS="123 456"
#                   drive issues that are ALREADY briefed through the full cycle
#                   (Do → Check → sign-off → publish → Act) — no Plan beat. Skips
#                   ids with no brief or already complete. NOACT=1 stops after
#                   sign-off; BY=<name> sets the §9 attribution.
#   make rehearse ID=13418 [CSV=…]
#                   dry-run the SAME control flow with stub leaves + stub gates —
#                   no Claude, no Docker (publish dry-runs too), instant.
#   make publish ID=123 [DRY=1]
#                   re-publish an already-accepted bundle as a draft PR (the flow
#                   does this on accept). DRY=1 prints the git/gh plan without pushing.
#   make status     list every bundle and its state.
#   make cli ARGS="signoff 13418 --accept"
#                   run any `pdca` subcommand without the source-path boilerplate.
#
#   make            full self-test: offline guards + a real cycle that fires the
#                   live gramps gate (Docker, ~3-5 min; honestly red on gramps'
#                   own pre-existing failures — that is the engine working).
#   make check      fast: driver + engine guards only, offline, no Docker (~1s).
#   make setup      one-time: grant Claude read of the workspace + sibling repos
#                   so the interactive leaves don't prompt per file/dir.
#   make install    create .venv with a real `pdca` console script (optional —
#                   the targets above already work without it).

PYTHON ?= python3
export PYTHONPATH := src
PDCA := $(PYTHON) -m pdca_harness.cli

.DEFAULT_GOAL := test
.PHONY: test check flow rehearse status cli install setup worktrees essential-worktrees batch publish

# --- the cycle -------------------------------------------------------------
# Live, continuous, Claude-driven. Give ID for one issue, or just CSV for a batch
# Plan session that may brief several issues (built all, then signed off cheap-first).
# On an accept the flow publishes a draft PR; NO_PUBLISH=1 stops at COMPLETE.
flow:
	@test -n "$(ID)$(CSV)" || { echo 'usage: make flow ID=<issue-id> [CSV="<path>"] [ACT=1] [NO_PUBLISH=1] [BY=<name>]'; echo '   or: make flow CSV="<path>" [...]   (batch: Plan briefs several)'; exit 2; }
	$(PDCA) flow $(ID) $(if $(CSV),--from-csv "$(CSV)") $(if $(NO_PUBLISH),--no-publish) $(if $(ACT),--act) $(if $(BY),--by "$(BY)")

# Drive already-briefed issues through the full cycle, no Plan beat (Do → Check →
# sign-off → publish → Act). NOACT=1 stops after sign-off; BY=<name> sets §9.
batch:
	@test -n "$(IDS)" || { echo 'usage: make batch IDS="<id> <id> ..." [NOACT=1] [BY=<name>]'; exit 2; }
	$(PDCA) batch $(IDS) $(if $(NOACT),--no-act) $(if $(BY),--by "$(BY)")

# Re-publish an accepted bundle as a draft PR (the flow does this on accept).
publish:
	@test -n "$(ID)" || { echo 'usage: make publish ID=<issue-id> [DRY=1] [BY=<name>]'; exit 2; }
	$(PDCA) publish $(ID) $(if $(DRY),--dry-run) $(if $(BY),--by "$(BY)")

# Same control flow with stub leaves + stub gates (no Claude / Docker / TTY), in an
# ISOLATED throwaway bundle root so it never touches the real results/ a live run uses.
rehearse:
	@test -n "$(ID)$(CSV)" || { echo 'usage: make rehearse ID=<issue-id> [CSV="<path>"]'; exit 2; }
	@rm -rf .rehearse
	PDCA_BUNDLE_ROOT=.rehearse PDCA_LEAVES_MODE=stub PDCA_GATES_MODE=stub $(PDCA) flow $(ID) $(if $(CSV),--from-csv "$(CSV)")
	@printf '(rehearsal bundles in ./.rehearse — throwaway; real runs use results/)\n'

status:
	@$(PDCA) status

# Escape hatch for any other subcommand: make cli ARGS="queue"
cli:
	$(PDCA) $(ARGS)

# One-time permission setup so the interactive leaves don't prompt: grant Claude
# read of the whole workspace and the sibling repos (gramps, addons-source) it
# patches. Writes the machine-local .claude/settings.local.json (gitignored).
setup:
	@$(PYTHON) -c "import json, os; ws = os.path.dirname(os.getcwd()); \
json.dump({'permissions': {'allow': ['Read(/' + ws + '/**)'], \
'additionalDirectories': [ws + '/gramps', ws + '/addons-source', '/tmp']}}, \
open('.claude/settings.local.json', 'w'), indent=2)"
	@echo "wrote .claude/settings.local.json — workspace read + siblings (gramps, addons-source) + /tmp"
	@echo "NOTE: folder-TRUST is separate from permissions — it lives in the global"
	@echo "      ~/.claude.json, not these settings, so setup can't pre-set it. The very"
	@echo "      first interactive session asks once 'trust this folder?'; accept it and"
	@echo "      it persists for every later run."

# --- validation worktrees: per-version, based on UPSTREAM -------------------
# DEFAULT validation runs against clean upstream/maintenance/gramps6{0,1} — the real
# contribution target, NOT the fork's maintenance branches (which carry local CI/tooling
# commits) or the developer's working clone. Core C4-verify uses gramps-6.{0,1}; the
# addon matrix uses gramps-6.{0,1} + addons-source-6.{0,1}. Detached so they don't
# contend for the primary checkout's branch. Fetches upstream first, then creates
# missing worktrees AND realigns clean existing ones to the current upstream tip.
# LANES=N additionally creates per-lane copies (gramps-6.x-lane0 … -lane{N-1}) for the
# in-driver worker pool (docs 09): lane K's gates patch its own worktree so concurrent
# bundles never contend. The bare set is always (re)built — serial runs use it unchanged.
worktrees:
	@ws=$$(cd .. && pwd); \
	sfxs=""; if [ -n "$(LANES)" ]; then k=0; while [ "$$k" -lt "$(LANES)" ]; do sfxs="$$sfxs -lane$$k"; k=$$((k+1)); done; fi; \
	for r in gramps addons-source; do git -C "$$ws/$$r" fetch upstream --prune --quiet || echo "warn: fetch upstream failed for $$r"; done; \
	for sfx in "" $$sfxs; do \
	for spec in "gramps gramps-6.0 upstream/maintenance/gramps60" \
	            "gramps gramps-6.1 upstream/maintenance/gramps61" \
	            "addons-source addons-source-6.0 upstream/maintenance/gramps60" \
	            "addons-source addons-source-6.1 upstream/maintenance/gramps61"; do \
	  set -- $$spec; repo="$$ws/$$1"; wt="$$ws/$$2$$sfx"; ref="$$3"; \
	  if [ -d "$$wt" ]; then \
	    if [ -n "$$(git -C "$$wt" status --porcelain 2>/dev/null)" ]; then echo "✔ $$wt (exists, dirty — left as-is)"; \
	    else git -C "$$wt" checkout --detach --quiet "$$ref" && echo "↻ $$wt → $$ref ($$(git -C "$$repo" rev-parse --short "$$ref"))"; fi; \
	  else echo "→ git -C $$1 worktree add --detach $$2$$sfx $$ref"; \
	    git -C "$$repo" worktree add --detach "$$wt" "$$ref" || exit 1; fi; \
	done; \
	done; \
	echo "worktrees ready (upstream base)$${sfxs:+; lanes:$$sfxs} — core uses gramps-6.{0,1}; addon matrix adds addons-source-6.{0,1}."

# --- essential fallback line: upstream + harness-enabling fixes -------------
# Builds gramps-<ver>-essential = upstream/maintenance/gramps<ver> + the fixes listed in
# engine/essential-fixes.tsv (cherry-picked), on branch testbed/essential-gramps<ver>.
# run-verify.sh retries a CORE bundle here when it FAILS on upstream, and stamps the
# dependency. Idempotent — skips existing worktrees; pass REBUILD=1 to refresh from the
# manifest (e.g. after upstream moves or the manifest changes).
# LANES=N also builds per-lane essential worktrees (gramps-<ver>-essential-lane{0..N-1})
# on lane-specific branches (a branch can live in only one worktree), mirroring the lane
# copies `make worktrees LANES=N` creates.
essential-worktrees:
	@ws=$$(cd .. && pwd); manifest=engine/essential-fixes.tsv; \
	[ -f "$$manifest" ] || { echo "no $$manifest"; exit 1; }; \
	sfxs=""; if [ -n "$(LANES)" ]; then k=0; while [ "$$k" -lt "$(LANES)" ]; do sfxs="$$sfxs -lane$$k"; k=$$((k+1)); done; fi; \
	git -C "$$ws/gramps" fetch upstream --prune --quiet || echo "warn: fetch upstream failed"; \
	for sfx in "" $$sfxs; do \
	for v in $$(awk -F'\t' '!/^#/ && NF>=3 {print $$1}' "$$manifest" | sort -u); do \
	  tag=$$(echo "$$v" | tr -d .); wt="$$ws/gramps-$$v-essential$$sfx"; br="testbed/essential-gramps$$tag$$sfx"; up="upstream/maintenance/gramps$$tag"; \
	  if [ -d "$$wt" ] && [ -z "$(REBUILD)" ]; then echo "✔ $$wt (exists; REBUILD=1 to refresh)"; continue; fi; \
	  [ -d "$$wt" ] && { git -C "$$ws/gramps" worktree remove --force "$$wt"; git -C "$$ws/gramps" branch -D "$$br" 2>/dev/null || true; }; \
	  git -C "$$ws/gramps" branch -f "$$br" "$$up"; \
	  git -C "$$ws/gramps" worktree add --quiet "$$wt" "$$br" || exit 1; \
	  awk -F'\t' -v v="$$v" '!/^#/ && $$1==v {print $$2}' "$$manifest" | while read -r c; do \
	    git -C "$$wt" cherry-pick "$$c" >/dev/null 2>&1 || { echo "cherry-pick $$c FAILED in $$wt"; git -C "$$wt" cherry-pick --abort 2>/dev/null; exit 1; }; \
	  done; \
	  echo "→ $$wt = $$up + $$(awk -F'\t' -v v="$$v" '!/^#/ && $$1==v {print $$3}' "$$manifest" | paste -sd, -)"; \
	done; \
	done; \
	echo "essential worktrees ready — run-verify falls back here on an upstream failure."

# --- optional real install (venv console script) ---------------------------
install: .venv/bin/pdca
	@printf '\nInstalled. Use `.venv/bin/pdca …` directly, or keep using `make flow …`.\n'

.venv/bin/pdca: pyproject.toml
	$(PYTHON) -m venv .venv
	.venv/bin/pip install -q -e .

# --- self-test -------------------------------------------------------------
# Depends on `check` so the cheap guards fail fast before the slow live cycle.
test: check
	@echo "== full cycle on a throwaway bundle (fires the live gramps engine) =="
	@rm -rf results/issue_selftest
	PDCA_LEAVES_MODE=stub $(PDCA) init-issue selftest --from-brief examples/toy/brief.md
	PDCA_LEAVES_MODE=stub $(PDCA) run selftest
	@printf '\n\xe2\x9c\x93 driver + engine OK. Inspect:\n'
	@printf '    results/issue_selftest/check-gates.md   (live gramps gate: real pass/fail)\n'
	@printf '    results/issue_selftest/SUMMARY.md       (assembled Check summary)\n'

check:
	$(PYTHON) -m pytest tests engine/tests -q
