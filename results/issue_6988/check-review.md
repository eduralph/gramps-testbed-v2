# Check Review — issue 6988 / surname-count-includes-patronymic-nonprimary

**Reviewer:** Claude (advisory, artifact-only)
**Inputs used:** `patch.diff`, `brief.md`, `check-gates.json`
**`PDCA_TARGET`:** unset — all path:line citations are grounded on `patch.diff` alone
**Date:** 2026-06-27

---

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 Spec | PASS | Brief is internally consistent: defect (patronymic components inflate unique-surname count), root cause (full multi-surname string from `get_surname()` without origin discrimination), success criterion ("Иванов" counted once not per patronymic), target branch, scope boundaries (not 6793, not display-formatting), and test-file requirement are all clearly stated. brief.md:6–17 |
| C2 Reproduction (red pre-fix) | PASS | check-gates.json C4 entry records `red-without-fix=PASS`, confirming the new `patronymic_surname_count_test.py` was red on the unfixed tree. check-gates.json:37 |
| C3 Change | PASS | New shared helper `surnamecounter.py` filters non-primary patronymic/matronymic components and falls back to `name.get_surname()` when nothing would be dropped or the component list would be emptied. Both gramplets route through it. `topsurnamesgramplet.py` is named in the brief defect description but not patched — flagged in T5 for human scope decision. patch.diff:76–161, 1–43, 44–73 |
| C4 Verification (red→green) | PASS | Gate reports `green-with-fix=PASS / red-without-fix=PASS` (gating=true). check-gates.json:37–38 |
| C5 Causal adequacy | PASS | Fix transforms the root cause (decomposes the full surname string by `NameOriginType` before tallying) rather than adding a capability probe around a guarded path. No `hasattr`/try-fallback smell in new code. The pre-existing `hasattr(database, "surname_list")` guard at patch.diff:37 is unchanged context, not a new probe. C5 smell-test does not fire. |
| T1 Structure | N/A | Core-only change (`gramps/plugins/gramplet/`); no addon bundle path present. T1 addon-layout rule (doc 16 §Structure) is addon-only. Gate concurs: "N/A: no addons-source path in patch.diff". check-gates.json:55 |
| T2 Shape | PASS | GPL header present on new `surnamecounter.py` (patch.diff:82–98); both new `.py` files (`surnamecounter.py`, `patronymic_surname_count_test.py`) registered in `po/POTFILES.skip` (patch.diff:336, 341). Gate reports shape PASS and potfiles PASS (the latter gating=true). check-gates.json:64, 72–73 |
| T3 Runtime | NEEDS-HUMAN | Gate reports FAIL — delta of 4 new failures: `LifeLineChartView.collection::import_or_collection`, `PDFFor…` (truncated in gate output). Names are unrelated to surname counting. Decide whether these failures pre-exist on `maintenance/gramps61` trunk independent of this patch (and the gate's baseline was stale), or whether the patch introduced an import-path regression — the gate cannot self-clear this. check-gates.json:82–84 |
| T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle; commit-message and contributor-workflow checks are not exercisable. Gate concurs: "N/A: no commit-msg.txt or pr-description.md in the bundle". check-gates.json:91–92 |
| T5 Judgment | NEEDS-HUMAN | Two scope/design items require human decision: **(1)** The brief's defect description explicitly names "Top Surnames and Statistics gramplets" — `topsurnamesgramplet.py` is listed in the prior-art survey (brief.md:43) but is not patched; if it has the same `name.get_surname()` counting pattern, the fix is incomplete — decide whether the omission is an intentional scope restriction or an oversight. **(2)** The `hasattr(database, "surname_list")` guard in `statsgramplet.py` (patch.diff:37) now gates display of `len(unique_surnames)`, a stat that no longer depends on `database.surname_list`; backends lacking that attribute will silently suppress the unique-surname count even though it was successfully computed — decide whether the guard should remain, be relaxed to unconditional, or be replaced with a meaningful predicate. |
| Validation — fitness-to-purpose | NEEDS-HUMAN | Per brief disposition (brief.md:47): "the correct treatment of patronymic surnames in counts is the human's call at sign-off" — whether non-primary patronymics are *excluded* from the counting key vs *grouped* under it is a genealogical domain design decision that cannot be mechanically settled. |

---

## Notes

### C3 logic walkthrough (grounded on patch.diff)

`get_counting_surname` (patch.diff:131–160) keeps a surname component when **either** it is the primary component (`surname.get_primary()`) **or** its origin is not in `{PATRONYMIC, MATRONYMIC}`. The two-condition early-return at patch.diff:152 (`not kept or len(kept) == len(surname_list)`) correctly handles:

- All components would be dropped → empty `kept` → fallback to `name.get_surname()` (safe, non-empty result).
- Nothing would be dropped → `len(kept) == len(surname_list)` → fallback (no-op, correct).
- Test `test_only_patronymic_component_falls_back` (patch.diff:313–322) confirms the patronymic-primary edge case: the component is kept via `surname.get_primary()`, so `len(kept) == len(surname_list)`, triggering the fallback. This is correct.

### T3 delta-failure names

The four failing tests named in the gate output (`LifeLineChartView.collection::import_or_collection`, `PDFFor…`) involve a chart-view collection import and PDF output — no surface overlap with `surnamecounter.py`, `statsgramplet.py`, or `surnamecloudgramplet.py`. Likely pre-existing regressions on the target branch, but this must be verified against a clean baseline checkout.

### T5 item 1 — `topsurnamesgramplet.py` gap

The brief defect sentence reads: "The **Top Surnames** and Statistics gramplets treat a person's non-primary *patronymic*-origin surname as part of the surname" (brief.md:7–8). `topsurnamesgramplet.py` is not modified by the patch. If its counting loop also calls `name.get_surname()` without origin filtering, it still exhibits the bug. The fix would be to route it through `get_counting_surname` as well. Human must confirm whether this file was deliberately left out of scope for this cycle.

---

## §6 Human-clearance checklist

- [ ] **T3** — Confirm the 4 T3 delta failures (`LifeLineChartView.collection::import_or_collection`, `PDFFor…`) are pre-existing on `maintenance/gramps61` trunk and not introduced by this patch before merging.
- [ ] **T5 (scope)** — Confirm whether `topsurnamesgramplet.py` (named in brief defect description) is intentionally out of scope for this cycle or must also be patched through `get_counting_surname`.
- [ ] **T5 (guard)** — Decide whether the `hasattr(database, "surname_list")` guard in `statsgramplet.py` should remain, be dropped (display `unique_surnames` unconditionally), or be replaced with a meaningful predicate now that `unique_surnames` no longer depends on `database.surname_list`.
- [ ] **V** — Sign off on the design choice: patronymic/matronymic non-primary surname components are *excluded* from the counting key (rather than, e.g., grouped under a canonical family-surname key by another means). Confirm this matches the intended genealogical semantics for the target user base.
