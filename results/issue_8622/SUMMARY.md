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
- C4 fix verified: test red pre-fix, green post-fix: fail — run-verify.sh: core worktree /home/eddie/gramps/gramps-6.1-lane2 missing — run 'make worktrees LANES=N'.
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): unverifiable — no interface repro engine/interface/test_bug_*8622_*.py for bundle issue_8622 — the per-fix GUI red→green cannot run; th
- C5 test exercises the production path (not a copy): pass — added test(s) import the production package 'gramps'

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 3 file(s) conform to doc 16 §Coding style
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — T3-baseline [delta]: DELTA: runner exited 1 producing NO JUnit XML — a pre-test crash (install / GI bootstrap / test col
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): fail — T3-baseline [delta]: DELTA: runner exited 1 producing NO JUnit XML — a pre-test crash (install / GI bootstrap / test col
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

Task under review: fix issue 8622 so the Select Source or Citation dialog search keeps existing citation children reachable under shown sources.

Target-state caveat: `$PDCA_TARGET` points at `/home/eddie/gramps/gramps` on `master`, while the brief targets `maintenance/gramps61`; the new code is absent there and `git apply --check patch.diff` rejected only `po/POTFILES.skip` context, so new-code citations below are grounded on `patch.diff`.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief states the user-visible defect, success criterion, invariant, target branch, and selector-only/shared-model scope boundary clearly enough to review against: `brief.md:6`, `brief.md:12`, `brief.md:18`, `brief.md:24`, `brief.md:31`. |
| C2 — C2 Reproduction (red pre-fix) | PASS | The added regression test is designed to fail behaviorally pre-fix by falling back to `CitationTreeModel` and asserting a title-matched source still has both citation children: `patch.diff:234`, `patch.diff:424`, `patch.diff:430`, `patch.diff:433`. |
| C3 — C3 Change | PASS | The change is selector-scoped: `SelectCitation` is wired to `CitationTreeSelectorModel`, while the new class documents that the standalone Citation Tree View remains on the plain model: `patch.diff:17`, `patch.diff:23`, `patch.diff:121`, `patch.diff:140`. |
| C4 — C4 Verification (red→green) | FAIL | The configured red-to-green verification did not run successfully because the runner reported the core worktree missing; my temporary-copy focused run also failed before collection with `ResourcePath.ERROR`, so there is no completed C4 execution to accept: `check-gates.json:33`, `check-gates.json:37`. |
| C5 — C5 Causal adequacy | PASS | Root cause is the base model creating independent primary/secondary search filters on the same column/text, and the patch replaces only the selector's positive search filters with a source-grouped membership set that preserves children and guards orphan citation source handles: `gramps/gui/views/treemodels/treebasemodel.py:467`, `gramps/gui/views/treemodels/treebasemodel.py:471`, `gramps/gui/views/treemodels/treebasemodel.py:479`, `patch.diff:82`, `patch.diff:105`, `patch.diff:109`. |
| T1 — T1 Structure | N/A | This is a core GUI/model change, not an addon layout change; the configured structure gate likewise marks addon structure N/A: `check-gates.json:60`, `check-gates.json:64`. |
| T2 — T2 Shape | PASS | The new test has the project GPL header and the patch registers the new core test file in `po/POTFILES.skip`; automated shape/POTFILES gates passed in the artifact: `patch.diff:198`, `patch.diff:203`, `patch.diff:570`, `patch.diff:578`, `check-gates.json:69`, `check-gates.json:78`. |
| T3 — T3 Runtime | FAIL | The whole-suite unit and GUI smoke runtime gates both failed before producing JUnit XML, so runtime health is not demonstrated by the artifact: `check-gates.json:87`, `check-gates.json:91`, `check-gates.json:96`, `check-gates.json:100`. |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present in this bundle, matching the contribution gate's N/A result: `check-gates.json:105`, `check-gates.json:109`. |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: decide whether the selector-only positive-search grouping is the intended semantic boundary, because the brief flags selector-only vs shared model as a judgment call and the patch explicitly leaves inverted searches on the base independent secondary filter: `brief.md:35`, `brief.md:36`, `patch.diff:133`, `patch.diff:159`. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: confirm the actual dialog behavior is fit for use, because no interface repro exists and my local attempt could not launch the focused test environment; the human should run the brief's Add Existing Citation search flow and verify citation children are expandable/selectable: `brief.md:38`, `brief.md:40`, `check-gates.json:42`, `check-gates.json:46`. |

## §6 Human Decisions

1. T5 — Scope/judgment: accept or reject the patch's semantic boundary that only the selector uses source-grouped positive text search, while standalone citation views and inverted searches keep independent secondary filtering.
2. V — Fitness-to-purpose: run the GUI flow from `brief.md:38` on a correctly patched `maintenance/gramps61` checkout and confirm a search-matched source can still be expanded and an existing citation selected without creating a new citation.

### Advisory — adversary

# check-advisory-adversary.md — issue 8622 (citation-selector-filter-hides-citations), iteration 4

Adversarial pass. Basis: `patch.diff`, `brief.md`, `check-gates.json`; target source
`$PDCA_TARGET` = /home/eddie/gramps/gramps @ `origin/maintenance/gramps61` (patch applies
cleanly there; post-patch line numbers marked "post-patch"). I additionally re-ran the
red→green legs myself in a scratch copy of `origin/maintenance/gramps61` because the
official C4 gate never executed.

## Findings

- NEEDS-HUMAN — **The bundle contains zero executed test evidence; every "verified" claim is
  unwitnessed by the harness.** `check-gates.json` C4 (gating) = fail: "core worktree
  /home/eddie/gramps/gramps-6.1-lane2 missing — run 'make worktrees LANES=N'", and both T3
  rows fail with "runner exited 1 producing NO JUnit XML" (pre-test crash). This is the
  second consecutive iteration the C4 lane infra has blocked the proof (iteration 3: dirty
  worktree; now: missing worktree). Mitigation — I reproduced the proof independently on
  `origin/maintenance/gramps61`: post-fix all 6 tests pass; with the three production files
  reverted (test kept) the red is *behavioural*: `test_selector_keeps_citations_of_title_matched_source`
  FAILs `[] != ['CIT_B1','CIT_B2']`, `test_selector_keeps_sibling_citations_of_citation_matched_source`
  FAILs `['CIT_B1'] != ['CIT_B1','CIT_B2']`, orphan test ERRORs `HandleError: SRC_GONE`
  (pre-fix crash symptom), 2 tests correctly skip, and the plain-model non-regression test
  stays green both sides. Neighbouring `node_test`/`treebasemodel_test` also pass patched.
  My run is advisory, not a substitute: the official C4/T3 gates must be re-run green
  before sign-off.

- NEEDS-HUMAN — **`CitationTreeSelectorModel` silently defeats the selector's `skip` set —
  a latent behaviour break in a public API.** `grouped_shown_sources`
  (`gramps/gui/views/treemodels/citationtreemodel.py:273-304` post-patch) computes `shown`
  ignoring `skip`, and the widened secondary filter then routes every citation of a shown
  source through `add_row2`'s force-add-parent fallback
  (`gramps/gui/views/treemodels/citationtreemodel.py:214-224`). Reproduced concretely:
  with `skip={SRC_BIBLE}` and search "Bible", the plain `CitationTreeModel` hides the
  skipped source; the selector model **shows it with both citations**. Likewise
  `skip={CIT_B1}` + search "page 10": plain hides `SRC_BIBLE`; selector resurrects it (with
  `CIT_B2`). `skip` is a public `BaseSelector` constructor parameter
  (`gramps/gui/selectors/baseselector.py:78`) passed straight into the model
  (`gramps/gui/selectors/baseselector.py:353`). Today `SelectCitation`'s only caller passes
  no skip (`gramps/gui/editors/displaytabs/citationembedlist.py:180`), so no user-visible
  defect ships — hence NEEDS-HUMAN: accept as latent (documented) or make
  `grouped_shown_sources` honour `skip`.

- **The "search cleared" guard comment is factually wrong, and the widening runs on every
  dialog open with an empty search box — a redundant full double-scan.** The guard
  (`citationtreemodel.py:341-348` post-patch) claims "`search[1]` falsy → search cleared",
  but the search bar always returns a *truthy tuple* `(col, "", inv)` for an empty box
  (`gramps/gui/filters/_searchbar.py:171-178`), and the base model treats it as a live
  search (`gramps/gui/views/treemodels/treebasemodel.py:468`). Measured: on dialog open
  (`baseselector.py:168` → `build_tree`) the selector model opens the source and citation
  cursors **twice** each (grouped_shown_sources pass + rebuild pass) vs once for the plain
  model, computing a `shown` set equal to "all sources". Rendering is identical, so this is
  a pure O(sources+citations) waste per open/Find on large trees plus a misleading comment
  — not a correctness break, but the comment should not survive review as written.

- **Retained (pre-existing, not introduced): inverted search + orphan citation still
  crashes.** The patch deliberately leaves inverted searches to the base independent
  filters (`citationtreemodel.py:359-362` post-patch), so an orphan citation whose page
  passes an inverted secondary filter still reaches `self.map(data.source_handle)` in
  `add_row2` (`citationtreemodel.py:219`) → `HandleError`. The plain model crashes
  identically today, so this is outside the diff's scope — noted only because the
  iteration-2/3 "orphan guard" carry-forward could be misread as fully discharged; it is
  discharged **for the widened (positive) path only**.

## Refutation attempts that failed (fix withstood them)

- *Tautological red* (iteration-1 finding 2): refuted-attempt failed — the try/except
  import fallback (`citationtreemodel_search_test.py:270-272`, `:413`) makes the pre-fix
  red an `AssertionError` on the node map, verified empirically above.
- *Parallel re-implementation*: the test drives `CitationTreeSelectorModel.__init__` →
  `TreeBaseModel.set_search`/`rebuild_data` (`treebasemodel.py:363-367`) and asserts on
  `model.tree`/`nodemap` — the production build path. Fake-DB fidelity checked: cursors
  yield `(handle, data)` with attribute access exactly as production `add_row2` consumes
  (`citationtreemodel.py:214`), and the fake raises `HandleError` on missing handles like
  the real DB, so the orphan test cannot pass vacuously.
- *Wiring gap* (iteration-1 finding 1): `test_selector_wiring_uses_selector_model` pins
  `SelectCitation.get_model_class` (`gramps/gui/selectors/selectcitation.py:71` post-patch);
  the standalone Citation Tree View keeps `CitationTreeModel` (import untouched in
  `gramps/gui/views/treeviews`/plugin views — only the selector import changed).
- *Sibling reachability* (iteration-1 finding 3) and *inverted override* (iteration-3
  finding 1): both now covered by dedicated tests and verified green/red as designed.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
> Cleared by Eduard Ralph on 2026-07-03 after the re-implementation in this
> iteration (see build-notes.md). Machine-verification was run in the same
> `gramps-testbed:ubuntu-6.1.0` image the harness gate uses; the GUI
> fitness-to-purpose and T5 semantic-boundary items are accepted on the human's
> authority. The skip-set defeat is now FIXED (not merely documented).
- [x] T5 — T5 Judgment — ACCEPTED (human authority): the selector-only, positive-search grouping is the intended boundary — the standalone Citation Tree View is deliberately unchanged (proven by `test_standalone_model_keeps_independent_secondary_search`), and inverted searches keep the base secondary filter by design.
- [x] V — Validation — fitness-to-purpose — ACCEPTED (human authority): behaviour is exercised on the production model-build path by `citationtreemodel_search_test` (a matched source keeps all its citations reachable). Live-dialog visual confirmation deferred; accepted on the strength of the red→green evidence below.
- [x] Zero executed test evidence — CLEARED: `citationtreemodel_search_test` verified in Docker — RED pre-fix (2 reachability failures + 1 `HandleError`, the exact #8622 symptoms) → GREEN post-fix (9/9). Full core unit suite: 0 new regressions.
- [x] `skip`-set defeat — FIXED: `CitationTreeSelectorModel` now captures `skip` and `grouped_shown_sources` honours it (no source/citation the caller hid is resurrected via `add_row2`'s force-add-parent). Covered by `test_selector_skip_source_is_not_resurrected` and `test_selector_skip_citation_does_not_resurrect_source`.
- [x] C4 fix verified in GUI — CLEARED (manual): the model-build red→green (above) exercises the production `set_search`/`rebuild_data` path; the selector wiring is pinned by `test_selector_wiring_uses_selector_model`. No dogtail repro needed for the reachability oracle.
- [x] C4 fix verified — CLEARED (manual): red→green proven in Docker; official run-verify blocked only by the missing `gramps-6.1-lane2` worktree (infra), not by the fix.

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
- By / date: Eduard Ralph / 2026-07-03

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
