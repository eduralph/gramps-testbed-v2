# Result — issue 13716 / sidebar-filter-type-list-stale

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: A view's sidebar filter "Type" selector (the same widget the Filter
- Success criterion: After a custom type is added to the already-open database
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61   (core fix → current maintenance line, forward-merged to master; INTEGRATION §2)
- Scope (one logical fix) / out of scope: make the sidebar-filter Type selectors present the database's current

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify[6.1]: PASS-ON-ESSENTIAL — fix is correct but depends on an essential fix (see essential-dependency.json)
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): unverifiable — no interface repro engine/interface/test_bug_*13716_*.py for bundle issue_13716 — the per-fix GUI red→green cannot run; 
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 9 file(s) conform to doc 16 §Coding style (1 advisory)
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [green]: green (no failures); baseline now clear (1 recorded red(s) gone) | ⚠ baseline tree drift: recorded 
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review — issue 13716 / sidebar-filter-type-list-stale

**Reviewer:** Check (advisory, decorrelated from builder)
**Artifacts read:** `patch.diff`, `brief.md`, `check-gates.json`
**Build-notes:** withheld (not available to this reviewer)

---

## §1 Verdict table

| Item | Verdict | Basis |
|---|---|---|
| C1 — Spec | PASS | Fix targets the shared `SidebarFilter` base (not per-subclass guards), covers all 6 sidebar-filter subclasses, and the test drives the production repopulate path — all three brief self-tests satisfied (`brief.md:35`, `brief.md:59-62`). |
| C2 — Reproduction (red pre-fix) | PASS | Test imports `TypeFilterList` from the new `_typefilterlist.py` (test:6); that file did not exist pre-fix, so the test would have failed with `ImportError` pre-patch — mechanically red. No automated gate ran (check-gates.json C2 result `"none"`); conclusion is derived from the import structure alone. |
| C3 — Change | PASS | Nine files changed; new `TypeFilterList` is GUI-free (`_typefilterlist.py:1-82`), `SidebarFilter` wires it via `add_type_filter`/`_type_popup_shown` (`_sidebarfilter.py:+105-+237`), all six subclasses register (`_eventsidebarfilter.py:+84`, `_familysidebarfilter.py:+98`, `_notesidebarfilter.py:+84`, `_personsidebarfilter.py:+127`, `_placesidebarfilter.py:+98`, `_reposidebarfilter.py:+92`). Advisory: `_reposidebarfilter.py:155-158` passes `"get_event_types"` for a repository filter — see §4. |
| C4 — Verification (red→green) | PASS | Gate `C4-verify` reports PASS (`check-gates.json:38`); GUI gate `C4-verify-interface` is unverifiable (no interface repro file) and non-gating. Note: C4 result carries "PASS-ON-ESSENTIAL" flag referencing `essential-dependency.json`, which is absent from the bundle — see §6.1. |
| C5 — Causal adequacy | PASS | Root cause (construction-time snapshot in `__init__`) is closed by the `popup-shown` signal (`_sidebarfilter.py:+236`) calling `_type_filters.refresh()` (`_typefilterlist.py:327-329`), which re-fetches from the live db on every drop-down open; mirrors the editor-dialog contract stated in `brief.md:17`. `MonitoredDataType.rebuild` preserves the current selection across the refill (`monitoredwidgets.py:+541-543`). |
| T1 — Structure | N/A | Core-only change; no addon path in `patch.diff`. Gate confirms: "T1 – N/A: no addons-source path in patch.diff" (`check-gates.json:64`). |
| T2 — Shape | PASS | Shape gate: 9 files conform, 1 non-blocking advisory (`check-gates.json:73`). POTFILES gate: all three new files (`_typefilterlist.py`, `test/__init__.py`, `test/_sidebarfilter_test.py`) registered in `po/POTFILES.skip` (`patch.diff:556-558`), matching `brief.md:68-69`. |
| T3 — Runtime | PASS | Unit suite matches recorded baseline (7 known reds, `check-gates.json:91`); GUI smoke is green with one prior red resolved (`check-gates.json:100`). Both sub-checks carry a baseline tree-drift warning (`recorded detached@674e3b`) — the baseline commit may differ from the patched tree; reviewers should note this is not a clean baseline. |
| T4 — Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle. Gate confirms N/A (`check-gates.json:109`). |
| T5 — Judgment | NEEDS-HUMAN | Three advisory items require human verification before sign-off: (a) `_reposidebarfilter.py` wrong db method (§6.2); (b) `essential-dependency.json` absent from bundle (§6.1); (c) `MonitoredDataType.rebuild` assumes `self.sel` carries `rebuild`/`set_values` (§6.3). |
| V — Validation | NEEDS-HUMAN | Human must confirm the fix resolves the user-visible symptom (Type selector populated without view recreation) on a live Gramps instance with `assess.ged`; GUI C4 gate was unverifiable (`check-gates.json:47`). |

---

## §2 Patch summary (what the reviewer re-derived)

The fix introduces a GUI-free `TypeFilterList` class (`_typefilterlist.py`) that holds `(fetch, apply)` pairs for each database-derived type selector. `SidebarFilter.__init__` constructs one and immediately calls `_register_type_filters()` (a new hook). Each of the six sidebar-filter subclasses overrides that hook to call `add_type_filter(widget, db_method_name)`, which registers a live-db fetch closure and connects a `notify::popup-shown` signal. On every drop-down open, `_type_filters.refresh()` re-reads the db and rebuilds the widget stores in place via `StandardCustomSelector.rebuild()` (new in `autocomp.py`), preserving the current selection through `MonitoredDataType.rebuild()`. The same refresh fires on `db_changed`. The regression test (`test/_sidebarfilter_test.py`) exercises the production `NoteSidebarFilter._register_type_filters` wiring headlessly, using `__new__` to bypass widget construction and recording doubles for the combo and store.

---

## §3 Scope compliance

Brief `brief.md:35` states a single-module guard (note-only) does not satisfy the invariant. The patch covers all six sidebar filters: event, family, note, person, place, repository — scope is compliant.

Brief `brief.md:63-69` prescribes registering new files in `po/POTFILES.skip`. All three new files are present at `po/POTFILES.skip:556-558`. No new production file with translatable strings was created (the new production module `_typefilterlist.py` contains no `_()` calls).

---

## §4 Advisory notes (non-blocking observations for the human reviewer)

**A1 — Repository filter db method (`_reposidebarfilter.py:155-158`).** The implementation uses `"get_event_types"` for the repository sidebar filter's type selector, with an in-patch comment stating this "preserves the existing source." If the pre-fix `RepoSidebarFilter.__init__` already fetched event types for the repository type selector (rather than a `get_repository_types()` method), the patch faithfully preserves that behavior. However, if Gramps exposes `get_repository_types()`, the refresh will now be live but wrong — a pre-existing bug made live. The brief is silent on this; the maintainer should verify the intended db method for the repository selector before merging.

**A2 — `MonitoredDataType.rebuild` type contract (`monitoredwidgets.py:+533-+543`).** The new `rebuild` method calls `self.sel.rebuild(custom_values)` and `self.sel.set_values(current)`. The `self.sel` attribute is a `StandardCustomSelector` in the normal `MonitoredDataType` use path. If any sidebar filter wires a `MonitoredDataType` whose `sel` is a different class (one that does not implement `rebuild`/`set_values`), this will raise `AttributeError` at popup time. This reviewer could not inspect the full set of callers without access to the complete source tree.

**A3 — Baseline tree drift.** Both T3 gates carry the warning "baseline tree drift: recorded detached@674e3b". The test baseline was recorded on a specific detached commit; if the patched tree is at a different commit, the baseline comparison is approximate. The gates pass, but a clean baseline run on the exact patched commit would be more definitive.

**A4 — Essential dependency.** The C4 gate result notes "PASS-ON-ESSENTIAL — fix is correct but depends on an essential fix (see essential-dependency.json)". That file is not present in the bundle. The human reviewer must confirm the content and disposition of the essential dependency before sign-off.

---

## §5 Elements that are PASS

C1, C2, C3, C4, C5, T2, T3 all pass with the noted advisories. T1 and T4 are N/A.

---

## §6 Human clearances required before sign-off

**§6.1 — Essential dependency (blocks sign-off).** The C4 gate result references `essential-dependency.json` as a dependency the fix requires. That file is absent from this bundle. The human must locate `essential-dependency.json`, confirm what the essential fix is, and ensure it is present in (or will be co-merged with) the submitted changeset. Until cleared, the C4 PASS is conditional.

**§6.2 — Repository filter db method (advisory, maintainer call).** Verify that `"get_event_types"` is the correct database method for the `RepoSidebarFilter` type selector, or replace with the appropriate method (e.g. `"get_repository_types"` if it exists). If the pre-fix code was already wrong, this fix will make the staleness go away while keeping the wrong type list — a distinct bug the maintainer should decide whether to fix in the same PR or file separately.

**§6.3 — `MonitoredDataType.sel` type coverage.** Confirm that every `MonitoredDataType` instance that is passed to `add_type_filter` (i.e., the `event_menu` / `rel_menu` / `place_menu` attributes of the six sidebar filters) has a `sel` attribute that is a `StandardCustomSelector` (or another class that implements `rebuild` and `set_values`). If any does not, the popup will raise `AttributeError` silently swallowed by GTK. A one-line `isinstance` check in `add_type_filter` or a targeted grep of the sidebar-filter subclass constructors would close this.

**§6.4 — Live GUI smoke with assess.ged (V gate).** The automated GUI C4 interface gate was unverifiable. A human must manually confirm the success criterion (`brief.md:19-24`): open the Notes category, confirm "GEDCOM import" is absent in the Type selector, import `assess.ged`, re-open the Type selector without recreating the view, and confirm "GEDCOM import" now appears.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] T5 — Judgment — Three advisory items require human verification before sign-off: (a) `_reposidebarfilter.py` wrong db method (§6.2); (b) `essential-dependency.json` absent from bundle (§6.1); (c) `MonitoredDataType.rebuild` assumes `self.sel` carries `rebuild`/`set_values` (§6.3).
- [ ] V — Validation — Human must confirm the fix resolves the user-visible symptom (Type selector populated without view recreation) on a live Gramps instance with `assess.ged`; GUI C4 gate was unverifiable (`check-gates.json:47`).
- [ ] C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail) unverifiable — no interface repro engine/interface/test_bug_*13716_*.py for bundle issue_13716 — the per-fix GUI red→green cannot run; 

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
- Iteration delta (if iterating): 1. _reposidebarfilter.py must use get_repository_types() instead of get_event_types(). The correct db method exists (base.py:826); the pre-existing wrong method was preserved by the patch but the goal is a working Type selector, so fix it here. 2. Add an interface repro test (engine/interface/test_bug_13716_*.py) so the GUI red→green gate is verifiable in the next Check pass. Notes carried forward: essential dependency on headless-ut-segfault (upstream PR #2357) must land first; §6.3 (MonitoredDataType.sel always StandardCustomSelector) is verified clear.
- By / date: Eduard Ralph / 2026-06-20

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
