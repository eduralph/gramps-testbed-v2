# Front door for the harness — everything you need is a `make` target. No
# PYTHONPATH, no aliases, no remembering subcommands.
#
#   make flow ID=13418                     run the cycle for one issue
#   make flow CSV="engine/….csv"           batch: one Plan session may brief
#                                          SEVERAL issues, all built unattended
#                                          then signed off cheap-first via the queue
#                   Runs Plan → Do → Check → sign-off (Plan/sign-off open Claude in
#                   your terminal; the Do gate runs the live gramps suite in Docker —
#                   use a real terminal). Optional: ACT=1 also runs the cross-cycle
#                   Act review; BY=<name> overrides the §9 attribution (defaults to
#                   the project author). You normally need neither.
#   make rehearse ID=13418 [CSV=…]
#                   dry-run the SAME control flow with stub leaves + stub gates —
#                   no Claude, no Docker, instant. Watch PLANNED→…→COMPLETE first.
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
.PHONY: test check flow rehearse status cli install setup

# --- the cycle -------------------------------------------------------------
# Live, continuous, Claude-driven. Give ID for one issue, or just CSV for a batch
# Plan session that may brief several issues (built all, then signed off cheap-first).
flow:
	@test -n "$(ID)$(CSV)" || { echo 'usage: make flow ID=<issue-id> [CSV="<path>"] [ACT=1] [BY=<name>]'; echo '   or: make flow CSV="<path>" [ACT=1] [BY=<name>]   (batch: Plan briefs several)'; exit 2; }
	$(PDCA) flow $(ID) $(if $(CSV),--from-csv "$(CSV)") $(if $(ACT),--act) $(if $(BY),--by "$(BY)")

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
	@echo "(the very first interactive session may still ask once to TRUST this project — accept it)"

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
