# Build notes — 820-pluginloading-gate

## Root cause (2 sentences)

`TestPluginLoading.test_load_all_addon_modules` classified load outcomes into
`hard_failures` / `crash_failures` / `dep_skips`, but its only assertion was
`assertGreater(len(plugins), 0)` — the three failure buckets were merely
`LOG.warning`-ed (target-branch `tests/test_plugin_registration.py:224-229`),
so a genuine non-dependency load failure passed silently. The test named a
failure class (`hard_failures`) it could not fail on, unlike the sibling smoke
tests `TestImportPluginSmoke` / `TestExportPluginSmoke`, which `self.fail` on
their findings (`tests/test_plugin_registration.py:257-261`, `287-293`).

## Decision: gate (not advisory)

The Success criterion allowed either making the test gate on non-dependency
`hard_failures` **or** declaring it advisory in the docstring. I chose to
**gate**, because:

- The Invariant to restore is stated over the category ("a CI test that names a
  failure class gates on it"), and the *sibling reference* tests in the same
  file already gate. Making the load check advisory would leave the file with
  one load-class check that doesn't gate beside two that do — inconsistent and
  surprising for a CI suite.
- A `hard_failure` is, by construction, the residue after the advisory classes
  are removed: dependency-unmet plugins are diverted to `dep_skips`
  (`:174-176`) and subprocess crashes (signal death — typically a missing
  display server) to `crash_failures` (`:199-200`). What remains
  (`returncode != 0`, not negative) is a real, non-environmental load error
  with no excuse — exactly what a loadability gate should catch.

`crash_failures` and `dep_skips` stay advisory (`LOG.warning`, `:209-222`),
matching the brief's "keep the dependency-skip / crash classification" scope.

## What changed (target branch = feature/ci-cd-pipeline-upstream @ 1466491ab)

1. **New `tests/plugin_load_gate.py`** — `hard_load_failure_message(hard_failures)`
   returns the gating message (str) when there are non-dependency failures, else
   `None`. Pure Python; imports nothing from `gi` / `gramps.gui`, so it loads in
   a headless runner. This is the single implementation of the gating *decision*.
2. **`tests/test_plugin_registration.py`**
   - import the helper (`:54` post-patch);
   - replace the silent `hard_failures` `LOG.warning` block (`:224-229`
     pre-patch) with `gating_message = hard_load_failure_message(hard_failures);
     if gating_message: self.fail(gating_message)` — production now *routes
     through* the helper;
   - expand the `test_load_all_addon_modules` docstring to declare it a gate;
   - add `TestPluginLoadingGate` (a plain `unittest.TestCase`, GUI-import-free)
     with `test_hard_failure_gates` (synthetic non-dep failure → a fail message)
     and `test_clean_run_does_not_gate` (no failures → `None`).

The test drives the **same** `hard_load_failure_message` that production calls —
not a copy — so the gating verdict the proving test asserts is the verdict
`test_load_all_addon_modules` turns into `self.fail`. The classification loop
(subprocess isolation, `_check_dependencies`) is unchanged, per scope.

## Why a separate prod module (not all in the test file)

The C4 runner (`engine/scripts/ubuntu/run-verify.sh:88-103`) classifies the
patched `test_*.py` file as the *test* and reverts the **other** (non-test)
files for the red pass. If the gating change lived only inside
`tests/test_plugin_registration.py`, the runner would find "no production change
to revert" (`:103`) and the red pass would keep the full gating logic — no red.
Extracting the verdict into `tests/plugin_load_gate.py` gives the runner a
production file to remove for the red pass; with it gone the test module fails
to import → red. This also satisfies the headless-import-safety rule (the helper
is `gi`-free) and the "production routes through the tested module" rule.

## Red → green evidence

Proven through the **exact headless path C4 uses** (`python3 -m unittest`, no
display / D-Bus / AT-SPI) against the feature-tip worktree (gramps 6.0.8 on
`PYTHONPATH`):

- GREEN with the fix: `TestPluginLoadingGate` both cases pass.
- RED with the production change reverted (helper module removed, test kept):
  `import tests.test_plugin_registration` fails with
  `No module named 'tests.plugin_load_gate'` → the test errors. This is exactly
  run-verify's red pass: `plugin_load_gate.py` is classified as an *added*
  production file (`PROD_NEW`) and `rm`-ed (`run-verify.sh:139`), leaving the
  test importing a module that no longer exists.

## C4 / run-verify caveat for Check

`run-verify.sh` validates against the version-pinned **upstream** worktree
(`addons-source-6.0` @ `upstream/maintenance/gramps60` = `03393c7d1`). That
commit does **not** contain `tests/test_plugin_registration.py` — the whole
addon-CI test suite lives only on the unmerged PR #820 branch
(`feature/ci-cd-pipeline-upstream`, the brief's target). A *standalone*
`run-verify` therefore fails to apply the patch (`No such file or directory`),
because `run-verify.sh` does not itself check out the bundle's target branch.

The driver's orchestrated C4 step *does* check out the feature tip onto the
worktree before running (observable in the worktree HEAD reflog oscillating
`1466491ab ↔ 03393c7d1` as sibling PR-#820 bundles validate). I did not run a
standalone `run-verify` to green because (a) at the upstream base it cannot
apply, and (b) the shared worktree was concurrently in use by another lane
(brief warns R-C and `820-review-nits` must not share a wave). The patch was
built and the red→green proof was run in an isolated detached worktree at the
feature tip to avoid disturbing the live lanes.

Note for the green leg of the orchestrated C4: it runs the *whole*
`tests.test_plugin_registration` module, including the now-gating
`test_load_all_addon_modules` against the real addon tree. The brief's premise
is that the tree currently has no `hard_failures` (the test "always-passes"). If
the green leg ever surfaces a real `hard_failure`, that is the gate doing its job
(a genuine addon load problem to triage separately) — not a defect in this
change.

## Alternatives considered

- **Advisory-only (docstring declares non-gating).** Rejected per the Invariant
  reasoning above; would diverge from the two sibling gating tests in the same
  file.
- **Gate inline in the test method (no helper module).** Rejected: defeats the
  C4 red-pass mechanics (no separate prod file to revert, see above) and would
  force the proving test to re-implement the verdict (a hand-copy of production),
  which the harness guidance explicitly forbids.
- **Also gate `crash_failures`.** Rejected: a subprocess signal-death is the
  documented "likely need display server" environmental case the existing code
  isolates on purpose; gating it would make the suite flaky on a bare CI box
  without a display, and the brief scopes the crash classification as "keep".

## Lint / commit-readiness

addons-source CI lint is `ruff check --select=E9,F63,F7,F82 --no-fix` plus a
trailing-whitespace check (`.github/workflows/ci.yml:56-101`) — **not** black /
ruff-format. Verified locally: both changed files `py_compile` clean (E9), no
undefined names (the only new symbol, `hard_load_failure_message`, is imported
and defined), and no trailing whitespace. An incidental `black` rejoin of an
unrelated `self.fail(...)` line was reverted so the diff is one logical change.
