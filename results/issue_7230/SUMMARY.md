# Result — issue 7230 / citation-tree-hides-sources-without-citations

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: As filed (v3.4.6): in the Citation Tree View, a source that has no citations
- Success criterion: Every source is shown as a top-level node in the Citation Tree View,
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: how `CitationTreeModel` populates source (top-level) nodes,

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: POSSIBLY-FIXED → verify first
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: fail — → essential-line retry for 6.1 also FAILED — a real failure, not a missing prerequisite.
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): unverifiable — no interface repro engine/interface/test_bug_*7230_*.py for bundle issue_7230 — the per-fix GUI red→green cannot run; th
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 – N/A: no checkable .py path in patch.diff
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [green]: green (no failures); baseline now clear (1 recorded red(s) gone) | ⚠ baseline tree drift: recorded 
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review — Issue 7230 / citation-tree-hides-sources-without-citations

**Reviewer role:** Check (advisory, artifact-only, decorrelated from builder)  
**Artifacts read:** `brief.md`, `check-gates.json`, `patch.diff`  
**`$PDCA_TARGET`:** unset — all path:line citations grounded against `patch.diff` only  
**Overall gate result (engine):** `fail` (C4-verify gating=true)

---

## §1 Patch summary (re-derived)

The patch contains **no production code change**. It adds two artifacts:

1. `gramps/gui/views/treemodels/test/citationtreemodel_test.py` — new 126-line regression-test file (patch.diff:1–132)
2. `po/POTFILES.skip` line `gramps/gui/views/treemodels/test/citationtreemodel_test.py` — i18n exclusion registration (patch.diff:141)

This is consistent with the brief's POSSIBLY-FIXED disposition: "if sources already appear, no production patch — route to §6." The builder elected to add a regression guard rather than a production fix.

---

## §2 Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — Spec | PASS | `brief.md` present, complete, and internally consistent: defect defined, success criterion stated ("every source shown as top-level node"), target file named (`citationtreemodel.py`), test-file path prescribed (`…/test/citationtreemodel_test.py`), POTFILES.skip requirement stated. Test-only patch is consistent with brief's POSSIBLY-FIXED disposition. |
| C2 — Reproduction (red pre-fix) | FAIL | No gate configured (`check-gates.json` C2 result=`"none"`). No evidence the new test was ever red against the pre-fix state (pre-`has_secondary` codebase). For a regression guard the builder must show the test is red on the old behaviour; without that, the test may not target the actual failure mode. C4 failure (test fails on current patched codebase) makes red→green proof impossible in any direction. |
| C3 — Change | PASS | Patch is minimal and contained. New test file has correct GPL v2+ header (`patch.diff:9–23`). `po/POTFILES.skip` entry added in correct block (`patch.diff:141`), immediately before the alphabetically adjacent `node_test.py`. No production file touched. |
| C4 — Verification (red→green) | FAIL | `check-gates.json` C4-verify: result=`"fail"`, gating=`true`. Engine note: "essential-line retry for 6.1 also FAILED — a real failure, not a missing prerequisite." The new test fails at runtime on the patched codebase. No green post-fix state exists to demonstrate. |
| C5 — Causal adequacy | FAIL | The test fails at runtime (C4 FAIL), so adequacy cannot be confirmed. Additionally, the test's internal API access pattern — `model.tree[None]`, `model.nodemap.node(nodeid).handle`, `.children` (`patch.diff:97–98`, `112`, `124–127`) — cannot be verified against `CitationTreeModel` production source with `$PDCA_TARGET` unset. The `uistate=None` headless-safety claim (docstring `patch.diff:46–48`) is also unverifiable. C4 failure suggests at least one assumption is wrong. |
| T1 — Structure | N/A | No addon-source path in patch.diff. T1 (doc 16 §Structure) governs addon layout only. Engine correctly marks N/A. |
| T2 — Shape | PASS | GPL v2+ header present (`patch.diff:9–23`). No `print()` statements in the new `.py` file. Engine gate reported "N/A: no checkable .py path in patch.diff" — this is a gate mis-classification (the file is present), but manual inspection of the diff confirms shape conformance. `po/POTFILES.skip` registration confirmed by separate T2-potfiles gate (result=`"pass"`, gating=`true`). |
| T3 — Runtime | PASS | Unit suite baseline matches recorded baseline (7 known reds, `check-gates.json` T3-unit). Interface smoke green (`check-gates.json` T3-interface). The C4 failure is specific to the new test and is correctly isolated from the baseline gates. |
| T4 — Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in bundle. T4 (doc 16 §Commit messages + §Contributor workflow) cannot be evaluated without those artifacts. Engine correctly marks N/A. |
| T5 — Judgment | FAIL | Three unresolved judgment questions: (a) the `uistate=None` headless-safety claim (`patch.diff:46–48`, `:94`) cannot be verified from diff alone and is contradicted by C4 failure; (b) the internal API surface (`model.tree`, `model.nodemap`) is opaque without the production source and may not exist or may have different shapes than assumed; (c) the builder did not explicitly route to §6 as the brief requires when the defect is already fixed — adding a regression test is not equivalent to a §6 close note, and the lack of a C2 red-pre-fix run means the test's correctness is unconfirmed. |
| V — Validation | NEEDS-HUMAN | Fitness-to-purpose is a product/maintainer decision: whether a test-only patch (with no §6 close note, no red-pre-fix evidence, and a failing C4) constitutes adequate closure of a POSSIBLY-FIXED defect is outside checker authority. |

---

## §3 Gating failures

| Gate | Rule | Status |
|------|------|--------|
| C4-verify | Unit test red→green | **FAIL** (gating=true) — test fails at runtime; no green post-fix state |
| T2-potfiles | POTFILES.skip registration | PASS (gating=true) |

**The C4 gating failure blocks merge.**

---

## §4 Gate discrepancy

The engine T2-shape gate reports "N/A: no checkable .py path in patch.diff." This is incorrect — `citationtreemodel_test.py` is a `.py` file added by the patch. The gate may be filtering test files or may have a path-detection bug. Manual inspection confirms the file passes shape (GPL header present, no `print()`), so the discrepancy does not change the shape verdict, but it should be noted for engine maintenance.

---

## §5 C4 failure — what is likely broken

Without `$PDCA_TARGET` the root cause cannot be confirmed, but the diff gives two candidate failure points:

1. **`uistate=None` not safe headless.** The test docstring (`patch.diff:46–48`) claims that for a tiny db the `ProgressMonitor` never reaches its popup threshold. If `CitationTreeModel.__init__` calls any GTK widget constructor unconditionally (not gated on `uistate`), even a small db causes a `Gtk.init` failure in a headless environment. The engine note "a real failure, not a missing prerequisite" is consistent with a GTK init error rather than a missing import.

2. **Internal API mismatch.** `model.tree[None]` (`:97`), `.children` (`:98`, `:112`), and `model.nodemap.node(nodeid)` (`:98`) are opaque from the diff. If the production `TreeBaseModel` uses different attribute names or a different children structure, the test crashes with `AttributeError` or `KeyError` before the `assertIn` runs. This would also manifest as "a real failure."

Either root cause requires reading `citationtreemodel.py` and `treebasemodel.py` on `maintenance/gramps61` to confirm and fix.

---

## §6 Items requiring human clearance

The following items cannot be resolved by the Check reviewer and must be cleared before this cycle can advance:

**§6-A (from V — NEEDS-HUMAN):** *Disposition adequacy.* The brief says the defect is POSSIBLY-FIXED and instructs "if sources already appear, no production patch — route to §6." No §6 close note accompanies this patch. A human maintainer must decide: (a) confirm the defect is already fixed in `maintenance/gramps61` by running the repro instruction from `brief.md`; (b) determine whether a regression test is required or whether a manual-verification close note suffices; (c) if a test is required, it must be fixed to pass (C4).

**§6-B (from C4/C5 FAIL):** *Test runtime failure.* The new test (`citationtreemodel_test.py`) fails at runtime on gramps 6.1. A developer must: reproduce the C4 failure with `python3 -m pytest gramps/gui/views/treemodels/test/citationtreemodel_test.py -v` on `maintenance/gramps61`; identify whether the failure is a GTK-init / `uistate=None` issue or an internal API mismatch; fix or remove the test accordingly.

**§6-C (from C2 FAIL):** *Red pre-fix evidence.* If the test is kept, the builder must demonstrate it was (or would be) red on the pre-`has_secondary` codebase (e.g., by checking out the commit before the two-cursor refactor and confirming the test fails). Without this, the regression guard does not prove it targets the actual defect.

**§6-D (from T5 FAIL):** *Internal API verification.* `model.tree[None]`, `model.nodemap.node(nodeid)`, and `.children` must be confirmed against the `TreeBaseModel`/`CitationTreeModel` source on `maintenance/gramps61` before any corrected test is submitted.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] V — Validation — Fitness-to-purpose is a product/maintainer decision: whether a test-only patch (with no §6 close note, no red-pre-fix evidence, and a failing C4) constitutes adequate closure of a POSSIBLY-FIXED defect is outside checker authority.
- [x] C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail) unverifiable — no interface repro engine/interface/test_bug_*7230_*.py for bundle issue_7230 — the per-fix GUI red→green cannot run; th

## 7. Proven / not proven
- Proven by which oracle: gates overall = fail (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: merged-wider
- Iteration delta (if iterating):
- By / date: Eduard Ralph / 2026-06-21

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
