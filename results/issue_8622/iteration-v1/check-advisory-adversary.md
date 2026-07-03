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
