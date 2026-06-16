This is part of the answer to [issue 9393](https://gramps-project.org/bugs/view.php?id=9393), using the "X framebuffer" approach (Option 1 of the feature request).

## Scope

This PR is **strictly CI infrastructure**. After review feedback from @kulath (2026-04-18) — "too many completely different changes in a single commit" — all per-addon code/lint/structure work that was originally bundled here has been split into one-PR-per-addon submissions; see the [Companion PRs](#companion-prs) section at the bottom. This PR adds only the workflow files, the container image, and a small shared test harness.

Thanks also to @GaryGriffin for the early testing feedback on bug 9393 and for asking the questions that led to the standalone per-job reproduction commands below.

## What's in the PR

### CI infrastructure
- `.github/docker/gramps-ci/Dockerfile` — Python 3.12 + Gramps 6.0 (pip) + PyGObject + GTK typelibs (incl. `gir1.2-gexiv2-0.10` for EditExifMetadata / PhotoTaggingGramplet) + xvfb/xauth + ruff, dbf, intltool, gettext, git. GTK lives in the base image so addon modules that do `from gi.repository import Gtk` at module load are importable; xvfb/xauth are bundled for tests that actually render.
- `.github/workflows/docker-build.yml` — rebuilds the image on `.github/docker/**` changes or via `workflow_dispatch`. Default-branch-only; gates on GHCR write access.
- `.github/workflows/ci.yml` — seven jobs:
  - **Lint** — `ruff --select=E9,F63,F7,F82` + trailing-whitespace check (uses `grep -P` so `\t` matches a real tab, not a literal `t` — see commit `205b21c` for the regex bug fix).
  - **Addon Structure** — every addon has `po/template.pot`.
  - **Compile Check** — `python3 -m py_compile` on every `.py`.
  - **Unit Tests (Linux)** — `<addon>/tests/test_*.py` (skips `test_windows_*` / `test_integration_*`) via dotted-path loading.
  - **Unit Tests (Windows)** — same matrix on the native Windows runner with a conda+pip env.
  - **Integration Tests (Gramps)** — `tests/test_plugin_registration.py` + `<addon>/tests/test_integration_*.py`, Linux-only, container `--init` so `xvfb-run` doesn't hang.
  - **Build** — `make.py gramps60 build all`.
- `.github/environment.yml` — hybrid conda+pip environment for Windows. Gramps isn't on conda-forge, so `pygobject`/`gtk3` come from conda; `gramps`/`orjson`/`dbf` come from pip.

### Shared test harness
- `tests/gramps_test_env.py` — `GrampsTestCase` / `GrampsDbTestCase` base classes (stdlib `unittest`, mirroring upstream Gramps' own test style).
- `tests/test_plugin_registration.py` — registers every addon in a subprocess (crash-safe), verifies `gramps_target_version=6.0` plus valid id/name/version, smoke-tests import/export entry functions.
- `tests/__init__.py`.

### TMGimporter test split
The pre-existing `TMGimporter/tests/test_libtmg.py` mixed pure-logic cases with DB-backed cases. Split per the `test_<scope>_*.py` filename convention introduced in commit `715e71d`:
- `test_libtmg.py` — empty stub (kept so a future cross-platform expansion has the file to extend).
- `test_linux_libtmg.py` — 1218 lines, all DB-backed; Linux-only because in-memory Gramps SQLite hangs on Windows under pip-Gramps + conda-forge GTK.

## Gate policy

PR-blocking checks should only fire on issues the PR's own diff can cause. Every test here runs gramps or addon code, so the policy is:

- **Blocking gates** (job-level `continue-on-error: false`): Compile Check, Integration Tests, Build.
- **Advisory gates** (job-level `continue-on-error: true`): Lint, Addon Structure, Unit Tests (Linux), Unit Tests (Windows).

The four advisory gates are currently red on pre-existing tree state (see Companion PRs). As those companion PRs land, the advisories will converge to green and can be flipped to blocking in a follow-up.

## Commits

| SHA       | Date       | Summary |
|-----------|------------|---------|
| `774a9ac` | 2026-04-19 | Initial CI/CD pipeline (issue 9393). Originally larger; force-pushed to this minimal scope after @kulath's review. |
| `c6aa10e` | 2026-04-20 | Auto-derive addon pip deps from `requires_mod` in `.gpr.py`. |
| `8d2654a` | 2026-04-20 | Remove `dbf` from image/env — installed via auto-derive now. |
| `28febdc` | 2026-04-20 | `shell: bash` on unit-test-linux + integration-test steps (fixes Dash `Bad substitution`). |
| `715e71d` | 2026-04-20 | OS-split addon tests by filename convention (`test_linux_*` / `test_windows_*` / `test_integration_*`). |
| `dd0fd38` | 2026-05-11 | Add `gir1.2-gexiv2-0.10` typelib to image (companion to #878, #880). |
| `205b21c` | 2026-05-11 | Lint trailing-whitespace check — switch BRE `[ \t]` to PCRE. The previous BRE pattern was buggy: inside `[...]`, BRE treats `\t` as the literal characters `\` and `t`, so the check matched any line ending in `t`/`\`/`[`/`]`/space — ~3 000 false-positive lines across ~430 files. PCRE (`-P`) correctly recognises `\t` as tab; real count is 597 lines across 21 files. |

## Local reproduction

This PR can't be exercised against `gramps-project/addons-source` directly (workflows live in the PR), but the per-job commands are reproducible standalone:

```bash
# Lint
ruff check --select=E9,F63,F7,F82 --no-fix --exclude='*.gpr.py' .
git --no-pager grep -P -n --full-name '[ \t]+$' -- '*.py' && echo FAIL || echo OK

# Addon Structure
for gpr in */*.gpr.py; do
  d="$(dirname "$gpr")"
  [ -f "$d/po/template.pot" ] || echo "MISSING: $d"
done

# Compile Check
find . -name '*.py' ! -path './.git/*' ! -path '*/__pycache__/*' \
  -exec python3 -m py_compile {} +
```

A complete end-to-end test is also available by forking to a personal repo and pushing a branch — the workflows fire because the workflow files come along with the fork. See the comment thread for the step-by-step walkthrough.

## Companion PRs

Code/lint/structure work that was originally bundled here is now submitted as one-PR-per-addon. Tracker:

- **Compile check (4)** — #834 Query, #835 HouseTimelineGramplet, #836 Themes, #837 lxml.
- **Lint backlog (24)** — #843, #847-#867 (excl. #868), #869 SurnameMappingGramplet (rename + migration).
- **Real bugs (5)** — #870 QuiltView `displayer`, #871 JSON `data`, #872 LifeLineChartView tuple-in-if, #873 libaccess lambda (thanks to @GaryGriffin for catching that the first version of #873 was missing the actual code edit), #874 lxml module-level `self`.
- **Plugin-registration migrations (3)** — #875 Wordle, #876 SourceReferences, #877 RebuildTypes.
- **Dependency declarations (3)** — #878 EditExifMetadata (Pillow + GExiv2), #879 MongoDB (pymongo), #880 PhotoTaggingGramplet (GExiv2).
- **Trailing whitespace (6)** — #881 GeoTimeLines, #882 DNA, #883 GraphView, #884 FamilyTreeDNA, #885 GrampyScript, #886 ToDoReport.
- **Gramps core companions (2)** — gramps-project/gramps#2299 (ClipboardGramplet headless-icon fallback), gramps-project/gramps#2302 (`webreport/common.py` no-ICU fallback) — both required to unblock plugin-registration smoke tests in this PR.

Once those land, all four advisory gates here should report green and can be promoted to blocking.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

