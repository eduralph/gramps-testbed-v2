# Result — issue 13636 / ** uimanager-toolbar-detach-on-close

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: ** Closing the Gramps main window (top-right X) before a queued `page_changer` idle callback fires crashes with `AttributeError: 'NoneType' object has no attribute 'remove'`. During a page change, `ViewManager` schedules `page_changer` via `GLib.idle_add` (`gramps/gui/viewmanager.py:1061-1066`); that callback calls `UIManager.update_menu()`. If the window is torn down first, the previous toolbar is already detached, so `toolbar.get_parent()` returns `None` at `gramps/gui/uimanager.py:258`, and the unguarded `toolbar_parent.remove(toolbar)` at `:260` raises. (Reported on AIO64-5.1.6; the same unguarded code is present on the current maintenance branch. Sibling of bug 12048, already referenced in the `page_changer` comment as a related toolbar-timing crash.)
- Success criterion: ** `UIManager.update_menu(init=False)` no longer raises `AttributeError` when the previous toolbar has already been detached (`toolbar.get_parent()` is `None`); the toolbar-rebuild path is skipped/handled gracefully instead of crashing, so closing the window mid page-change does not produce an unhandled exception.
- Repo + branch target: ** gramps (fork `eduralph/gramps`) @ `maintenance/gramps61` — core GUI fix, forward-merged to `master` (INTEGRATION §2, `doc16:113`). Branch from `upstream/maintenance/gramps61`, not the fork's tracking copy (`doc16:115`).
- Scope (one logical fix) / out of scope: ** Guard the toolbar detach/re-pack in `UIManager.update_menu` (`gramps/gui/uimanager.py:257-271`) against `toolbar.get_parent()` returning `None` (the shutdown race) so the method returns cleanly without raising. / out of scope: redesigning the toolbar rebuild, changing the `GLib.idle_add` / `page_changer` scheduling in `viewmanager.py`, altering window-teardown ordering, and the separate bug 12048.

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: ** likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change)
- T2 shape: code shape vs doc 16 §Coding style (GPL header, no diagnostic print): pass — T2 – N/A: no addons-source path in patch.diff (core-only change)
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — Generated XML report: /workspace/gramps-testbed-v2/test-results/TEST-gramps.gen.merge.test.merge_ref_test.SourceSourceCh
- T3 runtime: addon unit suites (whole-suite baseline): fail — → pip install logs (3 failure(s)): gramps-testbed-v2/test-results/install-logs/
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): fail — Generated XML report: test-results/TEST-unittest.suite._ErrorHolder-20260605101725.xml
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

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

## 6. NEEDS-HUMAN — items the human must clear before sign-off
Reviewed with the human at sign-off. The advisory review (§5) raised these as
NEEDS-HUMAN; each resolved against the `maintenance/gramps61` source and the gate
artifacts, then cleared by the human:
- [x] C5 Causal adequacy / F1 — verified against `gramps/gui/uimanager.py:140-274`.
  The menu rebuild (`menubar.remove_all()` + `append_section`, :253-255) runs *before*
  the guard; the toolbar block (:258-273) is the last block, followed only by a trailing
  `LOG.info`. So the early `return` skips nothing but the toolbar re-pack — F1's "menu/
  accelerator work after the toolbar block" does not exist. `get_parent()` is `None` only
  when the toolbar is not in the widget tree (the shutdown race). Citations match exactly:
  `get_parent()` at :258, `remove()` at :260. Guard is correct and benign.
- [x] T3 core unit (`merge_ref_test.SourceSourceCheck`) — independent. Addon-gated
  (`CliMerge`/`ExportRaw`) record-merge test, downstream of the addon-install failures
  below; unreachable by a core `gui.uimanager` change. Pre-existing baseline. Non-gating.
- [x] T3 addon unit (pip install, 3 failures) — independent. `QuiltView`/`CombinedView`
  declare `target_version` 6.0, invalid for core 6.1.0-beta1. Environmental / addon
  packaging. Non-gating. See §10 follow-up.
- [x] T3 GUI interface smoke (`_ErrorHolder`) — independent. Startup crash in the
  Dashboard/gramplet path; the window never appears and `update_menu`'s toolbar block is
  never reached, so the patch's early `return` cannot be the cause. Separate core bug,
  own cycle. Non-gating. See §10 follow-up.
- [x] T5 Judgment / Validation — fit for purpose: a minimal, correctly-placed guard with a
  genuine red→green regression test plus an anti-trivial-pass companion. Accepted by human.

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: merged-wider
- Iteration delta (if iterating):
- By / date: Eduard Ralph / 2026-06-05

## 10. Act candidates (hints for the next Act review)
Follow-up bugs surfaced during sign-off — independent of this fix, to be filed as
their own tracker items / Do-cycles (NOT part of issue 13636):
- **GUI startup crash (separate core bug).** Launching with the Dashboard view raises
  `AttributeError: Ad-hoc attribute _Glade__dirname is not permitted`
  (`gramps/gui/glade.py:68` `__setattr__` guard, via `grampletpane.py:790` `Glade()`),
  then `AttributeError: 'DummyPage' object has no attribute 'navigation_type'`
  (`grampletbar.py:538`). The main window never finishes building. Reproduced by the T3
  GUI smoke run (`test-results/TEST-unittest.suite._ErrorHolder-20260605101725.xml`).
  Out of scope for 13636; minor; own cycle.
- **Addon `target_version` staleness (addon-maintenance).** `QuiltView` and `CombinedView`
  ship `target_version` "6.0", rejected by core 6.1.0-beta1 ("invalid for Gramps"). This
  breaks the addon-unit install (3 pip failures) and, transitively, the addon-gated
  `gen.merge` tests. Fix is to bump the addons' `target_version`; not a core defect.
