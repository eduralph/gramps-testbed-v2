# Result — issue 8850 / gedcom-import-cal-date-case-sensitive

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: A GEDCOM `DATE` that uses the `CAL` (calculated) approximation keyword in any
- Success criterion: Importing a GEDCOM `2 DATE Cal 1847` (and the `Est`/`Int` variants in
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the GEDCOM date-qualifier extraction in `gramps/plugins/lib/libgedcom.py`. The

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: fail — → essential-line retry for 6.1 also FAILED — a real failure, not a missing prerequisite.
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style (1 advisory)
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review — issue 8850 / gedcom-import-cal-date-case-sensitive

**Reviewer role:** Check (advisory, artifact-only, decorrelated from builder)
**Artifacts read:** `patch.diff`, `brief.md`, `check-gates.json`
**Artifacts withheld:** `build-notes.md` (by design)
**PDCA_TARGET:** unset — all path:line citations are grounded against `patch.diff` only
**Overall gate result (from check-gates.json):** `fail`

---

## §1 Verdict Table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | `brief.md` fully defines the defect (case-sensitive `MOD` regex), the two-step fix requirement (regex flag + uppercase normalisation), success criterion (`QUAL_CALCULATED`/`QUAL_ESTIMATED` with year parsed), and SELF-TEST for generality over the qualifier-keyword class |
| C2 — C2 Reproduction (red pre-fix) | NEEDS-HUMAN | `check-gates.json` C2 result=`"none"`, oracle="(no gate configured)"; no automated red-pre-fix run was captured; `build-notes.md` withheld; confirmation that the new test was red on unpatched `maintenance/gramps61` must come from the builder or a manual re-run |
| C3 — C3 Change | PASS | `patch.diff` adds `re.IGNORECASE` at `libgedcom.py` hunk-offset +144 and `mod = mod.upper()` at hunk-offset +1108, matching both steps the spec requires; new test file and `po/POTFILES.skip` entry present; no out-of-scope paths touched |
| C4 — C4 Verification (red→green) | FAIL | `check-gates.json` C4 result=`"fail"` (gating=true): "essential-line retry for 6.1 also FAILED — a real failure, not a missing prerequisite" — tests are red post-fix; this gate blocks the change |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Causal chain is coherent on paper (case-insensitive match → `mod.upper()` → `QUALITY_MAP["CAL"]` → `QUAL_CALCULATED`), but C4 is red post-fix, so the chain is unverified; root cause of the C4 failure must be determined before adequacy can be signed off (see §6) |
| T1 — T1 Structure | N/A | Core-only change; `§Structure` gate is addon-only — confirmed by `check-gates.json` T1 path_line: "N/A: no addons-source path in patch.diff" |
| T2 — T2 Shape | PASS | `check-gates.json` T2 result=`"pass"` (1 advisory — likely a lint/style advisory, not a block); `po/POTFILES.skip` entry for the new test file confirmed at `patch.diff` hunk offset +169; GPL header present in new test file (`patch.diff:7–21`) |
| T3 — T3 Runtime | PASS | `check-gates.json` T3 result=`"pass"`; whole-suite baseline matches recorded baseline (7 known failures); baseline tree drift noted (`detached@674e3b`) but engine treats this as non-blocking |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in bundle — confirmed by `check-gates.json` T4 path_line |
| T5 — T5 Judgment | NEEDS-HUMAN | C4 gate failure leaves open whether (a) the test has a bug masking a correct fix, or (b) the code change has a gap; additionally, `test_int_mixed_case_is_calculated` (`patch.diff:127`) asserts `Date.QUAL_CALCULATED` for `INT` — correctness depends on the unread `QUALITY_MAP` contents in `libgedcom.py`; both require human judgement (see §6) |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Real-world GEDCOM file behaviour and Verify-the-Data tool response require human sign-off; cannot be confirmed from patch alone |

---

## §2 C1 — Spec

`brief.md` is present, human-authored, and covers:

- **Defect:** Mixed-case `CAL`/`EST`/`INT` qualifiers on `DATE` lines fail to match the `MOD` regex (`libgedcom.py:886` on `maintenance/gramps61`), leaving `qual = QUAL_NONE` and the value stored as `MOD_TEXTONLY`.
- **Two-step fix requirement (explicit in brief):** (1) make the regex case-insensitive; (2) normalise the captured token to uppercase before the `QUALITY_MAP` lookup — a half-fix that only adds the regex flag still delivers `QUAL_NONE` because `QUALITY_MAP` keys are uppercase.
- **SELF-TEST:** Fix must cover the qualifier-keyword class (`CAL`, `EST`, `INT`), not just `"Cal"`.
- **Scope boundary:** calendar-escape, range/span parsing, bare-numeric-DATE warning — out of scope.

Spec is clear, coherent, and sufficient to evaluate the patch.

---

## §3 C2 — Reproduction

No automated red-pre-fix run was recorded (`check-gates.json` C2 result=`"none"`). The test file (`patch.diff:86–135`) provides a GEDCOM fixture that *would* demonstrate the failure on unpatched code, but whether it was actually run against unpatched `maintenance/gramps61` is not evidenced in the available artifacts. This item requires human confirmation (see §6 item 1).

---

## §4 C3 — Change

Three files changed:

1. **`gramps/plugins/lib/libgedcom.py` (two hunks):**
   - Hunk 1 (`@@ -883 …`): `MOD = re.compile(r"\s*(INT|EST|CAL)\s+(.*)$", re.IGNORECASE)` — satisfies brief step 1.
   - Hunk 2 (`@@ -1104 …`): inserts `mod = mod.upper()` immediately after `mod, text = match.groups()` — satisfies brief step 2. The comment correctly names the invariant without referencing the task.

2. **`gramps/plugins/importer/test/importgedcom_caldate_test.py` (new, 129 lines):**
   - Drives the real importer via `import_as_dict` / `libgedcom` (not a copy of the regex) — satisfies brief constraint.
   - Tests all three qualifier keywords in mixed case (`Cal`, `Est`, `Int`) plus the all-caps control (`CAL`).
   - GPL header present.

3. **`po/POTFILES.skip`:** new test file appended at correct alphabetical position — satisfies brief requirement.

No out-of-scope paths (calendar-escape, range/span, bare-numeric warning) are touched.

**One observation for human review (T5):** `test_int_mixed_case_is_calculated` (`patch.diff:127`) asserts `Date.QUAL_CALCULATED` for `INT`. If `QUALITY_MAP` on `maintenance/gramps61` maps `INT` to `QUAL_ESTIMATED` rather than `QUAL_CALCULATED`, this assertion is wrong and the test would be red for the wrong reason — masking a real fix. The `QUALITY_MAP` contents are not visible in `patch.diff` and `PDCA_TARGET` is unset. See §6 item 3.

---

## §5 C4 / C5 — Verification and Causal Adequacy

**C4 is a gating failure.** `check-gates.json` records C4 result=`"fail"` with the annotation "essential-line retry for 6.1 also FAILED — a real failure, not a missing prerequisite." Without `build-notes.md`, the exact failure output is not available to this reviewer, but the engine marks it as a real test failure, not an environment / prerequisite problem.

Possible root causes of the C4 failure (without build-notes; for human investigation):

- **`CliUser` constructor signature:** `patch.diff:93` passes `callback=lambda *a, **k: None`. If `gramps.cli.user.User` does not accept a `callback` keyword argument in the `maintenance/gramps61` codebase, `import_as_dict` may raise or return `None`, causing every assertion in `_birth_date` to fail at line 101.
- **`gramps_id` assignment:** The test expects IDs `"I1"`, `"I2"`, `"I3"`, `"I4"` (`patch.diff:121,124,127,130`). Gramps may assign zero-padded IDs (`"I0001"`) rather than bare XREF tokens. If so, `get_person_from_gramps_id` returns `None` and all tests fail at line 103.
- **`QUALITY_MAP` key for `INT`:** As noted above, the assertion `QUAL_CALCULATED` for `INT` may be wrong if the real map uses a different quality.
- **GEDCOM fixture incompleteness:** The `SUBM` record at `patch.diff:58–60` is minimal; some importer validation may reject it.

Until the C4 failure is diagnosed, C5 (causal adequacy) cannot be confirmed — the fix may be correct and the test buggy, or the fix may have a gap.

---

## §6 NEEDS-HUMAN Items

Human must clear all three before this patch can be promoted.

**Item 1 — C2: Red pre-fix confirmation**
Confirm (from build-notes or a manual re-run) that `importgedcom_caldate_test.py` was run against unpatched `maintenance/gramps61` and all four tests were red. If this was not done, run it now against the unpatched branch.

**Item 2 — C4/C5: Diagnose the C4 failure and re-verify green post-fix**
Read `build-notes.md` (withheld from this reviewer) or re-run the verification script to obtain the full test output. Identify whether the failure is:
- (a) A test bug (e.g., wrong `CliUser` API, wrong gramps_id scheme) — fix the test, leave the code change, re-run C4.
- (b) A code gap (e.g., `mod.upper()` placed after, not before, the QUALITY_MAP lookup, or some other path) — fix the code, re-run C4.
- (c) A fixture / environment issue — diagnose and remediate, re-run C4.

C4 must be green before promotion. C5 sign-off follows from a green C4 plus reviewer agreement on the causal chain.

**Item 3 — T5: Verify `INT` → `QUAL_CALCULATED` assertion is correct**
Read `QUALITY_MAP` in `gramps/plugins/lib/libgedcom.py` on `maintenance/gramps61` and confirm that `INT` maps to `Date.QUAL_CALCULATED`. If it maps to `QUAL_ESTIMATED`, update `test_int_mixed_case_is_calculated` (`patch.diff:127`) before re-running C4.

**Item 4 — V: Human fitness-to-purpose sign-off**
After C4 is green, manually import a real-world GEDCOM file containing `2 DATE Cal 1847` (or synthesise the minimal snippet from `brief.md`), open the resulting person's birth date in the Gramps UI, confirm quality shows as "Calculated" with year 1847, and run Tools → Utilities → Verify the Data to confirm no flag is raised. Repeat for `Est` and `Int` variants.

---

## §7 Summary

The **code change is causally correct on paper** — adding `re.IGNORECASE` to `MOD` and then `mod.upper()` before the `QUALITY_MAP` lookup is exactly the two-step fix the spec requires, and the scope is clean. The **test design is sound in intent** (drives the real importer, covers all three qualifier keywords plus control). However, **C4 is a gating failure** and this review cannot determine whether the failure is in the test or the fix without `build-notes.md`. No promotion is possible until §6 items 1–4 are cleared.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C2 — C2 Reproduction (red pre-fix) — `check-gates.json` C2 result=`"none"`, oracle="(no gate configured)"; no automated red-pre-fix run was captured; `build-notes.md` withheld; confirmation that the new test was red on unpatched `maintenance/gramps61` must come from the builder or a manual re-run
- [ ] C5 — C5 Causal adequacy — Causal chain is coherent on paper (case-insensitive match → `mod.upper()` → `QUALITY_MAP["CAL"]` → `QUAL_CALCULATED`), but C4 is red post-fix, so the chain is unverified; root cause of the C4 failure must be determined before adequacy can be signed off (see §6)
- [ ] T5 — T5 Judgment — C4 gate failure leaves open whether (a) the test has a bug masking a correct fix, or (b) the code change has a gap; additionally, `test_int_mixed_case_is_calculated` (`patch.diff:127`) asserts `Date.QUAL_CALCULATED` for `INT` — correctness depends on the unread `QUALITY_MAP` contents in `libgedcom.py`; both require human judgement (see §6)
- [ ] V — Validation — fitness-to-purpose — Real-world GEDCOM file behaviour and Verify-the-Data tool response require human sign-off; cannot be confirmed from patch alone

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
- Iteration delta (if iterating): The libgedcom.py fix (re.IGNORECASE + mod.upper()) is correct — manual red→green confirmed. The test (importgedcom_caldate_test.py) is buggy and failed the Docker gate. Two concrete candidates to fix: 1. CliUser(callback=...) — verify User accepts a callback kwarg on maintenance/gramps61; if not, remove it. 2. gramps_id format — test expects "I1"/"I2" etc.; Gramps likely assigns "I0001" style. Fix the lookup to match actual ID format. Fix the test scaffolding, rerun run-verify.sh, get C4 green. No change needed to the production fix.
- By / date: Eduard Ralph / 2026-06-21

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
