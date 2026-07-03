# Result — issue 6170 / sidebar-filter-copy-shortcut

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: In a list view whose sidebar/filter has a focused text entry, pressing
- Success criterion: After the fix, with focus in a sidebar/filter text entry that
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: The navigation-view Ctrl+C handler, connected to the toplevel window,

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: unverifiable — patch ships no core test (*_test.py) — C4 red/green cannot run locally (e.g. a prose / ci.yml / fork-CI-verified change)
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): fail — C4-verify-interface: green-with-fix=PASS / red-without-fix=FAIL
- C5 test exercises the production path (not a copy): pass — added test(s) import the production package 'gramps'

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [green]: green (no failures); baseline now clear (1 recorded red(s) gone) | ⚠ baseline tree drift: recorded 
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

Reviewing Mantis 6170 / sidebar-filter-copy-shortcut: focused sidebar/filter text entries must own Ctrl+C, while list/tree focus must still copy the selected Gramps object.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief states the stolen-Ctrl+C defect, success criterion, invariant, and out-of-scope behavior for list/tree object copy at [brief.md](/tmp/pdca-review-gd66mz9c/brief.md:6) and [brief.md](/tmp/pdca-review-gd66mz9c/brief.md:28). |
| C2 — C2 Reproduction (red pre-fix) | NEEDS-HUMAN | DECISION OWED: confirm the withheld AT-SPI repro or manual repro actually goes red on the unpatched target; I could re-derive the static pre-fix path because the window-level handler consumes primary-C before propagation at [navigationview.py](/home/eddie/gramps/gramps/gramps/gui/views/navigationview.py:481) and the list view builds a `Gtk.Entry` search bar at [_searchbar.py](/home/eddie/gramps/gramps/gramps/gui/filters/_searchbar.py:57), but `engine/interface/test_bug_0006170_sidebar_filter_copy.py` is deliberately not in this artifact bundle per [brief.md](/tmp/pdca-review-gd66mz9c/brief.md:37). |
| C3 — C3 Change | PASS | The patch changes the same top-level Ctrl+C branch by checking `self.uistate.window.get_focus()` and returning `False` for `Gtk.Editable`/`Gtk.TextView` before `call_copy()`, while leaving object copy for non-editable focus intact at [patch.diff](/tmp/pdca-review-gd66mz9c/patch.diff:4). |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | DECISION OWED: accept only after a human sees the AT-SPI/manual red-to-green result; locally, `git apply --check` against `$PDCA_TARGET` passed and an applied temp copy compiled with `python3 -m py_compile`, but the configured core gate is `unverifiable` and the interface gate failed because its core worktree was missing at [check-gates.json](/tmp/pdca-review-gd66mz9c/check-gates.json:33) and [check-gates.json](/tmp/pdca-review-gd66mz9c/check-gates.json:42). |
| C5 — C5 Causal adequacy | PASS | The root cause and fix are in the production handler connected to the top-level window at [pageview.py](/home/eddie/gramps/gramps/gramps/gui/views/pageview.py:131); pre-fix it calls object-copy on Ctrl+C at [navigationview.py](/home/eddie/gramps/gramps/gramps/gui/views/navigationview.py:487), and the patch gates exactly that call based on focused editable state at [patch.diff](/tmp/pdca-review-gd66mz9c/patch.diff:16). |
| T1 — T1 Structure | N/A | No addon structure is touched; the patch modifies only `gramps/gui/views/navigationview.py` at [patch.diff](/tmp/pdca-review-gd66mz9c/patch.diff:1), matching the gate's core-only N/A note at [check-gates.json](/tmp/pdca-review-gd66mz9c/check-gates.json:60). |
| T2 — T2 Shape | PASS | The touched file already imports `Gtk` and `Gdk` at [navigationview.py](/home/eddie/gramps/gramps/gramps/gui/views/navigationview.py:41), no files are added or removed per [brief.md](/tmp/pdca-review-gd66mz9c/brief.md:46), and the patched temp copy compiles. |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: decide whether to rerun/clear runtime gates in a prepared environment; current gate evidence is not a product failure signal because both unit and interface baselines exited before producing JUnit XML at [check-gates.json](/tmp/pdca-review-gd66mz9c/check-gates.json:87) and [check-gates.json](/tmp/pdca-review-gd66mz9c/check-gates.json:96). |
| T4 — T4 Contribution | N/A | No commit message or PR-description artifact is present in this review bundle, and the contribution gate marks that N/A at [check-gates.json](/tmp/pdca-review-gd66mz9c/check-gates.json:105). |
| T5 — T5 Judgment | PASS | The change is narrowly scoped to the production Ctrl+C handler, preserves `call_copy()` for non-editable focus at [patch.diff](/tmp/pdca-review-gd66mz9c/patch.diff:19), and does not alter paste/cut or clipboard implementation scope excluded by [brief.md](/tmp/pdca-review-gd66mz9c/brief.md:31). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: a human must confirm the actual Gramps GUI behavior matches the intended UX, because fitness-to-purpose turns on visible focus/clipboard behavior described at [brief.md](/tmp/pdca-review-gd66mz9c/brief.md:12), not just static code shape. |

## §6 Human Decisions

1. C2 reproduction red pre-fix: run the withheld interface repro on an unpatched `maintenance/gramps61` worktree, or manually open People view, select a person, focus the sidebar/filter Name entry, type and select text, press Ctrl+C, and confirm the Gramps Clipboard window opens instead of copying the selected text.
2. C4 red-to-green verification: after applying the patch, rerun the same AT-SPI repro or manual flow and confirm Ctrl+C in the focused entry copies the selected text to the system clipboard without opening the Gramps Clipboard window, then focus the list/tree and confirm Ctrl+C still copies the selected object.
3. T3 runtime: rerun the core/unit and GUI interface baselines in an environment where the runner can create the required worktree and JUnit output; the present failures are pre-test runner failures, not evidence about this patch.
4. V fitness-to-purpose: sign off only if the final GUI behavior is acceptable for the full supported set of list views with sidebar/filter editable widgets, not just the People-view example.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C2 — C2 Reproduction (red pre-fix) — DECISION OWED: confirm the withheld AT-SPI repro or manual repro actually goes red on the unpatched target; I could re-derive the static pre-fix path because the window-level handler consumes primary-C before propagation at [navigationview.py](/home/eddie/gramps/gramps/gramps/gui/views/navigationview.py:481) and the list view builds a `Gtk.Entry` search bar at [_searchbar.py](/home/eddie/gramps/gramps/gramps/gui/filters/_searchbar.py:57), but `engine/interface/test_bug_0006170_sidebar_filter_copy.py` is deliberately not in this artifact bundle per [brief.md](/tmp/pdca-review-gd66mz9c/brief.md:37).
- [x] C4 — C4 Verification (red→green) — DECISION OWED: accept only after a human sees the AT-SPI/manual red-to-green result; locally, `git apply --check` against `$PDCA_TARGET` passed and an applied temp copy compiled with `python3 -m py_compile`, but the configured core gate is `unverifiable` and the interface gate failed because its core worktree was missing at [check-gates.json](/tmp/pdca-review-gd66mz9c/check-gates.json:33) and [check-gates.json](/tmp/pdca-review-gd66mz9c/check-gates.json:42).
- [x] T3 — T3 Runtime — DECISION OWED: decide whether to rerun/clear runtime gates in a prepared environment; current gate evidence is not a product failure signal because both unit and interface baselines exited before producing JUnit XML at [check-gates.json](/tmp/pdca-review-gd66mz9c/check-gates.json:87) and [check-gates.json](/tmp/pdca-review-gd66mz9c/check-gates.json:96).
- [x] V — Validation — fitness-to-purpose — DECISION OWED: a human must confirm the actual Gramps GUI behavior matches the intended UX, because fitness-to-purpose turns on visible focus/clipboard behavior described at [brief.md](/tmp/pdca-review-gd66mz9c/brief.md:12), not just static code shape.
- [x] C4 fix verified: test red pre-fix, green post-fix unverifiable — patch ships no core test (*_test.py) — C4 red/green cannot run locally (e.g. a prose / ci.yml / fork-CI-verified change)

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
- By / date: Eduard Ralph / 2026-07-02

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
