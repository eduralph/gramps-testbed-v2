# Check Review — issue 8850 / gedcom-import-cal-date-case-sensitive

**Reviewer role:** Check (advisory, decorrelated from builder)
**Artifacts read:** `brief.md`, `patch.diff`, `check-gates.json`
**`$PDCA_TARGET`:** unset — all path:line citations are grounded against `patch.diff` only
**Date:** 2026-06-21
**Iteration:** 2 (iteration 1 failed C4; this bundle is the retry)

---

## §1 Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | brief.md specifies mixed-case `CAL`/`EST`/`INT` must yield `QUAL_CALCULATED`/`QUAL_ESTIMATED` with year parsed; patch targets the two failure points called out in brief §Scope: case-sensitive `MOD` regex (`patch.diff:151`) and uppercase-keyed `QUALITY_MAP` lookup (`patch.diff:163`) — both addressed |
| C2 — C2 Reproduction (red pre-fix) | PASS | No independent C2 oracle configured (`check-gates.json`: "no gate configured"); C4 two-state result (`red-without-fix=PASS`) provides sufficient evidence that the test was red on the unfixed code; brief.md §Repro instruction unambiguously predicts the text-date outcome pre-fix |
| C3 — C3 Change | PASS | Three-file patch, all within brief-declared scope: (1) `libgedcom.py` — `re.IGNORECASE` on `MOD` (`patch.diff:151`) + `mod = mod.upper()` before lookup (`patch.diff:163`); (2) new `importgedcom_caldate_test.py` with 4 test methods; (3) `po/POTFILES.skip` registration (`patch.diff:175`); no out-of-scope paths touched |
| C4 — C4 Verification (red→green) | PASS | `check-gates.json` C4: `green-with-fix=PASS` / `red-without-fix=PASS` via `run-verify.sh`; both legs confirmed; this is the gating element |
| C5 — C5 Causal adequacy | PASS | Root cause is two-part: (a) `MOD` regex case-sensitive → `Cal`/`Est`/`Int` never match (`patch.diff:150`); (b) `QUALITY_MAP` keyed on uppercase → even a match with a mixed-case capture yields `QUAL_NONE`. Fix addresses both in sequence: `re.IGNORECASE` enables the match; `mod.upper()` normalises the capture before lookup (`patch.diff:163`). No half-fix; brief §Scope explicitly warned about the half-fix trap and the patch avoids it |
| T1 — T1 Structure | N/A | Core-only change; §Structure rules (folder==id, target\_version, fname, no `__init__.py`) are addon-only — confirmed N/A by `check-gates.json` T1 |
| T2 — T2 Shape | PASS | GPL header present on new test file (`patch.diff:7-22`); no `print()` calls in the diff; shape gate PASS with 1 advisory (unspecified, non-blocking per gate config); `po/POTFILES.skip` updated (`patch.diff:175`) — `T2-potfiles` gate PASS (gating) |
| T3 — T3 Runtime | PASS | `check-gates.json` T3-unit: matches recorded baseline (7 known reds); ⚠ baseline tree drift noted (`detached@674e3b`) — baseline was recorded at a different commit, so the 7-known-red count may not reflect the current tree's full suite state; gate is non-gating and passed, but the drift is flagged for human awareness (see §6) |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in bundle; `check-gates.json` T4 explicitly records N/A |
| T5 — T5 Judgment | PASS | Fix is minimal (2 production lines, 1 comment block); comment at `patch.diff:159-163` documents the two-step normalisation rationale inline; name-based lookup in test (`patch.diff:104`) correctly sidesteps the importer `gramps_id` padding format that caused iteration-1 failure; test covers the reporter's case (`Cal 1847`), both other qualifier keywords (`Est`, `Int`), and pins the pre-existing uppercase control (`CAL`) — property-level coverage, not single-string special-casing |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Human sign-off required per `check-gates.json` oracle designation; see §6 item V-1 for the specific question this reviewer cannot resolve from the patch alone |

---

## §2 Production-change analysis

**File:** `gramps/plugins/lib/libgedcom.py`

**Change 1** (`patch.diff:151`):
```diff
-MOD = re.compile(r"\s*(INT|EST|CAL)\s+(.*)$")
+MOD = re.compile(r"\s*(INT|EST|CAL)\s+(.*)$", re.IGNORECASE)
```
Enables case-insensitive matching of the qualifier keyword. Necessary but not sufficient alone.

**Change 2** (`patch.diff:159-163`):
```python
            mod = mod.upper()
```
Inserted immediately after `mod, text = match.groups()`, before `QUALITY_MAP.get(mod, ...)` and before `mod += " "`. Normalises the captured group to uppercase so both the map lookup and the downstream range/span text reconstruction operate on the expected value. This is the second half called out in brief §Scope and correctly placed.

No other production paths are touched. The out-of-scope items (calendar-escape, range/span parsing, bare-numeric-DATE warning) are untouched.

---

## §3 Test analysis

**File:** `gramps/plugins/importer/test/importgedcom_caldate_test.py` (135 lines, new)

**Structure:** `unittest.TestCase` with `setUpClass`/`tearDownClass` driving `import_as_dict` → real `libgedcom` importer path — satisfies brief requirement to drive the real extractor, not a regex copy.

**Fixture design:** Four individuals with distinct surnames (`Calc`, `Esti`, `Inte` for mixed-case; `Calc` repeated for uppercase control). The test keys on `"<first> <surname>"` (`patch.diff:104`) to avoid dependence on `gramps_id` padding format — this directly addresses the iteration-1 failure mode.

**Test methods:**

| Method | Fixture key | Expected quality | Year |
|--------|-------------|-----------------|------|
| `test_cal_mixed_case_is_calculated` | `Mixed Calc` | `QUAL_CALCULATED` | 1847 |
| `test_est_mixed_case_is_estimated` | `Mixed Esti` | `QUAL_ESTIMATED` | 1850 |
| `test_int_mixed_case_is_calculated` | `Mixed Inte` | `QUAL_CALCULATED` | 1852 |
| `test_cal_upper_case_control_is_calculated` | `Upper Calc` | `QUAL_CALCULATED` | 1847 |

**Observation:** `test_int_mixed_case_is_calculated` asserts `QUAL_CALCULATED` for `INT` (interpreted). This is consistent with whatever `QUALITY_MAP` defines for `INT` in uppercase (which worked pre-patch), since the patch does not alter `QUALITY_MAP`. The C4 gate passing confirms this expectation is met. However, the reviewer cannot independently verify the `QUALITY_MAP[INT]` value from the patch alone — see §6 item V-1.

**`CliUser` callback kwarg** (`patch.diff:96`): `CliUser(callback=lambda *a, **k: None)` — iteration 1 sign-off flagged this as potentially unsupported. The C4 gate passing confirms it works on the target branch in this iteration.

---

## §4 POTFILES.skip

`po/POTFILES.skip` updated at `patch.diff:175`, inserting `gramps/plugins/importer/test/importgedcom_caldate_test.py` alphabetically within the `plugins/importer/test directory` block, between the existing `importgedcom_ambiguous_date_test.py` and `importgeneweb_test.py`. Correct placement; T2-potfiles gate (gating) PASS.

---

## §5 Summary

The patch correctly addresses both halves of the root cause (regex case-sensitivity + map key normalisation). The test is structurally sound, drives the real importer, covers the reporter's case and all three qualifier keywords in mixed case, and includes an uppercase control. Iteration-1 weaknesses (gramps_id format dependency, callback kwarg) are resolved. All gating elements (C4, T2-potfiles) PASS.

One NEEDS-HUMAN item blocks final sign-off (§6 V-1); T3 baseline drift is flagged for awareness but is non-gating.

---

## §6 NEEDS-HUMAN items

### V-1 — `QUALITY_MAP[INT]` mapping confirmation

**Required before sign-off.**

`test_int_mixed_case_is_calculated` (`patch.diff:133`) asserts that GEDCOM `INT` (interpreted) resolves to `Date.QUAL_CALCULATED`. The patch does not show `QUALITY_MAP`, so this reviewer cannot confirm the mapping from the diff alone. The C4 gate confirms the test passes, but a human must verify that `QUAL_CALCULATED` is the *correct* semantic mapping for `INT` in Gramps — not merely what the current code happens to return.

**Action:** Confirm `QUALITY_MAP["INT"] == Date.QUAL_CALCULATED` in `gramps/plugins/lib/libgedcom.py` on `maintenance/gramps61`, and that this is the intended Gramps interpretation of the GEDCOM `INT` qualifier.

---

### T3-A — Baseline tree drift (informational, non-blocking)

`check-gates.json` T3 records: `⚠ baseline tree drift: recorded detached@674e3b`. The baseline was recorded at a different commit than the current target tree. The 7 known-test-red count may not reflect all currently-failing tests in the suite, meaning the new test could be masking a previously-unknown red or the baseline could have admitted new failures.

**Action (optional):** Re-record the T3 baseline on the current HEAD before final merge, or confirm that `674e3b` and the current HEAD have the same suite behaviour for all tests in scope.
