# Brief — issue 8850 / gedcom-import-cal-date-case-sensitive

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** gedcom-import-cal-date-case-sensitive
- **Defect:** A GEDCOM `DATE` that uses the `CAL` (calculated) approximation keyword in any
  case other than all-uppercase — e.g. `2 DATE Cal 1847`, as real-world GEDCOM files contain —
  is imported as a literal **text** date instead of a Calculated-quality date. The Verify-the-
  Data tool then flags it. The same input spelled `CAL 1847` (all caps) imports correctly as
  Calculated, exposing the case-sensitivity gap. (Reporter's file used `Cal 1847`.)
- **Success criterion:** Importing a GEDCOM `2 DATE Cal 1847` (and the `Est`/`Int` variants in
  mixed case) yields a `Date` whose quality is `QUAL_CALCULATED` (resp. `QUAL_ESTIMATED`) with
  the year parsed, **not** a `MOD_TEXTONLY`/text date — matching the all-uppercase `CAL`
  behaviour. Demonstrable by C4-verify importing the GEDCOM snippet and asserting the resulting
  date's quality and value.
- **Invariant to restore:** GEDCOM approximate-date qualifier keywords (`CAL`, `EST`, `INT`)
  are recognised on import case-insensitively and resolve to the correct `Date` quality — lenient
  import of the GEDCOM date-qualifier set, the same leniency the internal date parser already
  applies to modifier words (`ABT`/`BEF`/`AFT`) that travel inside the date text. (Internal
  Gramps GEDCOM-import robustness rule; no external canon — GEDCOM 5.5.1 specifies uppercase, but
  Gramps imports permissively from non-conformant exporters.) SELF-TEST: the property is over the
  qualifier-keyword class, not the one string `"Cal"` — a fix must not just special-case that
  token.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Scope:** the GEDCOM date-qualifier extraction in `gramps/plugins/lib/libgedcom.py`. The
  module-level `MOD` regex (`libgedcom.py:886`, `re.compile(r"\s*(INT|EST|CAL)\s+(.*)$")`) is
  case-sensitive, so `__extract_date` (`libgedcom.py:1093`, matched at `:1103`) never matches
  `Cal`/`Est`/`Int`, leaving `qual = QUAL_NONE` and passing the literal text through unparsed.
  Restore case-insensitive recognition of the qualifier so mixed-case `Cal 1847` is extracted as
  the calculated quality. NOTE for Do: recognising the keyword is necessary but not sufficient —
  the captured qualifier is then looked up in `QUALITY_MAP` (`mod, text = match.groups()` →
  `QUALITY_MAP.get(mod, QUAL_NONE)`), whose keys are uppercase, so a complete fix must also
  normalise the captured token before that lookup (a case-insensitive match that still feeds
  `"Cal"` to `QUALITY_MAP` yields `QUAL_NONE` and ships a half-fix). Mechanism is Do's to choose.
  / out of scope: calendar-escape (`@#D…@`) handling, range/span parsing, and the bare-numeric-
  DATE warning — leave those date paths untouched.
- **Repro instruction:** On maintenance/gramps61, import a minimal GEDCOM containing
  `1 BIRT` / `2 DATE Cal 1847`; inspect the imported person's birth date — it is text, and
  Tools → Utilities → Verify the Data flags it. The same file with `CAL 1847` imports as
  Calculated.
- **Test file:** gramps/plugins/importer/test/importgedcom_caldate_test.py — a new core
  `*_test.py` alongside the existing `importgedcom_ambiguous_date_test.py`, driving the
  **production** GEDCOM import (feed the GEDCOM snippet through the real importer/`GedLine`
  date extractor) and asserting the resulting `Date` has `QUAL_CALCULATED`. It MUST drive the
  real extractor, not a copy of the regex.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** adds `gramps/plugins/importer/test/importgedcom_caldate_test.py`
  (a test, no translatable strings) → register in `po/POTFILES.skip`.
- **Prior-art check (triage cycles):** `git log upstream/maintenance/gramps61 --
  gramps/plugins/lib/libgedcom.py` — the most recent date-related commit warns on bare-numeric
  DATE values; no CAL/EST/INT case-sensitivity fix. Merged history clean; closed-PR search by
  this path advised at review.
- **Mantis:** 8850
- **Disposition hint:** likely-fix

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: The libgedcom.py fix (re.IGNORECASE + mod.upper()) is correct — manual red→green confirmed. The test (importgedcom_caldate_test.py) is buggy and failed the Docker gate. Two concrete candidates to fix: 1. CliUser(callback=...) — verify User accepts a callback kwarg on maintenance/gramps61; if not, remove it. 2. gramps_id format — test expects "I1"/"I2" etc.; Gramps likely assigns "I0001" style. Fix the lookup to match actual ID format. Fix the test scaffolding, rerun run-verify.sh, get C4 green. No change needed to the production fix.
- Failing gate: C4 fix verified: test red pre-fix, green post-fix — → essential-line retry for 6.1 also FAILED — a real failure, not a missing prerequisite.
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
