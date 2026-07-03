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
