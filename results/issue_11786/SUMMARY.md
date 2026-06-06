# Result — issue 11786 / ** tag-rename-stale-name-in-listview

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: ** After renaming a tag (Tags button → Organize Tags → rename), an open list view (e.g. People View) keeps showing the **old** tag name in the Tags column. Switching views and back does not refresh it; only restarting Gramps does. (Mantis 11786, reported against People View, 5.1.2.)
- Success criterion: ** After a tag is renamed while a list view is showing a row tagged with it, that row's Tags column displays the **new** name without restarting Gramps or re-opening the tree — i.e. the rename is reflected on the next view refresh following the `tag-update` signal.
- Repo + branch target: ** gramps (core) @ `maintenance/gramps61` — branched from `upstream/maintenance/gramps61`; forward-merged to `master` by the maintainer (INTEGRATION §2: core fixes ride the current maintenance branch, not `master`).
- Scope (one logical fix) / out of scope: ** Invalidate the renamed tag's stale cached display value(s) so list views re-render the new tag name when the `tag-update` signal fires — the one logical change is making `tag_updated` (or the path it drives) drop the model's `(tag_handle, "TAG_NAME"/"TAG_COLOR")` cache entry for the renamed tag before re-rendering rows. / **out of scope:** redesigning the treemodel cache; touching tag *color* refresh behaviour beyond what falls out of the same cache-key fix; non-list views (chart/relationship views); the Tags side panel.

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: ** likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: fail — C4-verify: green-with-fix=FAIL / red-without-fix=PASS
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change)
- T2 shape: code shape vs doc 16 §Coding style (GPL header, no diagnostic print): pass — T2 – N/A: no addons-source path in patch.diff (core-only change)
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — bash: line 39:   254 Trace/breakpoint trap   (core dumped) GRAMPS_RESOURCES=. python3 -m xmlrunner discover -p "*_test.p
- T3 runtime: addon unit suites (whole-suite baseline): fail — → pip install logs (3 failure(s)): gramps-testbed-v2/test-results/install-logs/
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): fail — Generated XML report: test-results/TEST-unittest.suite._ErrorHolder-20260605210630.xml
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review — issue 11786 / tag-rename-stale-name-in-listview

Advisory, artifact-only review. Inputs available to me: `patch.diff`, `brief.md`,
`check-gates.json`. `build-notes.md` was deliberately withheld, so every Basis below
is re-derived from the diff/brief/gates, not from the builder's narrative.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | brief.md:10 states a concrete, testable success criterion (renamed tag's row shows the **new** name on the next refresh after `tag-update`, no restart). Defect, scope and repro are all pinned (brief.md:9,12,13). |
| C2 — C2 Reproduction (red pre-fix) | PASS | Re-derived from patch.diff:155-190: pre-fix `tag_updated` never drops `(tag_handle,"TAG_NAME")`, so the primed cache returns `OLD_TAG_NAME` and `assertEqual(..., NEW_TAG_NAME)` fails → red. check-gates.json confirms `red-without-fix=PASS`. Caveat carried to C4: a test that *crashes* in both states would show the same red-without-fix signature, so red-ness alone does not prove discrimination. |
| C3 — C3 Change | PASS | patch.diff:5-22 — one logical change: insert `self.model.clear_cache(tag_handle)` in `BasePersonView.tag_updated` (libpersonview.py ~535) before the backlink/`row_update` re-render. Mechanism matches the brief's root-cause site (brief.md:13) and stays inside the stated scope (brief.md:12); no color-key or treemodel redesign creep. Test files are the verification artifact, not a second logical change. |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | check-gates.json C4 (gating) = `green-with-fix=FAIL / red-without-fix=PASS`: the test did **not** turn green with the fix applied. brief.md:14 designates this interface-tier C4 as *advisory*, human sign-off carrying verification. Given the T3 core dumps (see T3 row), the green-with-fix failure may be a testbed crash rather than a logic miss — and if the test crashes in both states it discriminates nothing. A human must determine whether green-with-fix=FAIL is a real failure or environmental, since no clean red→green was demonstrated. §6 item. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | By inspection the fix is causally on-point: clearing `(tag_handle,"TAG_NAME")` (basemodel.py:46 `clear_cache`) before re-render addresses the exact stale-cache mechanism the brief names (brief.md:13). But the empirical check contradicts the theory — green-with-fix=FAIL means the fix was never observed to actually refresh the name end-to-end. Oracle is "reviewer + human sign-off"; adequacy stays unconfirmed pending human adjudication. §6 item. |
| T1 — T1 Structure | N/A | Addon-layout rules (folder==id, target_version, fname, no `__init__.py`) do not apply: patch.diff touches only core paths (`gramps/plugins/lib/...`, `gramps/gui/...`), no addons-source tree. Gate returned pass vacuously for the same reason (check-gates.json:55). |
| T2 — T2 Shape | PASS | Re-derived: the one new source file carries the full GPL header (patch.diff:33-48) and contains no diagnostic `print`/debug statements. Formal gate scoped itself N/A (no addons-source), but the substantive shape check passes on the core change. |
| T3 — T3 Runtime | FAIL | All three runtime gates fail (check-gates.json): core unit suite `Trace/breakpoint trap (core dumped)`, addon-unit `pip install` failures (3), GUI interface smoke failed. These are whole-suite *baselines* and read as testbed/environment instability (core dump + pip-install) rather than defects introduced by a one-line cache-clear; that very instability is the most likely cause of C4's green-with-fix=FAIL. Human should confirm the failures are pre-existing/infra, not patch-induced (overlaps §6). |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle, so commit-message / contributor-workflow conformance cannot be evaluated (check-gates.json:100). Nothing to check, not a failure. |
| T5 — T5 Judgment | NEEDS-HUMAN | Oracle is "reviewer + human sign-off" (check-gates.json:106). Always-human element. §6 item. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Oracle is "human at sign-off" (check-gates.json:114). Whether the fix truly satisfies the user-facing intent (new name visible on next refresh, no restart) is a fitness-to-purpose judgment reserved for the human. §6 item. |

## §6 — Items the human must clear

1. **C4 — verification did not go green.** The configured (gating) verify oracle
   reports `green-with-fix=FAIL`. brief.md:14 makes interface-tier C4 advisory, so
   this does not auto-fail the change, but no clean red→green was ever observed.
   Decide whether the failure is the testbed (see item 2) or a genuine gap.

2. **T3 / environment.** Core unit suite core-dumps (`Trace/breakpoint trap`),
   addon-unit pip-install fails, interface smoke fails. These look infra-level and
   are the prime suspect for C4's green-with-fix failure. Confirm they are
   pre-existing baseline breakage, not introduced by this patch — and confirm the
   bug-11786 test actually *discriminates* (passes with fix, fails without) when run
   in a healthy testbed, rather than crashing in both states (which would reproduce
   the observed `red-without-fix=PASS / green-with-fix=FAIL` without proving anything).

3. **C5 — causal adequacy / contested root cause.** Mechanism matches the stated
   root cause on paper, but theory and the (failed) empirical check disagree.
   Human sign-off required that `clear_cache(tag_handle)` is the complete and
   sufficient fix (and that the mirrored cache sites the brief notes —
   `citationbasemodel.py`, `eventmodel.py` — are genuinely out of scope, not just
   unaddressed).

4. **T5 — reviewer judgment.** Always-human.

5. **V — fitness-to-purpose.** Always-human: does the change satisfy the
   user-facing intent at sign-off.

## Note on scope / withheld input

`build-notes.md` was withheld by design; this review is decorrelated from the
builder's account. The one substantive divergence I can see from the brief: Do
shipped a **headless `*_test.py` companion** (which the brief invited, brief.md:14)
rather than the load-bearing GUI repro `test_bug_0011786_tag_rename_listview.py`.
That GUI test is **not present in patch.diff**. Because the companion still imports
Gtk it lands back in the advisory interface tier anyway, so it does not buy the
clean headless model-level gate the brief hoped for. Whether the missing GUI repro
is acceptable is part of the human verification sign-off (items 1–2).

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C4 — C4 Verification (red→green) — check-gates.json C4 (gating) = `green-with-fix=FAIL / red-without-fix=PASS`: the test did **not** turn green with the fix applied. brief.md:14 designates this interface-tier C4 as *advisory*, human sign-off carrying verification. Given the T3 core dumps (see T3 row), the green-with-fix failure may be a testbed crash rather than a logic miss — and if the test crashes in both states it discriminates nothing. A human must determine whether green-with-fix=FAIL is a real failure or environmental, since no clean red→green was demonstrated. §6 item.
- [x] C5 — C5 Causal adequacy — By inspection the fix is causally on-point: clearing `(tag_handle,"TAG_NAME")` (basemodel.py:46 `clear_cache`) before re-render addresses the exact stale-cache mechanism the brief names (brief.md:13). But the empirical check contradicts the theory — green-with-fix=FAIL means the fix was never observed to actually refresh the name end-to-end. Oracle is "reviewer + human sign-off"; adequacy stays unconfirmed pending human adjudication. §6 item.
- [x] T5 — T5 Judgment — Oracle is "reviewer + human sign-off" (check-gates.json:106). Always-human element. §6 item.
- [x] V — Validation — fitness-to-purpose — Oracle is "human at sign-off" (check-gates.json:114). Whether the fix truly satisfies the user-facing intent (new name visible on next refresh, no restart) is a fitness-to-purpose judgment reserved for the human. §6 item.

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
- By / date: Eduard Ralph / 2026-06-06

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
