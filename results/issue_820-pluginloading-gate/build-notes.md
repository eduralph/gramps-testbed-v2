# Build notes — 820-pluginloading-gate (iteration 3)

## What the brief settled, and what was actually left to do

This is the third Do pass. The brief is explicit that the **fix design is settled and
was judged sound twice** — iteration 1 was rejected on C2 (regression tested the unit
in isolation, not the production path) and that was corrected; iteration 2's design was
judged sound and only **C4** failed, and that C4 failure was a *harness gap*, not a
design fault (`tests/test_plugin_registration.py` is absent from clean upstream because
PR #820 is unmerged, so run-verify could not find the file to patch).

That gap is now closed (`engine/fork-bases.tsv` 6.0 row → `addons-source-6.0-fork` at
`feature/ci-cd-pipeline-upstream`; run-verify honours `Verification base`). So the
corrective per the brief was: **reproduce the settled v2 fix and demonstrate red→green
through run-verify against the fork base — do not redesign.** I did exactly that, plus
fixed one real, previously-unexercised defect in the patch's file ordering (below).

## The fix

Production (`tests/test_plugin_registration.py` on the fork branch):
- `:53` add `from tests.plugin_load_gate import hard_load_failure_message`.
- `:163` `test_load_all_addon_modules` docstring rewritten to state it now gates.
- `:224-229` the `if hard_failures: LOG.warning(...)` block (the always-pass-by-omission
  symptom named in the brief) is replaced by
  `gating_message = hard_load_failure_message(hard_failures); if gating_message:
  self.fail(gating_message)`. This makes the method gate on a non-dependency hard load
  failure exactly as its two siblings already do (`TestImportPluginSmoke` `self.fail`,
  `TestExportPluginSmoke` `self.fail`).

The dependency-skip and subprocess-crash advisory `LOG.warning`s (`:209-222`) are left
untouched, per the brief's scope ("keep as-is").

New non-test unit `tests/plugin_load_gate.py`:
- `hard_load_failure_message(hard_failures) -> str | None`: the single gating decision —
  non-empty `hard_failures` ⇒ a failure message (caller must fail); empty ⇒ `None`.
- Imports only `from __future__ import annotations`; **no `gi` / `gramps.gui`**, so it is
  loadable in the headless C4 runner.

New regression `tests/test_plugin_load_gate.py` (the brief's named test file):
- Drives the **real** `prod.TestPluginLoading("test_load_all_addon_modules")
  .test_load_all_addon_modules()` with one synthetic always-failing addon injected at the
  production module's own seams (`_get_addon_plugins`, `_check_dependencies`,
  `subprocess.run`). This is the production path, not a copy — it routes through the real
  `hard_load_failure_message` + `self.fail` (principles §3.4; the iteration-1 reject).
- `test_hard_failure_gates_the_load_test`: asserts the method raises
  `TestPluginLoading.failureException` and the message names the addon / "failed to load".
- `test_clean_load_does_not_gate`: a clean load must not fail.
- Imports `gramps.gen`-level only via the production module — no registry boot, no GUI.

## Why a separate test module rather than a case in `test_plugin_registration.py`

The brief requires the regression in its own module. The C4 runner executes the whole
selected module; running `test_plugin_registration` would boot the real registry-backed
`test_load_all_addon_modules`, which — now that it gates — fails on environmental addon
gaps in the minimal image (observed `stock_link` GError), conflating this fix with image
completeness and flaking run-to-run. The dedicated module keeps the gate's verification
deterministic while still exercising the real production code.

## The one real defect I had to fix vs. a literal v2 reproduction: diff file ordering

run-verify classifies patched files by name (`run-verify.sh:119-127`): in addon mode every
`test_*.py` is a candidate test, and the loop keeps the **last** one as `TEST_REL`. Both
`test_plugin_registration.py` and `test_plugin_load_gate.py` match `test_*.py`. `git diff`
emits files alphabetically, which puts `test_plugin_registration.py` **last** — so a
naively-generated patch makes `TEST_REL = tests/test_plugin_registration.py` and C4 would
run the heavy registry module (the exact flaky path the brief forbids). v2 never hit this
because its C4 never executed (file-not-found). I assembled the patch so
`tests/test_plugin_load_gate.py` is the last hunk, giving
`MODULE = tests.test_plugin_load_gate`. Verified in the C4 output:
`(test: tests/test_plugin_load_gate.py ; removing: tests/plugin_load_gate.py)`.

`PROD` = `tests/plugin_load_gate.py` (the only non-`test_` file) → satisfies
run-verify's "patch has no production change to revert" guard (`:130`). This is the whole
reason the brief extracts the helper: a test-only patch has nothing for C4's red leg to
revert, so the gating decision is moved into a non-`test_*.py` unit that production routes
through.

## Red→green proof (run-verify against the fork base)

`PDCA_BUNDLE=… run-verify.sh` → `green-with-fix=PASS / red-without-fix=PASS` on
`addons-source-6.0-fork` (core 6.0.8):
- **Green** (fix applied): both cases pass — the production method raises
  `failureException` on the synthetic hard failure, and passes on a clean load.
- **Red** (production change reverted, test kept): run-verify removes the added non-test
  file `tests/plugin_load_gate.py`; the production module's `from tests.plugin_load_gate
  import …` then raises `ModuleNotFoundError`, so the regression module errors → red.

Note on the red leg: it fires via the import of the removed helper, because the harness
can only revert the **non-test** production file and the gate's `self.fail` wiring lives
in a `test_*.py` file it must keep. This is structurally unavoidable for a fix whose code
under change is itself a test file, and is precisely the seam the brief mandates. The
*substantive* proof of the Success criterion is the **green** leg's
`test_hard_failure_gates_the_load_test`, which asserts the real method raises its
`failureException` on a hard failure — and that assertion would also go red if the
`self.fail` wiring were reverted while the helper stayed (the test genuinely depends on
the production gate, not only on the helper's presence).

## Alternatives considered / rejected

- **Documented-advisory instead of gate.** Closed by the brief (Disposition: settled —
  gate). Would leave one file with two contradictory contracts for "an addon won't load"
  (the two siblings already `self.fail`). Not pursued.
- **Inline `self.fail(f"{len(hard_failures)} addon(s) failed to load:\n  " + …)` with no
  helper module.** Smaller as a diff (~3 lines, no new file), but C4 cannot verify it: a
  test-only patch leaves run-verify with no non-test file to revert (`:130` aborts:
  "patch has no production change to revert"), so the gate could never be proven
  red→green on this harness. The brief forces the extracted seam for this reason. The
  helper is the minimum extraction that both production and the regression route through.
- **Putting the regression case inside `test_plugin_registration.py`.** Rejected — boots
  the flaky real registry under C4 (above), and the brief names a separate file.

## Formatting / commit-readiness

`black` (26.5.0) reports the two new files and my edited hunks clean. The only `black`
delta in the worktree is in `test_target_version_matches_gramps_install` (`:144-148`), a
pre-existing block I did **not** touch — reformatting it would be an unrelated change, so
it is left alone. POTFILES: N/A (addons-source carries no top-level `po/POTFILES.*`; the
POTFILES MUST is core-only per INTEGRATION §4; the added modules carry no translatable
strings).

## Act cleanup — 2026-06-16 (remove the `plugin_load_gate.py` helper)

Per the §10 Act candidate, the harness-driven helper `tests/plugin_load_gate.py`
(`hard_load_failure_message`) is **removed** from the contribution. It had a single
caller and existed mainly to give `run-verify`'s C4 red leg a non-`test_` "production"
file to revert; the gating decision is a one-liner that belongs inline.

What changed in the regenerated `patch.diff`:
- **Deleted** `tests/plugin_load_gate.py`.
- **Inlined** the decision in `tests/test_plugin_registration.py::TestPluginLoading`:
  `if hard_failures: self.fail("<N> addon(s) failed to load:\n  " + …)`. Import + docstring
  reference to the helper dropped.
- `tests/test_plugin_load_gate.py` (the regression test) is **unchanged** — it never
  imported the helper; it drives the real production method via injection. Re-run after the
  edit: **2 tests OK** (`test_hard_failure_gates_the_load_test`, `test_clean_load_does_not_gate`),
  so the inlined gate is proven end-to-end.

C4 consequence: the patch is now **test-only** (two `test_*.py` files, no `production` file
for `run-verify` to revert), so **C4 is no longer mechanically verifiable** — it must be
flagged C4-unverifiable and human-accepted. This is the dependency named in the sibling Act
candidate (INTEGRATION.md should document the C4-unverifiable / test-only path); land that
before/with publishing so the gate posture is on record.
