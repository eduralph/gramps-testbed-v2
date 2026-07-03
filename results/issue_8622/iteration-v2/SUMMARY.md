# Result — issue 8622 / citation-selector-filter-hides-citations

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: In the "Select Source or Citation" dialog (Add Existing Citation…), the
- Success criterion: After the fix, applying a text search in the Select Source or
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: In the tree model that backs the selector, a text search applies the same

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): unverifiable — no interface repro engine/interface/test_bug_*8622_*.py for bundle issue_8622 — the per-fix GUI red→green cannot run; th
- C5 test exercises the production path (not a copy): pass — added test(s) import the production package 'gramps'

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 3 file(s) conform to doc 16 §Coding style
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [green]: green (no failures); baseline now clear (1 recorded red(s) gone) | ⚠ baseline tree drift: recorded 
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

Review task: fix issue 8622 so filtering the "Select Source or Citation" dialog keeps existing citation children reachable under any shown source instead of forcing creation of a new citation.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief defines the defect, success criterion, restored invariant, and selector-only scope: filtered selector sources must keep citation children selectable while standalone tree-view search should not regress (`brief.md:6`, `brief.md:12`, `brief.md:18`, `brief.md:27`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | I applied only the new test to an otherwise unpatched temp copy and it failed behaviourally, not by missing API: title search produced `[] != ['CIT_B1', 'CIT_B2']`, matching the test's intended fallback path (`patch.diff:385`, `patch.diff:401`). |
| C3 — C3 Change | PASS | Patch introduces a selector-specific model and wires only `SelectCitation` to it, preserving the plain `CitationTreeModel` for standalone views (`patch.diff:9`, `patch.diff:17`, `patch.diff:133`, `patch.diff:146`). |
| C4 — C4 Verification (red→green) | PASS | Gate reports green-with-fix and red-without-fix PASS (`check-gates.json:33`); I also ran the focused test in a patched temp copy with GTK 3 forced and got 4 tests OK, while the pre-fix temp copy had 2 behavioural failures and 1 skip. |
| C5 — C5 Causal adequacy | PASS | The root cause is the shared column/text building independent primary and secondary filters in target `gramps/gui/views/treemodels/treebasemodel.py:471`, and the new grouped filter keeps all citations for a shown source, including citation-driven sibling cases (`patch.diff:63`, `patch.diff:92`, `patch.diff:117`, `patch.diff:423`). |
| T1 — T1 Structure | N/A | Core-only patch; no addon layout is touched, matching the conformance gate's N/A result (`check-gates.json:59`). |
| T2 — T2 Shape | PASS | New test has the project GPL header and the added core test file is registered in `POTFILES.skip`; conformance gates also pass shape and potfiles checks (`patch.diff:208`, `patch.diff:190`, `check-gates.json:68`, `check-gates.json:77`). |
| T3 — T3 Runtime | PASS | Runtime gates report the core unit baseline matched and GUI interface smoke green, with only baseline tree-drift caveats unrelated to this patch (`check-gates.json:86`, `check-gates.json:95`). |
| T4 — T4 Contribution | N/A | Bundle contains no commit message or PR description artifact to review, and the contribution gate marks this N/A (`check-gates.json:104`). |
| T5 — T5 Judgment | PASS | The implementation follows the brief's preferred judgment call by isolating changed search semantics to the selector and pinning the standalone model's independent secondary search as unchanged (`brief.md:31`, `brief.md:35`, `patch.diff:450`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: because no per-fix dogtail GUI repro exists (`check-gates.json:41`), a human must decide whether the headless model red→green evidence is sufficient or manually clear the actual Add Existing Citation dialog UX described in §6; impact is final confidence that the live selector expands/selects as intended, not just its model. |

Target-state caveat: `$PDCA_TARGET` is readable but stale relative to `patch.diff`; it lacks `CitationTreeSelectorModel` and the new test file, and `git apply --check` fails only on drifted `po/POTFILES.skip`. I treated that as a target-state caveat, not a C4 defect, and grounded affected changed-file citations on `patch.diff`.

## §6 Human Clearance Items

1. Validation fitness-to-purpose: run Gramps with the patch applied, open a person, go to Source Citations, choose Add Existing Citation..., search for text matching a source title, click Find, expand the matching source, and confirm an existing citation row is visible and selectable without creating a new citation. Also search for text matching one citation page and confirm sibling citations under that shown source remain reachable.

### Advisory — adversary

# Adversarial review — issue 8622 (citation-selector-filter-hides-citations)

Advisory only; never gates. Ground: `$PDCA_TARGET=/home/eddie/gramps/gramps` (read-only).

## Refutation attempts that FAILED (the fix held)

I tried hard to break the red→green story and the core logic, and could not:

- **Tautology check — refuted.** Traced the pre-fix behaviour of the fallback in
  `citationtreemodel_search_test.py:391` (`model_class = CitationTreeSelectorModel or CitationTreeModel`).
  With the fix reverted the test builds the plain `CitationTreeModel` and, for a `"Bible"` title
  search, the base secondary filter (`treebasemodel.py:480` `SearchFilter(func2, ...)` on the page
  column via `citationtreemodel.py:153` `citation_page`) drops both Bible citations, so
  `test_selector_keeps_citations_of_title_matched_source` fails on an empty child list — a genuine
  **behavioural** `AssertionError`, not the iteration-1 `TypeError`. Iteration-1 finding 2 is closed.
- **Production-path fidelity — refuted.** The search tuple `(False,(col,text,inv),False)` the test
  feeds matches exactly what the real dialog builds: `baseselector.py:328-334` reshapes
  `search_bar.get_value()` into `(flag, (col,text,inv), exact)` and `baseselector.py:347-355`
  constructs the model with `search=filter_info`. The filter `.match(handle, db)` contract
  (`_searchfilter.py:31`) and `_get_value`/`map2` wiring (`treebasemodel.py:961`) are the real ones.
- **Invariant completeness — refuted.** The citation-driven parent case (source pulled in only
  because a child citation matched) keeps its siblings: `_SourceGroupSearchFilter._source_shown`
  (patch.diff:108-115) unions title-match with `_sources_with_matching_citation`, and the secondary
  leg maps every citation to its parent source (patch.diff:117-125). Grouping is column-agnostic, so
  it holds for ID/author searches too. Iteration-1 finding 3 is addressed; the standalone view is
  pinned unchanged by `test_standalone_model_keeps_independent_secondary_search`.

## Findings a human should adjudicate

- **NEEDS-HUMAN — Patch baseline ≠ `$PDCA_TARGET`; the green evidence was demonstrated on a
  different tree.** The brief targets `maintenance/gramps61`, but `$PDCA_TARGET` is checked out on
  `master` (`git log`: `aef9f35ec6 "Gramps is still using GTK3"`), and the fix is **not present**
  there: `citationtreemodel.py` ends at line 235 (no `CitationTreeSelectorModel`),
  `selectcitation.py:40,67` still import/return `CitationTreeModel`, and
  `__init__.py:34` has no selector-model export. Worse, the POTFILES.skip hunk
  (`patch.diff:194-200`) uses a trailing context line
  `gramps/gui/views/treemodels/test/treebasemodel_test.py` that **does not exist** in the target —
  target `po/POTFILES.skip:456` has only `node_test.py` and the test dir contains only
  `__init__.py`/`node_test.py`. So that hunk will not apply cleanly to `$PDCA_TARGET`, and the
  C4/T2 "pass" rows in `check-gates.json` were produced against a tree that differs from the one
  under review (the gate itself flags "baseline tree drift: recorded detached@674e3b"). The
  reviewer's acceptance of C4/T2 as target-grounded is not warranted until the patch is confirmed to
  apply and re-run on this checkout.

- **NEEDS-HUMAN — The fix widens the secondary-filter crash surface to orphan citations.**
  Pre-fix, deciding a citation row touches only citation data (`citation_page`), and the parent
  source is loaded (`self.map(data.source_handle)`, `citationtreemodel.py:219`) **only** for
  citations that already passed the page filter. Post-fix, the secondary leg routes **every**
  citation through `_citation_source_handle` → `map2(handle).source_handle` → `source_filter.match`
  → `map(source_handle)` (patch.diff:117-125, 187-189). A citation with a dangling/deleted
  `source_handle` therefore triggers `get_raw_source_data` on a missing handle **during search**,
  regardless of whether its page matched — a `HandleError` path that pre-fix search never hit for
  non-matching citations. The fake DB (`citationtreemodel_search_test.py:310`, 3 clean rows, no
  orphans) cannot exercise this; a source/citation integrity test should.

- **NEEDS-HUMAN — Wiring (dialog→model) is asserted only in the green leg; nothing drives
  `build_tree` end-to-end.** `test_selector_wiring_uses_selector_model`
  (`citationtreemodel_search_test.py:479-480`) `skipTest`s whenever `CitationTreeSelectorModel` is
  absent, i.e. exactly in the C4 full-revert red leg — a skip is not a red. The behavioural tests
  import the model class directly and never call `SelectCitation.get_model_class` or
  `baseselector.build_tree`. Combined with `check-gates.json` C4-verify-interface =
  `unverifiable` (no dogtail repro), **no test exercises the real dialog build path**. A
  `get_model_class` typo is caught only because the green run would fail its `assertIs`; the brief's
  claim that iteration-1 finding 1 ("selector wiring untested") is *closed* is only partially true —
  it is guarded going forward but never proven via red→green.

## Advisory (non-blocking) note

- **Performance regression the row-count masks.** For a search matching no source title,
  `_sources_with_matching_citation` (patch.diff:92-106) scans the entire citation cursor once, and
  the secondary leg then does a source lookup per citation. On a real tree with thousands of
  citations this is a full extra table scan + per-row source fetch per keystroke-search; the 3-row
  fake DB cannot reveal it. Grouping correctness is fine — only the cost is untested.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] V — Validation — fitness-to-purpose — DECISION OWED: because no per-fix dogtail GUI repro exists (`check-gates.json:41`), a human must decide whether the headless model red→green evidence is sufficient or manually clear the actual Add Existing Citation dialog UX described in §6; impact is final confidence that the live selector expands/selects as intended, not just its model.
- [ ] C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail) unverifiable — no interface repro engine/interface/test_bug_*8622_*.py for bundle issue_8622 — the per-fix GUI red→green cannot run; th

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: iterated-to-Do
- Iteration delta (if iterating): The new secondary filter leg in _SourceGroupSearchFilter routes every citation through _citation_source_handle → map2(handle).source_handle → source_filter.match → map(source_handle), meaning a citation with a dangling/deleted source_handle will trigger get_raw_source_data on a missing handle during search — a HandleError path that pre-fix code never hit for non-matching citations. The fake DB in the test (3 clean rows, no orphans) cannot exercise this. The fix must guard against orphan citations in the secondary leg (e.g. catch HandleError / check handle existence before dereferencing) and add a test covering the orphan case.
- By / date: Eduard Ralph / 2026-07-02

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
