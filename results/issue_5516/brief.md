# Brief — issue 5516 / date-quality-keyword-matches-inside-word

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** date-quality-keyword-matches-inside-word
- **Defect:** Entering a free-text date that merely *contains* a date quality/modifier
  keyword as a substring of an ordinary word silently mangles the text. The reporter's
  case: typing `Test data` stores `Tdata`. Root cause (verified): `DateParser.match_quality`
  (gramps/gen/datehandler/_dateparser.py:880–890) matches with
  `self._qual = re.compile(r"(.* ?)%s\s+(.+)" % self._qual_str, re.IGNORECASE)`
  (line 528), where `_qual_str` includes `est`/`est.`. The leading `(.* ?)` is not anchored
  to a word boundary, so for `Test data` it matches group(1)=`T`, the quality token
  `est` inside `Test`, then group(3)=`data` — the parser strips `est ` and yields `Tdata`,
  marking the date estimated. The same substring hazard exists for other quality/modifier
  tokens embedded in unrelated words.
- **Success criterion:** `DateParser().parse("Test data")` returns a date whose text is
  preserved as `Test data` (a free-text date), NOT `Tdata`, and whose quality is not set to
  estimated; genuine quality-prefixed dates (e.g. `est 1900`, `estimated 1900`, `calc 1900`)
  still parse to QUAL_ESTIMATED/QUAL_CALCULATED as before. Demonstrable by C4-verify against
  gramps/gen/datehandler/test/dateparser_test.py.
- **Invariant to restore:** n/a — non-structural behavioural bug fix (principles.md §1.1).
  (Correctness requirement: a date quality/modifier keyword is recognised only as a whole
  token, never as a substring inside an unrelated word.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** medium
- **Scope:** the quality/modifier text-stripping that fires when the keyword appears as a
  substring of an unrelated word, corrupting otherwise-free-text date input. / out of scope:
  the genuine parsing of real quality-prefixed and modifier-prefixed dates (these must keep
  working); locale-specific quality strings beyond ensuring the same whole-token behaviour.
- **Repro instruction:** on maintenance/gramps61, `from gramps.gen.datehandler import parser;
  d = parser.parse("Test data")` — observe the stored value is `Tdata` (and quality estimated)
  instead of the free text `Test data`. (GUI: add an event, type `Test data` in the Date field.)
- **Test file:** gramps/gen/datehandler/test/dateparser_test.py (add a case; existing file —
  drive the production `DateParser.parse` path).
- **Citations expected:** Do must cite path:line on the target branch for every change.
- **New/removed files:** none (test added to an existing file).
- **Prior-art check (triage cycles):** searched by path
  `gramps/gen/datehandler/_dateparser.py` on upstream/maintenance/gramps61 — only Black
  reformat (b3a5cf346f) and license-text (d82eb0f460) commits touch it; no functional fix for
  substring quality-matching. No prior/closed PR found for this path.
- **Mantis:** 5516
- **Disposition hint:** likely-fix
