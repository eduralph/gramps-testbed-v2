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
- C4 fix verified: test red pre-fix, green post-fix: fail — run-verify.sh: /home/eddie/gramps/gramps-6.1-lane2 has uncommitted or untracked changes — refusing to patch it
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

Reviewing issue 8622: filtered "Select Source or Citation" searches must keep existing citation children reachable under any source retained by the selector search.

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | The brief defines the defect and success criterion as keeping citation children reachable under a matched source in the selector search, while preserving standalone tree-view behavior (`brief.md:6`, `brief.md:12`, `brief.md:31`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The added test is constructed to fall back to pre-fix `CitationTreeModel` and fail on the semantic child-row assertion rather than on a missing symbol (`patch.diff:276`, `patch.diff:416`, `patch.diff:433`). |
| C3 — C3 Change | PASS | The patch routes only `SelectCitation` to `CitationTreeSelectorModel`, leaving the plain `CitationTreeModel` available for standalone views (`patch.diff:9`, `patch.diff:17`, `patch.diff:146`). |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | DECISION OWED: the automated C4 gate did not verify behavior because its runner refused a dirty/untracked lane (`check-gates.json:33`), and my temporary rerun was blocked by the available `$PDCA_TARGET` being `master` plus a GTK import mismatch before tests executed; human must rerun the focused red→green test on a clean `maintenance/gramps61` target to clear verification. |
| C5 — C5 Causal adequacy | PASS | The existing root cause is secondary search using the same column/text independently for citation rows (`gramps/gui/views/treemodels/treebasemodel.py:467`, `gramps/gui/views/treemodels/treebasemodel.py:472`, `gramps/gui/views/treemodels/treebasemodel.py:480`), and the patch groups selector search by source for both primary and secondary rows (`patch.diff:63`, `patch.diff:181`, `patch.diff:190`). |
| T1 — T1 Structure | N/A | Core-only patch; no addon structure is touched, matching the gate's N/A result (`check-gates.json:60`). |
| T2 — T2 Shape | PASS | The new test has the project GPL header and the new core Python test is registered in `po/POTFILES.skip` in the patch (`patch.diff:211`, `patch.diff:557`); target `master` has a different `POTFILES.skip` layout, so that hunk's local apply miss is target-state drift. |
| T3 — T3 Runtime | PASS | The configured broader runtime gates report the core unit baseline and GUI smoke as passing or baseline-matching, with noted baseline drift not attributed to this patch (`check-gates.json:87`, `check-gates.json:96`). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present in this check bundle, so contribution-wrapper review does not apply (`check-gates.json:105`). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: the patch intentionally widens selector text search so a citation-page match exposes all sibling citations under that source (`patch.diff:63`, `patch.diff:455`); human must decide that this grouped selector behavior is the desired scope tradeoff and not an over-broad selector result. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: fitness requires a human/manual confirmation that the actual dialog lets a searched source expand and select an existing citation instead of creating a new one, because no GUI per-fix repro exists in the bundle (`check-gates.json:42`). |

§6 Human Clearances

1. C4 verification: rerun the focused regression on a clean `maintenance/gramps61` target with the patch applied, including the red pre-fix and green post-fix legs for `gramps.gui.views.treemodels.test.citationtreemodel_search_test`.
2. T5 judgment: confirm that selector search should group by source and expose sibling citations when any citation under that source matches the search text.
3. Validation fitness: manually open Source Citations -> Add Existing Citation..., search for a source title, click Find, expand the retained source, and confirm an existing citation child can be selected without creating a new citation.

### Advisory — adversary

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

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C4 — C4 Verification (red→green) — DECISION OWED: the automated C4 gate did not verify behavior because its runner refused a dirty/untracked lane (`check-gates.json:33`), and my temporary rerun was blocked by the available `$PDCA_TARGET` being `master` plus a GTK import mismatch before tests executed; human must rerun the focused red→green test on a clean `maintenance/gramps61` target to clear verification.
- [ ] T5 — T5 Judgment — DECISION OWED: the patch intentionally widens selector text search so a citation-page match exposes all sibling citations under that source (`patch.diff:63`, `patch.diff:455`); human must decide that this grouped selector behavior is the desired scope tradeoff and not an over-broad selector result.
- [ ] V — Validation — fitness-to-purpose — DECISION OWED: fitness requires a human/manual confirmation that the actual dialog lets a searched source expand and select an existing citation instead of creating a new one, because no GUI per-fix repro exists in the bundle (`check-gates.json:42`).
- [ ] **Inverted search ("does not contain") now shows the very citations the
- [ ] **Orphan guard is only half-delivered; the patch's own docstring
- [ ] C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail) unverifiable — no interface repro engine/interface/test_bug_*8622_*.py for bundle issue_8622 — the per-fix GUI red→green cannot run; th
- [ ] C4 fix verified: test red pre-fix, green post-fix FAILED (gating) — run-verify.sh: /home/eddie/gramps/gramps-6.1-lane2 has uncommitted or untracked changes — refusing to patch it

## 7. Proven / not proven
- Proven by which oracle: gates overall = fail (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: iterated-to-Do
- Iteration delta (if iterating): Two substantive fixes required in CitationTreeSelectorModel: 1. Inverted-search regression: _SourceGroupSearchFilter.match must not discard the citation-level predicate for negative/inverted searches ("does not contain"). When the search rule is inverted, a citation whose page matches the exclusion term must not be shown — grouping by source cannot override the citation-level filter result. Fix the match logic so the citation-level predicate is applied before adding to the shown set. 2. Orphan guard half-delivered: an orphan citation whose page matches the search text currently gets its dangling source_handle added to shown unconditionally, causing HandleError in add_row2. The guard must cover the matching-orphan case (skip or safely handle citations with missing source handles) and a test must cover this path. "No new crash path" does not satisfy the iteration-2 requirement for a guard; the matching-orphan case must be explicitly handled and tested. Note: the C4 lane (gramps-6.1-lane2) is now clean — the dirty-worktree blocker is resolved for the next run.
- By / date: Eduard Ralph / 2026-07-02

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
