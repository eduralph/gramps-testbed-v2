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
- C5 test exercises the production path (not a copy): unverifiable — test file(s) add no import of the production package 'gramps' — may exercise a copy, not production: gramps/gui/views/tr

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

Reviewing issue 8622: searched "Select Source or Citation" results must keep existing citation children reachable under matched source rows.

Target caveat: `$PDCA_TARGET` is readable but on `master` (`aef9f35ec6`) rather than the brief's `maintenance/gramps61`; the Python hunks apply cleanly, but `po/POTFILES.skip` context is stale, so changed-line citations below are grounded on `patch.diff` where necessary.

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | The brief defines the defect and success criterion: search currently hides citation children and must keep them expandable/selectable under a matched source (`brief.md:6`, `brief.md:12`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The unpatched target builds independent primary/secondary text filters from the same column/text, which reproduces the child-drop condition for source-title searches (`/home/eddie/gramps/gramps/gramps/gui/views/treemodels/treebasemodel.py:471`). |
| C3 — C3 Change | PASS | The patch scopes the behavior to the citation selector by adding selector model kwargs and passing `match_child_via_parent=True`, while default model behavior remains opt-in (`patch.diff:20`, `patch.diff:36`, `patch.diff:102`). |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | DECISION OWED: in a correctly provisioned Gramps 6.1 lane, confirm the new focused test runs red before and green after; local run reached import setup but aborted on GTK/API environment mismatch (`Gtk.IconSize.MENU`) before assertions. |
| C5 — C5 Causal adequacy | PASS | The wrapper retains a citation if either the citation filter matches or the parent source filter matches, directly addressing the same-column secondary-filter cause (`patch.diff:80`, `patch.diff:137`). |
| T1 — T1 Structure | N/A | Core-only change with no addon layout surface, matching the gate's N/A assessment (`check-gates.json:60`). |
| T2 — T2 Shape | PASS | Added Python test has GPL header and the new core test is registered in `POTFILES.skip`; `git diff --check` on the patched temp clone produced no whitespace errors (`patch.diff:153`, `patch.diff:375`). |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: runtime health must be judged in a valid lane because configured unit/interface gates failed before producing JUnit, and my focused retry was blocked by local GTK/resource setup rather than a test assertion (`check-gates.json:87`). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present in this review bundle, so contribution-wrapper review does not apply (`check-gates.json:105`). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: accept whether the selector-only opt-in is the right product boundary, since the brief calls the selector-vs-shared-model locus a judgment call and the patch intentionally preserves standalone tree-view search semantics (`brief.md:35`, `patch.diff:187`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: a human must validate the actual GUI workflow preserves the intended user outcome: after searching, an existing citation can be selected rather than forcing new citation creation (`brief.md:12`). |

## §6 Human Clearance Items

1. C4: On a correct `maintenance/gramps61` lane, apply the patch and run `python3 -m unittest gramps.gui.views.treemodels.test.citationtreemodel_search_test`; clear only if the new selector test fails on the unpatched baseline and passes with the patch.
2. T3: Rerun the configured core unit and GUI smoke gates in a provisioned lane; clear only if failures are unrelated baseline/tooling failures or the patched tree-model path passes.
3. T5: Decide whether selector-only `match_child_via_parent=True` is the intended scope, leaving standalone Citation Tree View searches unchanged.
4. V: Manually exercise Gramps: open a person, go to Source Citations, choose Add Existing Citation, search for a source, expand the matched source, and confirm an existing citation child is selectable and added without creating a new citation.

### Advisory — adversary

# check-advisory-adversary.md — issue 8622 (citation-selector-filter-hides-citations)

Adversarial pass. Target grounded at `$PDCA_TARGET` = /home/eddie/gramps/gramps (checkout is on
`master`; the patch targets `maintenance/gramps61` and was verified against that branch content).

## Refutations / findings

- **The asserted red→green evidence does not exist in the gates.** `check-gates.json` C4
  (`C4-verify`, gating) is **fail** — `run-verify.sh` never ran ("core worktree
  /home/eddie/gramps/gramps-6.1-lane2 missing"), C5 is unverifiable, T3 crashed pre-test, and
  `overall` is `fail`. Any claim that the fix is "verified red→green" is unwarranted on this
  bundle as it stands. I re-ran the proof independently on `maintenance/gramps61`
  (patch applies cleanly there; it does **not** apply on `master` — `po/POTFILES.skip` context
  differs, master:456 lacks the `treebasemodel_test.py` line present at gramps61:486-487):
  pre-fix the new test errors, post-fix both tests pass, and sibling tests
  (`node_test`, `treebasemodel_test`) stay green. So the fix is verifiable — but the harness
  evidence must be regenerated on the gramps61 worktree before sign-off.

- **The red is tautological in character.** Pre-fix, `test_selector_keeps_citations_of_matched_source`
  fails with `TypeError: unexpected keyword argument 'match_child_via_parent'`
  (patch.diff:318-323 → test file line ~166) — any test of a new API is red this way; it does not
  observe the defect on the pre-fix production path. Mitigation: the companion
  `test_default_search_drops_citations` pins the defective same-column semantics
  (children `[]` under a matched source), so the *pair* does demonstrate the semantic delta.
  I confirmed the assertion flips with the production change (not a copy): the test imports
  production via `from ..citationtreemodel import CitationTreeModel` — the C5 gate's
  "no import of package 'gramps'" is a false alarm of its import-string heuristic.

- NEEDS-HUMAN — **The selector wiring is exercised by no test and no interface repro.** The GUI-facing
  half of the fix — `**self.get_model_kwargs()` in `gramps/gui/selectors/baseselector.py` `build_tree`
  (target :347-355 pre-patch) and the `SelectCitation.get_model_kwargs` override
  (`gramps/gui/selectors/selectcitation.py:66` region) — is covered by nothing: the C4 test constructs
  `CitationTreeModel(..., match_child_via_parent=True)` directly, and `C4-verify-interface` is
  unverifiable ("no interface repro engine/interface/test_bug_*8622_*.py"). Concrete failing case: a
  typo/rename of `get_model_kwargs` (or dropping the `**` splice) keeps every test green while the
  user-visible bug persists in the dialog. A dogtail repro or a small selector-level test would close this.

- NEEDS-HUMAN — **The brief's invariant is only partially restored.** Invariant: "if a source is
  shown, its citations remain selectable." Empirically on the patched gramps61 model: a selector
  search matching only a citation page (`"p.10"`) forces the parent source into the tree via the
  `add_row2` fallback (`gramps/gui/views/treemodels/citationtreemodel.py:214-224` on target), yet the
  sibling citation (`p.20`) stays unreachable under that *shown* source — children = `['CIT_B1']`
  only. This is identical to pre-fix behaviour (no regression), and matches the reported defect's
  direction (source-title search), but any Check claim that the invariant is restored *as stated* is
  over-broad: it holds only for parents kept by the primary match, not for child-driven parents.
  Human to decide whether that residual case is in scope or acceptable.

- **Standalone-test bootstrap is fragile (ties to the T3 fail).** Run standalone
  (`python3 -m unittest gramps.gui.views.treemodels.test.citationtreemodel_search_test`) on a
  dual-GTK system, gi resolves Gtk 4.0 and the import chain crashes at
  `gramps/gui/widgets/buttons.py:50` (`Gtk.IconSize.MENU`) before any test runs — the docstring's
  "runs headless" claim holds only with GTK 3 pinned first. Same pre-existing pattern as the
  sibling tests (not introduced by this diff), but note T3's "GI bootstrap" pre-test crash is
  consistent with this; whole-suite evidence must be regenerated regardless.

## Attempted and could not refute

- Exact search (`search[2]`), inverted ("does not contain") search, empty search text, and the
  sidebar GenericFilter path (`search[0]` truthy → wrapper skipped, `citationtreemodel.py` patched
  `set_search` guard) all behave consistently in empirical probes on the patched model.
- Standalone Citation Tree View regression: default `match_child_via_parent=False` leaves
  `TreeBaseModel.set_search` semantics untouched; pinned by the second test; `node_test` and
  `treebasemodel_test` pass post-patch. Other selectors get `get_model_kwargs() == {}` — no collision.
- `skip`-list handling: checked before the wrapper in `treebasemodel.py:569-571`; the wrapper cannot
  resurrect skipped handles.
- `map2(handle).source_handle` in the wrapper matches production raw-data attribute access
  (`add_row2` uses `data.source_handle`, `citationtreemodel.py:214` on target).
- Noted but not filed (pre-existing, untouched, unreachable from the selector): `set_search(None)`
  with a secondary model crashes at `treebasemodel.py:491` (`search[2]` on `None`); the selector's
  `build_tree` always passes a tuple.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C4 — C4 Verification (red→green) — DECISION OWED: in a correctly provisioned Gramps 6.1 lane, confirm the new focused test runs red before and green after; local run reached import setup but aborted on GTK/API environment mismatch (`Gtk.IconSize.MENU`) before assertions.
- [ ] T3 — T3 Runtime — DECISION OWED: runtime health must be judged in a valid lane because configured unit/interface gates failed before producing JUnit, and my focused retry was blocked by local GTK/resource setup rather than a test assertion (`check-gates.json:87`).
- [ ] T5 — T5 Judgment — DECISION OWED: accept whether the selector-only opt-in is the right product boundary, since the brief calls the selector-vs-shared-model locus a judgment call and the patch intentionally preserves standalone tree-view search semantics (`brief.md:35`, `patch.diff:187`).
- [ ] V — Validation — fitness-to-purpose — DECISION OWED: a human must validate the actual GUI workflow preserves the intended user outcome: after searching, an existing citation can be selected rather than forcing new citation creation (`brief.md:12`).
- [ ] **The selector wiring is exercised by no test and no interface repro.** The GUI-facing
- [ ] **The brief's invariant is only partially restored.** Invariant: "if a source is
- [ ] C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail) unverifiable — no interface repro engine/interface/test_bug_*8622_*.py for bundle issue_8622 — the per-fix GUI red→green cannot run; th
- [ ] C5 test exercises the production path (not a copy) unverifiable — test file(s) add no import of the production package 'gramps' — may exercise a copy, not production: gramps/gui/views/tr

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
- Iteration delta (if iterating): Three adversarial findings require improvement before acceptance: 1. Selector wiring untested: the C4 test constructs CitationTreeModel directly and never exercises baseselector.py or selectcitation.py. A typo in get_model_kwargs() or a dropped ** in build_tree keeps all tests green while the user-visible bug persists in the dialog. A selector-level test or AT-SPI/dogtail interface repro is needed to close this gap. 2. Tautological pre-fix red: test_selector_keeps_citations_of_matched_source fails pre-fix with TypeError (unexpected keyword argument) rather than a semantic assertion about the defect. The companion test test_default_search_drops_citations partially mitigates this, but the primary C4 test should fail because of the wrong behaviour, not because the API does not exist yet. 3. Invariant only partially restored: the brief states "if a source is shown, its citations remain selectable." The fix holds for source-driven parents (source title matches search) but citation-driven parents (citation page matches, source forced in via add_row2 fallback) still leave sibling citations unreachable. The brief's invariant as stated is over-broad relative to what the patch delivers; either the fix must be extended to cover the citation-driven case or the brief/invariant must be narrowed to explicitly exclude it.
- By / date: Eduard Ralph / 2026-07-02

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
