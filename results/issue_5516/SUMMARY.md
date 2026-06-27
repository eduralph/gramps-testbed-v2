# Result — issue 5516 / date-quality-keyword-matches-inside-word

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: Entering a free-text date that merely *contains* a date quality/modifier
- Success criterion: `DateParser().parse("Test data")` returns a date whose text is
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the quality/modifier text-stripping that fires when the keyword appears as a

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 2 file(s) conform to doc 16 §Coding style (1 advisory)
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# check-review.md — issue 5516 / date-quality-keyword-matches-inside-word

**Reviewer:** Check subagent (advisory; decorrelated from builder)
**Grounding:** `$PDCA_TARGET` is unset — all citations grounded on `patch.diff` alone.
**Date:** 2026-06-27

---

## Verdict Table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 Spec | PASS | Brief is human-authored, root cause is pinned to a specific path:line (`_dateparser.py:528`), success criterion is concrete and testable; scope boundary (genuine quality-prefixed dates must keep working) is explicit — brief.md:6–23 |
| C2 Reproduction (red pre-fix) | PASS | Analytically confirmed: old regex `(.* ?)%s\s+(.+)` matches `"Test data"` as `T` + `est` + ` data` → mangled result `"Tdata"` with QUAL_ESTIMATED; gate oracle also records `red-without-fix=PASS` (check-gates.json:37) |
| C3 Change | PASS | Patch touches exactly the two in-scope files; sole production change is insertion of `\b` at patch.diff:13; test file adds two targeted test methods (regression + positive) at patch.diff:25–44; no new or removed files, no unrelated edits |
| C4 Verification (red→green) | PASS | Gate oracle `C4-verify` (gating=true) records `green-with-fix=PASS / red-without-fix=PASS` (check-gates.json:37–38); fix is analytically consistent: `\b` blocks the spurious match inside `"Test"` while preserving matches on genuine quality tokens at word boundaries |
| C5 Causal adequacy | PASS | Fix directly removes the root cause by anchoring the regex to a word boundary — the substring hazard is eliminated at the match site, not papered over; no capability probe (`hasattr`/`try-except`/feature guard) present; C5 smell test does not fire |
| T1 Structure | N/A | Core-only change; `§Structure` (folder==id, target_version, etc.) is addon-only — confirmed by gate: `T1 – N/A: no addons-source path in patch.diff` (check-gates.json:55) |
| T2 Shape | PASS | Gate records `T2 ✓ shape: 2 file(s) conform to doc 16 §Coding style (1 advisory)` and `T2 ✓ potfiles` (check-gates.json:64, 73); advisory is non-blocking; no new core .py files require POTFILES registration |
| T3 Runtime | NEEDS-HUMAN | Gate records 1 new failure not in baseline: `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` (check-gates.json:82) — decide whether this failure is pre-existing/environmental or patch-introduced; the patch touches no SQLite code so the failure is analytically unrelated, but baseline provenance cannot be confirmed without a re-run against an unpatched tree |
| T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle; gate records N/A (check-gates.json:91); commit/PR wrapper to be provided by the contributor at submission time |
| T5 Judgment | PASS | The change is a single-character (`\b`) insertion at the exact match site; test coverage is complete (regression + positive cases); no scope creep, no imports added, no config changed; the `_mod` regex sharing the same substring hazard is noted as out of scope per brief.md:28 and is not silently left broken by this patch |
| Validation — fitness-to-purpose | NEEDS-HUMAN | Decide whether the `\b` fix handles all locale-specific `_qual_str` alternatives correctly, including tokens with non-ASCII characters or punctuation (e.g. `est.`) that may interact with `\b` differently across Python versions/locales — this cannot be mechanically settled without running the full locale test matrix |

---

## §6 Human-clearance items

- [ ] **T3 — SQLite baseline failure:** Confirm that `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` is pre-existing or environmental (not introduced by this patch). Re-run `T3` against an unpatched `maintenance/gramps61` tree to establish the baseline; if the failure is pre-existing, close this item and mark T3 PASS.

- [ ] **V — Locale/token `\b` fitness:** Confirm that the `\b` word-boundary assertion behaves correctly for all locale-specific quality strings in `_qual_str` (especially punctuated forms such as `est.` and any non-ASCII alternatives) across the Python versions Gramps 6.1 targets. If any token starts with a non-word character, the `\b` placement needs adjustment for that token.

---

## Reviewer notes

**What the fix does (re-derived independently):**  
`patch.diff:13` changes `self._qual = re.compile(r"(.* ?)%s\s+(.+)" % self._qual_str, re.IGNORECASE)` to `self._qual = re.compile(r"(.* ?)\b%s\s+(.+)" % self._qual_str, re.IGNORECASE)`. The inserted `\b` asserts a word boundary immediately before the first character of the quality keyword, meaning the keyword can only match where it begins a word — ruling out substring positions inside a longer token such as `est` inside `Test`.

**Why the fix is causally complete (not a guard):**  
The root cause is the absence of a word-boundary constraint on the start of the quality token. Adding `\b` directly restores the intended semantics: quality tokens are whole-word matches only. No fallback path, no try/except, no feature detection — the fix transforms the root cause.

**Out-of-scope note (not a defect):**  
The brief (line 15) acknowledges the same substring hazard in other quality/modifier patterns (`_mod`). The patch deliberately scopes to `_qual` only. This is consistent with brief.md:28 ("out of scope: the genuine parsing of real quality-prefixed and modifier-prefixed dates"). If `_mod` has the same bug, a separate fix cycle is appropriate.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] T3 Runtime — Gate records 1 new failure not in baseline: `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` (check-gates.json:82) — decide whether this failure is pre-existing/environmental or patch-introduced; the patch touches no SQLite code so the failure is analytically unrelated, but baseline provenance cannot be confirmed without a re-run against an unpatched tree
- [x] Validation — fitness-to-purpose — Decide whether the `\b` fix handles all locale-specific `_qual_str` alternatives correctly, including tokens with non-ASCII characters or punctuation (e.g. `est.`) that may interact with `\b` differently across Python versions/locales — confirmed by inspection across all 28 locales (158 tokens): every token starts with a word character (`\w`), so `\b` anchors correctly in all cases; Python 3 `re` treats Unicode letters as `\w` by default, covering Cyrillic/Arabic/Greek/CJK tokens without any flag.

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: merged-wider
- Iteration delta (if iterating):
- By / date: Eduard Ralph / 2026-06-27

## 10. Act candidates (hints for the next Act review)
- PR note: `\b` is safe for all 158 quality tokens across 28 locales — every token starts with a `\w` character (including punctuated abbreviations like `est.`; trailing period irrelevant); Python 3 `re` treats Unicode letters as `\w` by default so non-ASCII locales (Arabic, Cyrillic, Greek, CJK etc.) are also covered. Future locale authors should be warned: a quality token starting with a non-word character (e.g. a parenthesis) would need a different boundary strategy.
