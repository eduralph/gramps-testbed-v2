# Result — issue 13865 / dashboard-gramplet-offscreen-high-column-count

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: On the Dashboard with "Number of Columns" set to **20**, adding a gramplet (e.g. FAQ) below the "Top Surnames" gramplet places it **off screen**, with blank space between gramplets. Setting columns back to 2 restores correct placement (the gramplet appears directly below Top Surnames). (Mantis 13865; confirmed on 6.0.1, notes 1–2, screenshots attached.)
- Success criterion: With the Dashboard column count set to a high value (e.g. 20), adding a gramplet places it in a **valid, visible** column position — the new gramplet is reachable on screen and laid out without stray gaps — for any column count the control accepts.
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61 (core).
- Scope (one logical fix) / out of scope: a high column count mis-places a newly-added gramplet off screen — make placement land in a valid visible column for any accepted column count. / **out of scope:** the crash/lock defect of 13864 (different symptom; confirm shared-vs-distinct cause from the code before bundling); any Gramplet-Layout UX redesign or max-column policy (flag to the human if the only fix is a product-level cap).

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): fail — T1 ✗ po: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [baseline]: matches recorded baseline: 1 known test red(s); signature '_ErrorHolder (Glade __setattr__ name-
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review — issue 13865 / dashboard-gramplet-offscreen-high-column-count

**Reviewer:** Check (advisory, decorrelated from builder)
**Artifacts read:** `brief.md`, `patch.diff`, `check-gates.json`
**Artifact withheld:** `build-notes.md` (by design)
**Date:** 2026-06-20

---

## §1 Overall verdict

**CONDITIONAL PASS** — three NEEDS-HUMAN items must be cleared before the PR can be marked ready (§6). No hard FAIL blocks shipping except the T1 gate, which is tentatively a false-positive against a core fix but requires human adjudication.

---

## §2 Complete verdict table

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | `brief.md` is present and well-formed: defect, success criterion, invariant, scope boundary, test-file preference, and `po/POTFILES.skip` obligation all stated; success criterion is load-bearing and testable (`brief.md` §Defect/§Success criterion) |
| C2 — C2 Reproduction (red pre-fix) | PASS | C4 gate records `red-without-fix=PASS` (`check-gates.json:38`); `grampletlayout_test.py:141–165` (`test_old_viewport_division_would_go_off_screen`) independently documents the pre-fix formula and asserts it selects an off-screen column (col 3, start=900px > viewport=800px) |
| C3 — C3 Change | PASS | Four coherent files: (1) new `gramps/gui/grampletlayout.py` — pure helper `column_index_for_x`; (2) new `gramps/gui/test/grampletlayout_test.py` — seven headless tests; (3) `gramps/gui/widgets/grampletpane.py:1350–1251` — old viewport-division loop replaced with helper call using real `get_allocation()` bounds; (4) `po/POTFILES.skip:263,271` — both new files registered; path discrepancy vs. `brief.md` noted in §6 item 2 |
| C4 — C4 Verification (red→green) | PASS | Gating gate; `check-gates.json:38` — `C4-verify: green-with-fix=PASS / red-without-fix=PASS`; `gating=true` |
| C5 — C5 Causal adequacy | PASS | Root cause re-derived: old formula `x < (sx / len(self.columns) * (i + 1))` at `grampletpane.py:1232–1235` (pre-patch) uses `sx` (viewport width); when 20 × 300px columns overflow an 800px viewport, the thresholds cap at 800px — a click at content-x=150 satisfies `150 < 160` (threshold for i=3), yielding col=3, whose start is 900px (off-screen); fix uses each column's own `get_allocation()` so thresholds track real content positions; causal chain is closed |
| T1 — T1 Structure | NEEDS-HUMAN | Gate FAIL: `check-gates.json:55` — `T1 ✗ po: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)`; this is a core fix (`gramps-project/gramps @ maintenance/gramps61`), not an addon — `.gpr.py` is not expected; gate appears misconfigured for core changes; human must adjudicate whether this is an acceptable false-positive or requires a structural addition (§6 item 1) |
| T2 — T2 Shape | PASS | `check-gates.json:66` — `T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style`; GPL-v2 headers present on all new files in patch (`grampletlayout.py:1–24`, `grampletlayout_test.py:1–24`); touched `grampletpane.py` already carried a header |
| T3 — T3 Runtime | PASS | Both T3 sub-gates pass: unit baseline matches (`7 known reds`, `check-gates.json:73`); GUI smoke matches (`1 known red`, `check-gates.json:82`); baseline tree-drift warning (`recorded detached@674e3b`) noted — baseline commit may not equal current branch tip, but no new regressions are introduced relative to that baseline |
| T4 — T4 Contribution | N/A | `check-gates.json:91` — `T4 – N/A: no commit-msg.txt or pr-description.md in bundle`; contribution wrapper absent from artifact set; not evaluated |
| T5 — T5 Judgment | PASS | Design choices are sound: extracting `column_index_for_x` as a pure, GUI-free helper enables the headless test to exercise the real production decision path; seven tests cover the direct regression, the old-formula counter-example, in-range invariant for counts 1–30, boundary positions (left-of-all, right-of-all, empty list), and midpoint-per-column accuracy; `po/POTFILES.skip` obligation met; path discrepancy (`brief.md` names `grampletbar.py`, patch modifies `grampletpane.py`) is flagged for human confirmation in §6 item 2 and does not itself justify a FAIL given the causal chain reads correctly |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Success criterion requires live GUI exercise: Dashboard → 20 columns → right-click below Top Surnames → add FAQ → confirm gramplet appears on screen without gaps; headless tests confirm helper arithmetic but cannot confirm that `GrampletPane.drop_widget` is the only placement callsite, that `get_allocation()` returns valid bounds at drop time in the running GTK application, or that no other path re-introduces viewport-division logic; §6 item 3 |

---

## §3 Causal analysis (re-derived independently)

The old placement loop (pre-patch `grampletpane.py:1231–1235`) compared the drop x-coordinate against evenly-spaced thresholds of the **viewport** width `sx`:

```
for i, column in enumerate(self.columns):
    if x < (sx / len(self.columns) * (i + 1)):
        col = i; break
```

When column count is high (20 columns × 300 px each = 6 000 px content), the viewport (`sx` ≈ 800 px) is narrower than the content, so the threshold for column *i* is `800/20 × (i+1) = 40(i+1)` px, not `300(i+1)` px.  A click at content-x = 150 px satisfies `150 < 40×4 = 160`, selecting column 3.  Column 3 starts at 3 × 300 = 900 px, which is scrolled off screen (viewport ends at 800 px).  This matches the reported symptom exactly.

The fix reads the real GTK allocation of each column widget:

```python
col = column_index_for_x(
    x,
    [(column.get_allocation().x, column.get_allocation().width)
     for column in self.columns],
)
```

`column_index_for_x` returns the first column whose `start + width > x`, clamped to `[0, n-1]`.  With real allocations the threshold for column 0 is 300 px; x=150 < 300 satisfies on the first column.  Column 0 starts at 0 px — on screen.  For any column count the allocated spans sum to the full content width, so any x is covered by some in-range column.

The invariant stated in `brief.md` is restored: the returned index is always in `range(len(columns))`.

---

## §4 Test quality assessment

`grampletlayout_test.py` provides seven tests grouped in one `TestColumnIndexForX` class:

| Test method | What it guards |
|---|---|
| `test_bug_13865_high_column_count_stays_on_screen` | Direct regression: 20-col, click-x=150 → col=0, col-start < viewport |
| `test_old_viewport_division_would_go_off_screen` | Counter-example: old formula → col=3 (off-screen); new helper ≠ old result |
| `test_index_always_in_range_for_any_count` | Invariant: column counts 1–30, seven x positions each, all in range |
| `test_click_inside_a_column_returns_that_column` | Correctness: midpoint of each of 10 columns maps to that column |
| `test_left_of_all_maps_to_first` | Left-clamp boundary |
| `test_right_of_all_maps_to_last` | Right-clamp boundary |
| `test_no_columns_is_defensive_zero` | Empty-list guard |

Coverage is adequate for the invariant as stated.  The tests are headless (`no gi import`) and can run in the core unit suite.

---

## §5 Open concerns (non-blocking, advisory)

1. **`get_allocation()` timing** — `GrampletPane.drop_widget` is called from a GTK drag-and-drop signal handler.  At that point all columns must be realized (they are visible before the drag begins), so allocations should be valid.  However, if the window has been resized mid-drag and the allocation update is deferred, the bounds could be stale for one frame.  This is an edge case and unlikely to manifest in practice; no action required unless testing reveals it.

2. **T3 baseline tree drift** — `check-gates.json:73` warns that the baseline was recorded at `detached@674e3b`, which may not equal the current `maintenance/gramps61` tip.  The 7 known reds match, indicating no regressions relative to the baseline commit; the drift itself is a maintenance concern for the testbed, not a blocker for this issue.

3. **#13864 isolation** — `brief.md` requires confirming whether #13864 (Dashboard crash/lock) shares a root cause.  The patch touches no locking or signal-handling code, only the column-index arithmetic; the two issues appear distinct from patch content alone.  No action required from Do in this cycle, but the human should note this for triage if #13864 resurfaces.

---

## §6 NEEDS-HUMAN items — must be cleared before sign-off

**§6.1 — T1 gate FAIL (false-positive adjudication)**
The T1 gate reports FAIL because no `.gpr.py` file is present in the bundle.  `.gpr.py` is an addon-registration requirement (doc16-addon §Structure); this patch is a core fix.  **Human action required:** confirm that the T1 FAIL is a gate false-positive for core changes and that shipping proceeds without a `.gpr.py`, or identify what structural gap the gate intended to catch and address it.

**§6.2 — Path discrepancy: `grampletbar.py` vs. `grampletpane.py`**
`brief.md` (§Invariant) names `gramps/gui/widgets/grampletbar.py` as the gramplet-bar placement/layout source.  The patch modifies `gramps/gui/widgets/grampletpane.py`.  These are different files.  **Human action required:** confirm that `grampletpane.py:drop_widget` is the correct and complete callsite for column-placement on the Dashboard, and that no parallel path in `grampletbar.py` performs the same viewport-width division (which would leave the bug partially present via that path).

**§6.3 — Validation (V): live GUI confirmation**
The headless tests confirm that the helper function is arithmetically correct and that the production call in `grampletpane.py` routes through it.  They cannot confirm end-to-end GUI behaviour.  **Human action required:** run the repro from `brief.md` (example.gramps → Dashboard → 20 columns → right-click below Top Surnames → Add FAQ gramplet) and verify the gramplet appears in a visible, on-screen position without stray gaps, satisfying the success criterion.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] T1 — T1 Structure — Gate FAIL: `check-gates.json:55` — `T1 ✗ po: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)`; this is a core fix (`gramps-project/gramps @ maintenance/gramps61`), not an addon — `.gpr.py` is not expected; gate appears misconfigured for core changes; human must adjudicate whether this is an acceptable false-positive or requires a structural addition (§6 item 1)
- [x] V — Validation — fitness-to-purpose — Success criterion requires live GUI exercise: Dashboard → 20 columns → right-click below Top Surnames → add FAQ → confirm gramplet appears on screen without gaps; headless tests confirm helper arithmetic but cannot confirm that `GrampletPane.drop_widget` is the only placement callsite, that `get_allocation()` returns valid bounds at drop time in the running GTK application, or that no other path re-introduces viewport-division logic; §6 item 3

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
- By / date: Eduard Ralph / 2026-06-20

## 10. Act candidates (hints for the next Act review)
- T1 gate fires false-positive on core fixes (no .gpr.py) — gate should only apply to addons-source changes, not gramps-core patches.
