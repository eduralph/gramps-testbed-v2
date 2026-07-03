# check-advisory-adversary.md — issue 8622 (iteration 3)

Adversarial pass. I attempted to refute the red→green evidence, the fix, and the
reviewer's framing. Line refs: unpatched code → `$PDCA_TARGET`
(`/home/eddie/gramps/gramps`, HEAD `aef9f35ec6`, branch **master**); new code →
post-image lines of `patch.diff` applied to that tree.

## The evidence

- **The bundle contains no machine red→green at all.** `check-gates.json` C4-verify is
  `fail` — `run-verify.sh: /home/eddie/gramps/gramps-6.1-lane2 has uncommitted or
  untracked changes — refusing to patch it`. The proof the brief demands was never
  produced this iteration; any reviewer claim of "verified red→green" is unwarranted on
  this bundle. I re-ran it myself in a scratch clone of `$PDCA_TARGET`: **green leg**
  5/5 pass patched; **red leg** (production hunks reverted, test kept) fails with 3
  behavioural `AssertionError`s on the node map (e.g. `[] != ['CIT_B1','CIT_B2']` under
  `SRC_BIBLE`), 1 skip (wiring test), 1 pass (standalone pin) — the red is genuinely
  behavioural, not an ImportError/TypeError (iteration-1 finding 2 is fixed). So the
  evidence design is sound, but it is **my** run on **master**, not the gate's run on
  the `maintenance/gramps61` lane the brief targets — and `po/POTFILES.skip` does not
  even apply to master HEAD (context drift; I had to `--exclude` it). The gating C4
  must be re-run on a clean 6.1 lane before the claim stands.
- Attempted to refute the tautology risk in the try/except-ImportError fallback
  (`citationtreemodel_search_test.py:280-282` post-image): could not — with production
  reverted the fallback builds the real `CitationTreeModel` and the assertions fail on
  the production node map. Also verified the test's search tuple `(False, (col, text,
  inv), False)` matches what the dialog really passes: `baseselector.py:328-334` +
  `gramps/gui/filters/_searchbar.py:178` produce exactly that shape. Not a parallel
  re-implementation.

## The fix

- NEEDS-HUMAN — **Inverted search ("does not contain") now shows the very citations the
  user excluded.** The selector's search bar offers this rule
  (`gramps/gui/filters/_searchbar.py:121`). Concrete failing case, probed on the fake
  DB: search *"does not contain 'page 10'"* — pre-fix `CitationTreeModel` shows
  `SRC_BIBLE: [CIT_B2]` (CIT_B1 "page 10" correctly hidden); post-fix
  `CitationTreeSelectorModel` shows `SRC_BIBLE: [CIT_B1, CIT_B2]` — the excluded
  citation is displayed. Cause: `_SourceGroupSearchFilter.match` (patched
  `citationtreemodel.py:320-327`) tests only source membership, so the citation-level
  negative predicate is discarded. Self-consistent under "group by source", but it
  contradicts the search bar's advertised rule for citation rows and is a behaviour
  change beyond the reported defect. Brief is silent on inverted search; human must
  decide if this is acceptable collateral.
- NEEDS-HUMAN — **Orphan guard is only half-delivered; the patch's own docstring
  overclaims it.** Docstring (patched `citationtreemodel.py:267-272`): an orphan
  citation "never triggers a `get_raw_source_data` on a missing handle during the
  search". Refuted by probe: an orphan whose **page matches** the search (e.g. orphan
  page "page 99", search "page") gets its dangling `source_handle` added to `shown`
  unconditionally (patched `citationtreemodel.py:316`), passes the secondary filter,
  and `add_row2` then dereferences the missing source →
  `HandleError: Handle SRC_GONE not found` (target
  `gramps/gui/views/treemodels/citationtreemodel.py:214-224`, `self.map(...)` at 219).
  Pre-fix crashes identically on that input, so it is **not a regression** — but
  iteration-2's sign-off demanded "guard against orphan citations in the secondary leg
  … and add a test covering the orphan case", and the added test
  (`test_selector_search_survives_orphan_citation`) covers only the *non-matching*
  orphan. Whether "no new crash path" satisfies iteration-2, and whether the docstring/
  test-docstring claims should be narrowed, is for the human.
- Attempted to refute via exact-search (`search[2]=True`, `ExactSearchFilter`,
  `treebasemodel.py:475-477` target): could not — grouped filter handles it (probe:
  exact "Holy Bible" shows both citations post-fix; pre-fix showed none, i.e. the same
  defect the fix targets).
- Attempted to refute via stale `shared["shown"]` cache (computed once per
  `set_search`, patched `citationtreemodel.py:371`): could not find a live path — the
  selector builds a **fresh** model on every Find (`baseselector.py:346-355`) and wires
  no db signals. Note only: `CitationTreeSelectorModel` is exported from
  `treemodels/__init__.py`; any future reuse in a live (signal-driven) view would
  consult a stale shown-set.

## The verdict

- The iteration-1 demand for "a selector-level test **or** AT-SPI/dogtail interface
  repro" is met only in its weakest reading: `test_selector_wiring_uses_selector_model`
  asserts `SelectCitation.get_model_class()` identity (patch.diff:534-552) but never
  drives `build_tree()`; C4-verify-interface reports "no interface repro
  engine/interface/test_bug_*8622_*.py" (`check-gates.json`, unverifiable). The wiring
  gap between `get_model_class` and the constructed model
  (`baseselector.py:347-355`) is narrow — I verified the kwargs shape by reading —
  but end-to-end dialog behaviour remains machine-unverified.
- Any acceptance rationale citing a passing C4 would be unwarranted: `overall: "fail"`;
  the only red→green in existence is this adversary's scratch run on master, not the
  target branch.

**Summary:** evidence design and core fix survive my strongest attacks (behavioural
red confirmed, production path exercised, sibling-citation and non-matching-orphan
cases hold); two refutations stand — inverted-search semantics regression
(concrete case above) and the overclaimed/half-tested orphan guard — plus the
unexecuted gating C4.
