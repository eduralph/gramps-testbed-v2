# Check Review — issue 13716 / sidebar-filter-type-list-stale

Reviewer: Check (advisory, artifact-only, decorrelated from builder)
Artifacts read: `brief.md`, `check-gates.json`, `patch.diff`
Artifact withheld: `build-notes.md` (by design)
Review date: 2026-06-20

---

## §1 Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — Spec | PASS | `brief.md` fully states defect, success criterion, invariant, repro, scope, test-file path, carry-forwards, and POTFILES handling; all fields parseable |
| C2 — Reproduction (red pre-fix) | PASS | No formal oracle configured (check-gates.json C2 result: none); inferential basis: `_sidebarfilter_test.py` imports `TypeFilterList` (new module) and calls `_type_filters.refresh()` — both absent pre-fix, so test is guaranteed `ImportError`/`AttributeError` red on an unpatched tree |
| C3 — Change | PASS | All 6 sidebar filters (note/event/family/person/place/repo) receive `_register_type_filters()`; shared fix lives in `_sidebarfilter.py`; `_reposidebarfilter.py:155` carry-forward (`get_event_types` → `get_repository_types`) addressed; `_typefilterlist.py` (new production module) registered in `po/POTFILES.skip` |
| C4 — Verification (red→green) | PASS | Gating headless-unit gate `C4-verify` reports `PASS-ON-ESSENTIAL` (check-gates.json); non-gating interface gate `C4-verify-interface` blocked by dirty workspace (environmental), not a test-logic failure; see §6.1 and §6.2 |
| C5 — Causal adequacy | PASS | Root cause (construction-time snapshot of `get_*_types()` passed once to selector, never re-read) is fully addressed: `rebuild()` on `StandardCustomSelector` (`autocomp.py:58`) and `MonitoredDataType` (`monitoredwidgets.py:490`) enable in-place refresh; `_type_popup_shown` hook (`_sidebarfilter.py:238`) mirrors editor-dialog contract (re-read per presentation); db-change path also calls `_type_filters.refresh()` (`_sidebarfilter.py:195`); `MonitoredDataType.rebuild` preserves current selection across refill (`monitoredwidgets.py:596–598`) |
| T1 — Structure | N/A | T1 is addon-layout only; patch is core-only (no addons-source path in diff); check-gates.json T1 confirms `N/A: no addons-source path in patch.diff` |
| T2 — Shape | PASS | check-gates.json T2-shape: 9 files conform (1 advisory noted, no `print()` visible in diff); T2-potfiles (gating) PASS: `_typefilterlist.py`, `test/__init__.py`, `_sidebarfilter_test.py` all registered in `po/POTFILES.skip:611–613` (none have translatable strings) |
| T3 — Runtime | PASS | check-gates.json T3-unit: matches recorded baseline (7 known reds, no new failures; tree-drift warning non-blocking); T3-interface: GUI smoke green, 1 previously-recorded red now clear |
| T4 — Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in bundle; check-gates.json T4 confirms `N/A: no commit/PR wrapper in bundle` |
| T5 — Judgment | PASS | `popup-shown` signal approach is the minimum-surprise pattern (matches editor-dialog behaviour); `TypeFilterList` factoring is correctly GUI-free (no `gi`/`gramps.gui` imports in `_typefilterlist.py:1–82`), enabling headless unit testing; `_fill_list` resets `self.active_index = 0` before re-scan (`autocomp.py:49`), needed for correct index bookkeeping on refill; family filter correctly registers both `event_menu` and `rel_menu` (`_familysidebarfilter.py:99–100`); `event_menu` attribute name used for note/repo selectors is an existing naming quirk, not introduced by this patch |
| V — Validation | NEEDS-HUMAN | Fitness-to-purpose against the real Mantis 13716 scenario (GEDCOM import → new Note type appears in open-db sidebar Type selector without gramplet removal) requires human confirmation; cannot be verified from diff alone |

---

## §2 Scope conformance

The fix is implemented once in the shared `SidebarFilter` base class (`_sidebarfilter.py`) and opted into by every affected subclass via `_register_type_filters()`. The brief's self-test constraint ("a single-module guard does NOT satisfy this") is met: all six sidebar-filter subclasses are covered. No non-type filter fields (ID/Text/Tag) were touched. The db layer is not modified. The Isotammi Filter+ addon is not touched. Scope is clean.

---

## §3 Carry-forward resolution

Both carry-forwards from iteration 1 are addressed:

1. **`_reposidebarfilter.py` wrong db method.** `get_event_types()` replaced by `get_repository_types()` at `_reposidebarfilter.py:155` (init path) and `_reposidebarfilter.py:165` (register path). The regression test `test_repo_filter_reads_repository_types_not_event_types` (`_sidebarfilter_test.py:553–575`) verifies this using a `_FakeDb` with disjoint `repository_types` and `event_types` sets.

2. **Interface repro test.** The check-gates.json `C4-verify-interface` gate ran (and was blocked by an environment issue — see §6.1). The test infrastructure exists. The headless regression test (`_sidebarfilter_test.py`) additionally covers the production repopulate path as required by the brief.

---

## §4 Notable observations (non-blocking)

- **`_fill_list` active_index reset (`autocomp.py:49`).** On every `_fill_list` call `self.active_index` is reset to 0 before scanning. This is necessary because the list is cleared before refill (`store.clear()` at line 48); without the reset, the active-index bookkeeping would be stale. `MonitoredDataType.rebuild` compensates at the higher level by saving and restoring the current selection (`monitoredwidgets.py:596–598`), so the user's in-progress selection is not lost across a background refresh.

- **`_fill_menu` vs `_fill_list` branching in `rebuild` (`autocomp.py:68–72`).** When `self.menu` is truthy (a menu-style selector), `rebuild` refills both `self.store` (the tree store) and `self.completion_store` (the flat completion list). When falsy (list-style selector), only `self.store` is refilled. This correctly mirrors the constructor logic where `completion_store` is a separate flat view over the menu store.

- **T3 baseline tree drift.** The gate reports `recorded detached@674e3b`; the workspace has since moved. This is an infrastructure note, not a test failure.

---

## §5 Essential dependency

The `C4-verify` gate passes as `PASS-ON-ESSENTIAL`, citing `essential-dependency.json` (not provided in this bundle). The referenced upstream dependency is upstream PR #2357 (headless-ut-segfault). The fix itself appears correct; the dependency gate means the headless test suite cannot complete cleanly on an unpatched upstream. **This dependency must land before the fix can ship** — see §6.2.

---

## §6 Human-required clearance items

These items cannot be cleared by the Check reviewer. Each NEEDS-HUMAN verdict and each qualified PASS with an open caveat produces one item here.

**§6.1 — C4-verify-interface: confirm environmental block, not test failure.**
The interface gate was refused by `run-verify-interface.sh` because `/home/eddie/workspace/gramps-6.1 has uncommitted changes`. The human must either clear the uncommitted changes and re-run the interface gate, or explicitly confirm that the block is environmental and that no interface regression is expected.

**§6.2 — Essential dependency: confirm upstream PR #2357 status.**
The headless unit test passes only as `PASS-ON-ESSENTIAL`. `essential-dependency.json` is not in this bundle. The human must confirm the status of upstream PR #2357 (headless-ut-segfault) and either confirm it is merged to `maintenance/gramps61`, or gate this fix's shipment until it is.

**§6.3 — C2: confirm observed red pre-fix.**
No formal pre-fix run is recorded (C2 oracle: none). The reviewer's inferential basis (ImportError on `TypeFilterList` before the fix) is sound but not a substitute for an observed red. The human should confirm the test was seen red on an unpatched tree, or accept the inferential basis and waive this item.

**§6.4 — V: Validate fitness-to-purpose against Mantis 13716.**
The human must confirm the fix resolves the reported scenario: starting Gramps, opening the Notes category, importing `assess.ged` (creating a "GEDCOM import" Note type), and verifying the Type selector in the Filter Gramplet now offers "GEDCOM import" without removing and re-adding the gramplet. This cannot be confirmed from the diff.

---

## §7 Overall gate status

All gating checks pass (C4-verify gating PASS, T2-potfiles gating PASS). Non-gating items: C4-verify-interface blocked environmentally (§6.1); C2 inferential (§6.3). Four §6 items require human clearance before sign-off. The fix is technically sound; clearance is a process and environmental matter, not a correctness matter.

---

## §8 Addendum — PR #2396 review question (2026-06-21)

After publication, reviewer prculley asked on PR #2396 how the selector recognizes
custom-type changes from other editors/imports, observing that `_db_changed` only
fires on a family-tree switch. This addendum records the verification; it does not
change any §1 verdict.

- **Mechanism confirmed.** `_db_changed`/`refresh()` (`_sidebarfilter.py:195`) is the
  secondary, tree-switch trigger only. The live trigger is the `notify::popup-shown`
  connection in `add_type_filter` (`_sidebarfilter.py:236`): opening a selector calls
  `_type_popup_shown` → `refresh()` → `fetch` re-reads the live db, so a type added by
  any editor/import since construction is offered on next open. This is the
  pull-on-open contract already credited under C5/T5 — the question surfaced no gap.

- **`popup-shown` reliability (the linchpin) verified against local GTK 3.24.52.** All
  seven selectors are `Gtk.ComboBox(has_entry=True)`. Source: in `gtkcombobox.c`,
  `popup-shown` is set+notified only by `gtk_combo_box_child_show()`/`child_hide()`,
  which both menu-mode and list-mode popup setup wire to their popup toplevel's
  `show`/`hide` — so the notify is independent of popup mode. Empirical: driving such a
  combo through `popup()`/`popdown()` emitted `notify(popup-shown=True)` then `False`.

- **Correction.** `has_entry=TRUE` does **not** force list mode;
  `gtk_combo_box_check_appearance()` keys only off `wrap_width` and the
  `appears-as-list` style property. On the test theme (`appears-as-list` False) these
  combos use a GtkMenu popup, and the notify still fired — the mechanism is
  theme-independent. Verification detail recorded in `build-notes.md`
  ("PR #2396 follow-up").
