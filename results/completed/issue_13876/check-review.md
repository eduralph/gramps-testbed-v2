# Check Review — issue 13876 / citation-tree-view-delete-noop
## Iteration 2

**Reviewer:** Check (advisory, artifact-only, decorrelated from builder)
**Artifacts read:** `patch.diff`, `brief.md`, `check-gates.json`
**Artifact withheld:** `build-notes.md` (by design)

---

## §1 Overall verdict

**CONDITIONAL FAIL — C4 not cleared; T1 advisory outstanding.**

C4 is the gating element that blocked iteration 1. The same "green-with-fix=PASS / red-without-fix=PASS" claim appears in `check-gates.json` this iteration, but neither the "red-without-fix" leg nor the importability of `LibSourceView` in the headless runner can be verified from the available artifacts. The fix itself is causally correct. Ship is blocked until §6 items are cleared by a human with Bash access.

---

## §2 Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | Brief names the defect (noop delete for Citation row in tree view), the scope (tree mode only; source-row behaviour out of scope), and the success criterion (citation removed from DB matching list-view behaviour). Patch targets exactly these elements. |
| C2 — C2 Reproduction (red pre-fix) | PASS | Gate not configured (check-gates.json result: "none"), but analytically derivable: pre-fix code at `libsourceview.py` calls `remove_source(citation_handle, trans)`; citation handles are not in the source table, so this is a no-op; `assertFalse(db.has_citation_handle(...))` therefore fails → test is red pre-fix by construction. |
| C3 — C3 Change | PASS | Single surgical change at `libsourceview.py:109-112` (diff hunk): replaces hardcoded `remove_source` with `db.method("remove_%s", obj_type)`, making dispatch parametric on `obj_type`. New test file and POTFILES.skip additions are scoped to this fix only; no unrelated deletions (carry-forward concern addressed). |
| C4 — C4 Verification (red→green) | FAIL | Two legs required. **Green-with-fix:** T3-unit matches recorded baseline (no new failures), consistent with the new test passing with the patch applied — derivable. **Red-without-fix:** not derivable from any available artifact; requires running the verify script against the unpatched code. Identical "green-with-fix=PASS / red-without-fix=PASS" claim was fabricated in iteration 1 (builder has no Bash access). Additionally, `LibSourceView` is imported directly in `citationtreeview_test.py:80`; the test docstring asserts the module has no `gi`/`gramps.gui` imports, but this claim was judged "unverified and wrong" in the iteration-1 carry-forward and cannot be re-verified from the patch fragment (only changed lines are shown, not the full import block of `libsourceview.py`). |
| C5 — C5 Causal adequacy | PASS | Root cause is correctly identified: `remove_object_from_handle` already receives `obj_type` as a parameter (confirmed by test call `handler.remove_object_from_handle("Citation", ...)` and by pre-existing `db.method(...)` calls in the unchanged lines at `libsourceview.py:96-98` that already use `obj_type`). The bug is the hard-coded `remove_source` at the tail of the function ignoring that parameter. Fix is minimal and causally complete. |
| T1 — T1 Structure | FAIL | check-gates.json (advisory, gating=false): "T1 ✗ po: no .gpr.py". Same failure as iteration 1; the patch adds `gramps/plugins/view/test/__init__.py` without a paired `.gpr.py`. Gate over-broad for a non-addon test package, but was not cleared in this iteration; carries as advisory. |
| T2 — T2 Shape | PASS | check-gates.json: "T2 ✓ shape: 3 file(s) conform to doc 16 §Coding style". GPL header present on all touched/new files (verified in `patch.diff` lines 22-39). |
| T3 — T3 Runtime | PASS | check-gates.json: T3-unit "matches recorded baseline: 7 known test red(s)"; T3-interface "matches recorded baseline: 1 known test red(s)". No new failures introduced. Note: "baseline tree drift: recorded detached@674e3b" is advisory; human should confirm the baseline commit is the intended reference. |
| T4 — T4 Contribution | N/A | check-gates.json self-reports: "N/A: no commit-msg.txt or pr-description.md in the bundle." No contribution wrapper to evaluate. |
| T5 — T5 Judgment | NEEDS-HUMAN | Oracle defined as "reviewer + human sign-off" (check-gates.json). See §6 items T5-a and T5-b. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Oracle defined as "human at sign-off" (check-gates.json). Must be verified manually in the running application per §6 item V-1. |

---

## §3 Fix analysis

The change at `libsourceview.py` (diff lines 9-12) is correct and minimal:

```python
# before
self.dbstate.db.remove_source(handle, trans)

# after
self.dbstate.db.method("remove_%s", obj_type)(handle, trans)
```

`obj_type` is already in scope (it is a parameter of `remove_object_from_handle` and is used in the unchanged back-reference cleanup loop above this line). When `obj_type == "Citation"`, this resolves to `db.remove_citation(handle, trans)`, which is the correct operation. When `obj_type == "Source"`, it resolves to `db.remove_source(handle, trans)`, preserving existing source-deletion behaviour. The fix is causally adequate and scope-contained.

---

## §4 Test analysis

`citationtreeview_test.py` drives `LibSourceView.remove_object_from_handle` directly via a minimal stub (`_Handler` with only `self.dbstate` set). The test:

1. Creates an in-memory SQLite DB via `make_database("sqlite")` and `db.load(":memory:")`.
2. Adds a Source and a child Citation.
3. Calls `remove_object_from_handle("Citation", citation_handle, trans, in_use_prompt=False)`.
4. Asserts the citation is gone and the source is untouched.

This design correctly avoids the GUI mixin surface (no `uistate`, no GTK/gi) IF AND ONLY IF `libsourceview.py` itself carries no `gi` or `gramps.gui` imports. That conditional is the unresolved blocker (see §6 item C4-a).

---

## §5 Carry-forward compliance

| Iteration-1 finding | Status in this patch |
|---------------------|---------------------|
| Builder fabricated C4 run | Same claim present; cannot be cleared without Bash access — see §6 |
| Test imported LibSourceView (may have GUI deps) | Same import retained; importability still unconfirmed — see §6 |
| Massive POTFILES.skip deletions | **Resolved.** This patch adds only the two new test entries; no unrelated lines removed. |
| T1 __init__.py without .gpr.py | **Not resolved.** Same advisory failure. |

---

## §6 Human sign-off items

These items cannot be cleared from artifacts alone. A human with Bash access to the gramps testbed must verify each before sign-off.

**C4-a (blocking) — LibSourceView importability in headless runner.**
Run `python3 -c "from gramps.plugins.lib.libsourceview import LibSourceView"` under the headless runner environment (no DISPLAY, no GTK init). If the import raises — due to `gi`/`gramps.gui` dependencies anywhere in `libsourceview.py`'s import chain — the test will fail at collection time and C4 cannot be green. If the import succeeds, document the result and proceed to C4-b.

**C4-b (blocking) — Red-without-fix leg.**
Run the verify script (`./engine/scripts/ubuntu/run-verify.sh` or equivalent) against the unpatched `maintenance/gramps61` HEAD to confirm `citationtreeview_test.py` is red without the patch. Record the script output. The check-gates.json entry "red-without-fix=PASS" cannot be accepted on the builder's assertion given the iteration-1 fabrication history.

**T1-a (advisory) — `__init__.py` without `.gpr.py`.**
Confirm whether `gramps/plugins/view/test/` is recognised by the Gramps test runner through `__init__.py`-based package discovery or through a different mechanism. If the `__init__.py` is the correct approach for this test directory and no `.gpr.py` is needed, override the T1 advisory with a written justification. If the test runner works without `__init__.py`, consider removing it to suppress the gate noise.

**T5-a (advisory) — `in_use_prompt=False` parameter.**
Confirm that `LibSourceView.remove_object_from_handle` on `maintenance/gramps61` actually accepts `in_use_prompt` as a keyword argument. The parameter is used in the test at `citationtreeview_test.py:131` but the function signature is not visible in the patch fragment.

**T5-b (advisory) — T3 baseline tree drift.**
check-gates.json notes "baseline tree drift: recorded detached@674e3b". Confirm the baseline was recorded against the correct `maintenance/gramps61` commit and that the 7 known unit test reds are the same pre-existing failures, not regressions introduced by this patch.

**V-1 (always-human) — End-to-end fitness.**
In a running Gramps instance (with example.gramps loaded): Sources category → Citation Tree view → expand any source group → select a Citation row → Delete (toolbar or Edit menu) → confirm dialogs → verify the citation disappears from the view and is absent on reload. This is the success criterion stated in `brief.md` and cannot be confirmed by the headless test alone.
