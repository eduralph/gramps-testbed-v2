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
