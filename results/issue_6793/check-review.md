# check-review.md — issue 6793 / surname-gramplets-disagree-on-unique-count

> Reviewer: Claude (advisory, artifact-only). `PDCA_TARGET` is **unset**; all
> `path:line` citations are grounded on `patch.diff` alone.

---

## 5/5/1 Verdict Table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 Spec | PASS | Brief names the defect (three gramplets, three counting rules, divergent totals), states the success criterion (one consistent rule, same total across gramplets on the same tree), scopes out patronymics/cloud-weighting, and explicitly mandates a test that calls production routines — all verified against `brief.md`. |
| C2 Reproduction (red pre-fix) | PASS | No automated gate configured (`result: "none"`); grounded on `patch.diff` instead. Pre-fix code visibly encodes three distinct rules: `statsgramplet.py:191` uses `len(set(database.surname_list))`; `surnamecloudgramplet.py:104–117` uses `name.get_surname().strip()` into a `namelist`; `topsurnamesgramplet.py` uses `name.get_group_name().strip()` via `record_surnames`. These enumerate different fields and populations, confirming the divergence the brief reports (244 vs 449). |
| C3 Change | PASS | Patch: (1) creates `gramps/plugins/lib/libsurnames.py` with canonical `record_surnames` + `count_unique_surnames`; (2) removes local `record_surnames` from `topsurnamesgramplet.py`, imports from libsurnames (logic identical — safe refactor); (3) replaces `surnamecloudgramplet.py`'s bespoke loop and `namelist` with `record_surnames` + `len(surnames)`; (4) replaces `statsgramplet.py:191`'s `len(set(database.surname_list))` with `count_unique_surnames(database)`; (5) adds test; (6) updates `po/POTFILES.skip`. No out-of-scope touchpoints detected. |
| C4 Verification (red→green) | PASS | Gate `C4-verify` recorded `green-with-fix=PASS / red-without-fix=PASS` (`check-gates.json:38`). Gate is gating (`"gating": true`). |
| C5 Causal adequacy | PASS | Root cause is divergent enumeration rules; fix eliminates the divergence by routing all three gramplets through a single shared function (`libsurnames.py`). No new `hasattr` / capability probe is *added* by the patch — the pre-existing `hasattr(database, "surname_list")` guard at `statsgramplet.py:15` (patch context) is unchanged; C5 smell-test does not fire. One residual judgment point is noted under T5. |
| T1 Structure | N/A | Gate recorded N/A: this is a core-only change; §Structure (addon folder layout) does not apply (`check-gates.json:56`). |
| T2 Shape | PASS | Gate `T2-shape` and `T2-potfiles` both pass (`check-gates.json:64–74`). New files carry GPL-2+ headers (`libsurnames.py:1–17`, `surnamecount_test.py:1–17` in `patch.diff`); both new `.py` files are registered in `po/POTFILES.skip` (`patch.diff:438,446`). |
| T3 Runtime | NEEDS-HUMAN | Gate `T3-unit` is non-gating but logged **one new failure not in baseline**: `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` (`check-gates.json:82`). Decide whether this failure is pre-existing/flaky or patch-induced before merge — the SQLite export test is unrelated to gramplet surname code, making patch causation unlikely, but the delta must be cleared by a human rerun or baseline annotation. |
| T4 Contribution | N/A | Gate recorded N/A: no `commit-msg.txt` or `pr-description.md` in bundle (`check-gates.json:91`). |
| T5 Judgment | NEEDS-HUMAN | Two design choices the patch embeds need human confirmation: **(a) Semantically orphaned guard** — `statsgramplet.py:15` (patch context) retains `hasattr(database, "surname_list")` to gate the unique-surname display block, but the block now calls `count_unique_surnames(database)` which uses only `db.iter_people()` — if a DB implementation provides `iter_people()` but no `surname_list`, the Statistics gramplet silently omits the unique-surname line while Surname Cloud still shows one (decide: drop the guard to use `iter_people()` directly, or leave as conservative gate); **(b) Empty-string counted as unique surname** — `libsurnames.py:406–414` (patch.diff) includes `""` in the `surnames` dict; the old Surname Cloud `namelist` explicitly excluded empty strings (`and not name.get_surname().strip() == ""`); the new canonical rule treats a no-surname person as contributing `""` to the unique count — decide whether this is the intended canonical definition. |
| Validation — fitness-to-purpose | NEEDS-HUMAN | Decide whether **(1)** the chosen canonical rule — distinct `get_group_name()` values across primary and alternate names, including the empty string — is the correct product definition of "unique surnames"; and **(2)** the three gramplets are now fully aligned in *both* their counting method and the conditions under which they display the count (see T5(a)). These questions cannot be settled mechanically and must be verified on a real tree (e.g. the `example.gramps` repro from `brief.md`) before merge. |

---

## Notes

### C5 smell-test (mandatory)
The patch does **not** add any new `hasattr`, `try/except ImportError`, or runtime capability probe around newly introduced code. The pre-existing `hasattr(database, "surname_list")` guard was already present before this patch and is not itself a patch artefact. The smell-test rule ("fires when the fix *adds* a capability probe") does **not** trigger. The guard's now-stale semantics are captured as a T5/NEEDS-HUMAN item.

### T3 isolation note
`Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` operates on the SQLite backend; the patch touches only `gramps/plugins/gramplet/` and `gramps/plugins/lib/libsurnames.py`. Patch causation is very unlikely but cannot be ruled out without a clean rerun.

### Scope-creep / prior-art check
Brief documents a prior-art search concluding no prior unification PR existed (only unrelated Black/license and a wrong-surname-link fix `e39dc09e2e`). The patch is narrowly scoped to the counting divergence; cloud weighting and patronymic membership (issue 6988) are untouched. No scope-creep detected.
