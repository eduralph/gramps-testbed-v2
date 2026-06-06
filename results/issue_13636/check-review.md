# Check Review — issue 13636 / uimanager-toolbar-detach-on-close

> **Reviewer stance:** advisory, artifact-only, decorrelated from the builder.
> Inputs available: `patch.diff`, `brief.md`, `check-gates.json`.
> `build-notes.md` withheld by design; no repo/checkout present. Evidence below
> is re-derived from the diff text and brief; claims that require the actual
> target-branch source or a live run are marked as unverifiable here.

## Overall advisory verdict: **PASS (with NEEDS-HUMAN items)**

The change is a minimal, correctly-placed guard that matches the stated root
cause, and the test is well-constructed: it is genuinely red pre-fix, green
post-fix, and the second test case prevents a trivial pass. Open items are all
either always-human (C5/T5/V) or non-gating baseline failures (the three T3
rows) that appear unrelated to this core-only change and need human
confirmation they are pre-existing.

---

## Re-derived evidence

**The fix (uimanager.py).** After `toolbar_parent = toolbar.get_parent()` the
patch adds:

```python
if toolbar_parent is None:
    LOG.info("*** Update ui: toolbar already detached, skipping rebuild")
    return
```

This directly addresses the brief's root cause: at shutdown the previous
toolbar is already detached, `get_parent()` returns `None`, and the unguarded
`toolbar_parent.remove(toolbar)` raised `AttributeError`. The guard sits exactly
between the `get_parent()` read and the first dereference of `toolbar_parent`
(`remove`), so it cannot be bypassed. ✔

**Red pre-fix / green post-fix (re-derived, not run here).**
- Detached case (`get_parent() → None`): pre-fix reaches
  `toolbar_parent.remove(toolbar)` = `None.remove(...)` → `AttributeError`;
  post-fix returns `None` via the guard. So the test
  `test_update_menu_detached_toolbar_does_not_raise` is genuinely red→green.
- Anti-trivial-pass: `test_update_menu_attached_toolbar_rebuilds` asserts
  `parent.remove.assert_called_once_with(prev_toolbar)`. That assertion can only
  hold if `update_menu` actually reaches the `remove` line, which proves the
  detached test exercises the same path rather than returning early for an
  unrelated reason. This is the right way to harden a "does not raise" test. ✔

**Scope.** `patch.diff` touches only `gramps/gui/uimanager.py` (the guard) and
adds `gramps/gui/tests/uimanager_test.py`. It does not touch `viewmanager.py`,
`GLib.idle_add`/`page_changer` scheduling, or window-teardown ordering, and does
not address bug 12048 — consistent with the brief's in/out-of-scope lines. ✔

---

## Per-item verdicts

| Item | Verdict | Basis |
|---|---|---|
| **C1 Spec** | PASS | `brief.md` states a single, testable success criterion (no `AttributeError` when `get_parent()` is `None`; rebuild skipped/handled, method returns cleanly). Defect, scope, and oracle are unambiguous. |
| **C2 Reproduction (red pre-fix)** | PASS | Re-derived above: detached test raises `AttributeError` pre-fix at the unguarded `None.remove(...)`. Reproduced at the unit layer per brief; companion test confirms the path is reached (no trivial pass). |
| **C3 Change** | PASS | Minimal `is None` guard at the correct location (`get_parent()` read → guard → first deref). In scope; no collateral edits. |
| **C4 fix verified (GATING)** | PASS | Gate reports `green-with-fix=PASS / red-without-fix=PASS`; consistent with my re-derivation. *Note: I cannot independently execute `run-verify.sh` (artifact-only); the verdict rests on the gate plus the structural re-derivation above.* |
| **C5 Causal adequacy** | NEEDS-HUMAN | Always-human. Advisory: the guard targets the exact root cause. One design note (below) — `return` exits the whole method, not just the toolbar block; sanctioned by the scope ("method returns cleanly"), but worth a human glance. |
| **T1 structure** | PASS | N/A — core-only change, no addons-source path. Matches gate. |
| **T2 shape** | PASS | New test file carries the GPL2+ header; the change logs via `LOG.info(...)`, no `print()` diagnostic. Matches gate. |
| **T3 runtime — core unit suite** | NEEDS-HUMAN | Gate result FAIL but **non-gating**. Reported failure is `gramps.gen.merge.test.merge_ref_test.SourceSourceCh…` — unrelated to `uimanager`. Almost certainly a pre-existing whole-suite baseline failure; human should confirm it is baseline, not a regression introduced here. |
| **T3 runtime — addon unit suites** | NEEDS-HUMAN | FAIL, non-gating; cause is `pip install` logs (3 failures) — environmental/setup, not reachable by a core-only `uimanager` guard. Confirm as baseline. |
| **T3 runtime — GUI interface smoke** | NEEDS-HUMAN | FAIL, non-gating (`_ErrorHolder` in the smoke harness). The patch does not touch the launch path; however, because this bug is shutdown/teardown-adjacent, a human should confirm the smoke failure is pre-existing and not caused by the early `return`. |
| **T4 contribution** | PASS | N/A — no `commit-msg.txt` / `pr-description.md` in the bundle. Matches gate. (See finding F4: brief expects path:line citations from Do; not verifiable from these artifacts.) |
| **T5 Judgment** | NEEDS-HUMAN | Always-human (reviewer + human sign-off). |
| **Validation — fitness-to-purpose** | NEEDS-HUMAN | Always-human at sign-off. |

---

## Findings / notes

**F1 — Guard `return` exits the whole method (minor, accepted).** The inline
comment says "Skip the toolbar rebuild," but `return` skips *everything*
remaining in `update_menu` (any menu/accelerator work that follows the toolbar
block). In the shutdown race this is harmless and is explicitly sanctioned by
the brief's scope ("so the method returns cleanly without raising"). Flagging
only so a human confirms no post-toolbar work in `update_menu` must still run in
a legitimate (non-shutdown) `get_parent() is None` scenario. Verdict impact:
none; folded into C5 NEEDS-HUMAN.

**F2 — Test mocks `gi` only, not `config` (divergence from brief, empirically
fine).** The brief describes mocking "`Gtk` and `config`." The test stubs only
`gi`/`gi.repository` and imports `gramps.gen.config` for real. Since C4 reports
the test imports and runs, this works; noted as a benign divergence from the
brief's described setup, not a defect.

**F3 — Three T3 rows are FAIL but non-gating and appear unrelated.** All three
failures (merge_ref unit, addon pip-install, GUI smoke) sit outside the code
this patch touches. The honest read is "pre-existing baseline noise," but
artifact-only I cannot prove they predate the change — hence NEEDS-HUMAN rather
than PASS on those rows. They do not block (gating=false).

**F4 — Citations not verifiable here.** The brief requires Do to cite path:line
on `maintenance/gramps61` (≥ `uimanager.py:258-260`). The patch lands in the
right file/region and the test docstring cites `viewmanager.py:1061-1066` and
`uimanager.py:260`, but with `build-notes.md` withheld and no checkout, I cannot
confirm Do's citations or that the diff's line numbers match the target branch.
Leave to human/T5.

## Residual uncertainties (artifact-only limits)
- Could not execute `run-verify.sh`/`run-unit.sh`; red/green is re-derived
  structurally and corroborated by the gate, not independently run.
- Only the diff hunk context (uimanager.py ~256-271) is visible; code before
  line 256 in `update_menu` (early branches, where the `toolbar` at :258 is
  first bound) is unverifiable. The attached-toolbar test reaching `remove`
  mitigates this by proving the guarded path executes.
