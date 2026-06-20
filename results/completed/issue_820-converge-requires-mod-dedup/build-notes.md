# Build notes — 820-converge-requires-mod-dedup

Target branch: `gramps-project/addons-source @ feature/ci-cd-pipeline-upstream`
(verified against `origin/feature/ci-cd-pipeline-upstream`; `.github/` is
byte-identical at the fork worktree commit `06b95bcd0` used for local C4, so the
line numbers below hold on the target branch).

## What the brief asked for (Success criterion + Invariant)

- `requires_mod` derivation from **one** module #820 owns under `.github/scripts/`,
  consumed by all three jobs.
- `is_active()` in **one** sourced helper consumed by every job.
- Derived module list + active-addon set **unchanged** (CI stays green on the fork).
- No dependency on gramps-testbed-v2 — its `addon_python_deps.py` is design reference only.
- Invariant (DRY/single-source): no derivation or helper duplicated across CI jobs.

## The duplication removed (citations on the target branch)

`.github/workflows/ci.yml`:
- `is_active()` inlined **verbatim** in 6 job steps: lint `76-84`, addon-structure
  `119-127`, compile-check `161-169`, unit-test-linux `337-345`,
  unit-test-windows `525-533`, integration-test `693-701`.
- `requires_mod` install heredoc inlined **identically** in 3 jobs: unit-test-linux
  `242-258`, unit-test-windows `448-464`, integration-test `594-610`.
- `find_spec` validator heredoc inlined **identically** in the same 3 jobs:
  `279-318`, `478-517`, `624-663`.

A one-line change to any was a 3- or 6-site edit, and the copies could silently diverge.

## The fix

Two new files #820 owns (self-contained, no testbed import):

- `.github/scripts/addon_python_deps.py` — sibling to the existing
  `.github/scripts/addon_system_deps.py` (`1-209` on target). Pure stdlib. Exposes
  `install_list(root)` (the install union the 3 install steps print) and
  `check_resolves(root)` (the find_spec name-gate the 3 validate steps run), plus
  `declared_mods(root)` for the raw-name set. Scanning mirrors `addon_system_deps.py`'s
  regex + `ast.literal_eval` mechanism exactly. CLI: `--install-list ROOT` /
  `--check-resolves ROOT`.
- `.github/scripts/active_addons.sh` — the single `is_active()` definition, sourced by
  each filtering step.

`ci.yml`: each install heredoc → `addon_python_deps.py --install-list .` (3 sites,
`python3` on Linux/integration, `python` on the conda-Windows job); each validator
heredoc → `addon_python_deps.py --check-resolves .` (3 sites); each inline
`is_active()` → `source .github/scripts/active_addons.sh` (6 sites). The surrounding
step logic (the `if [ -n "$addon_mods" ]` install loop, the per-step active-addon
filtering loops) is untouched.

Adopted the testbed's `engine/scripts/lib/addon_python_deps.py` **technique** (its
`requires_mod_union`/`unresolved_requires_mod` and the PIL→Pillow map) — re-implemented
in #820's own code, **not** imported.

### Behaviour preservation, proven

`install_list(.)` over the real tree == the old heredoc's output, byte-for-byte:
`boto3 dbf life_line_chart litellm networkx psycopg psycopg2 pygraphviz svgwrite`.
The validator (`check_resolves`) reproduces the old step verbatim: same `pip show`
gate (so a name pip never installed is skipped, not failed — preserving the green on
exotic system-dep gaps), same `find_spec` on the **raw** import name, same
`::error::` output and exit 1. The test pins both against an independent oracle.

### PIL→Pillow decision — in-scope, and a no-op on today's tree

The module carries the design reference's `_IMPORT_TO_DISTRIBUTION = {"PIL": "Pillow"}`
**install-only** map, because the brief's defect text names centralising that map as
part of the goal and the "resolve explicitly, don't leave it silent" learning asks for
it. Decision: **include it, on the install side only.** Two facts make this safe:

1. **No `requires_mod=["PIL"]` exists in the current addons-source tree** (I grepped all
   166 `.gpr.py`; the only `requires_mod` declarations are boto3, dbf, life_line_chart,
   svgwrite, litellm, networkx, pygraphviz, psycopg, psycopg2). So the map maps nothing
   today — `install_list` is **identical** to the old heredoc output, and "derived module
   list unchanged" holds literally. (The brief learning referenced EditExifMetadata's
   `["PIL"]`; that declaration is not present on this branch.)
2. If a `["PIL"]` is ever added, the install side translates to `Pillow` (so
   `pip install` succeeds instead of silently failing with `× PIL failed to install`),
   while `check_resolves` keeps validating the **raw** `PIL` — exactly what Gramps'
   `find_spec` checks. The test asserts the map never leaks into `declared_mods`
   (`Pillow` ∉ raw names), so the find_spec gate can never start checking the
   distribution name.

This is future-proofing + centralisation, not a behaviour change on the current tree.

## Test (`tests/test_requires_mod_dedup.py`)

Lives in the repo's existing top-level `tests/` package (so the C4 runner derives the
valid module `tests.test_requires_mod_dedup`, and the integration job's
`unittest discover -s tests` picks it up in CI too). Pure stdlib / GUI-import-free —
it imports the **production** module the 3 jobs call (not a copy) and reads the real
`ci.yml`, resolving both from `__file__` so it is cwd-independent.

It pins:
1. **Behaviour preservation** — `install_list` and `declared_mods` equal an independent
   oracle (the old heredoc algorithm) over the real tree; the install map is install-only.
2. **DRY invariant, per-category** — no inline `is_active()` and no `requires_mod`
   heredoc survive in `ci.yml`; all 3 jobs call the module (`--install-list` ×3,
   `--check-resolves` ×3); and — addressing learning #2 — **every** job step that *calls*
   `is_active` also sources the helper (parsed step-by-step, asserted ≥6 sites), so a
   missed step is caught rather than masked by an "at least one source" check.

### Red→green (engine runner, fork base)

`run-verify.sh` with the brief's `Verification base: origin/feature/ci-cd-pipeline-upstream`
patches `addons-source-6.0-fork` and reports
**green-with-fix=PASS / red-without-fix=PASS** — green with the module present, red
(`ModuleNotFoundError: addon_python_deps`) with the production files reverted. Note the
brief flags local C4 as not the acceptance signal; the real acceptance is **fork CI
green** (push `feature/ci-cd-pipeline-upstream` → `ci.yml` + `docker-build.yml` run).

## Alternatives rejected

- **Import the testbed's `addon_python_deps.py`** — rejected per the brief's re-plan
  note: #820 must stay self-contained (maintainer decision). Re-implemented the technique
  in #820's own `.github/scripts/` instead.
- **Leave the validator heredoc inline, only dedup the install derivation** — would leave
  the find_spec validator triplicated (3 × ~40 lines = ~120 duplicated lines at
  `279-318`/`478-517`/`624-663` still copy-pasted), so the DRY invariant the brief states
  "over the category (every per-job derivation)" would still be violated. Moving
  `check_resolves` into the module removes all 3 copies at the cost of one ~40-line
  function.
- **A shared composite GitHub Action instead of a script** — heavier (a new
  `action.yml` + wiring in each job) and does not fit the validator, which must run
  *after* the install step inside the same job. A plain script consumed by all jobs is
  the minimal change that restores the invariant.

## POTFILES

addons-source has no top-level `po/POTFILES.in` listing `.github/scripts/` (only per-addon
`po/` dirs, e.g. `DynamicWeb/po/POTFILES.in`); the sibling `addon_system_deps.py` /
`run_addon_tests.py` are likewise unregistered. The new CI scripts and the test carry no
translatable strings and belong to no addon, so no POTFILES change applies.

## Commit-readiness

`black` (default 88-col) run over both new `.py` files — `--check` clean. `ci.yml` is
valid YAML (`yaml.safe_load` parses all 8 jobs). Worktree restored clean after patch
generation.
