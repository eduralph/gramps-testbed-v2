# Brief — issue 7084 / dateparser-partial-date-modifier-roundtrip

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** dateparser-partial-date-modifier-roundtrip
- **Defect:** As filed (2013, against the developer "Check Localized Date Displayer and
  Parser" DateTest tool): a block of dates the date *displayer* renders fail to parse back
  through the date *parser*, so display→parse does not round-trip. The reporter described the
  class as "if `May 1234` is valid, then `before May 1234` should parse the same way"; the
  attached `7084-bad-dates-EN.txt` is dominated by partial dates (month + year, no day) under
  a modifier / quality / dual-year ("slash") context.
- **Success criterion:** **Verify-first, then conditional.** Do MUST first reproduce on
  maintenance/gramps61: run `DateParser` over the `DateDisplay` output for the reporter's
  partial-date classes (e.g. `"before May 1900"`, `"about May 1900"`, `"estimated Jan 1847"`,
  `"May 1900/01"`) and confirm whether any still parse to a text/`MOD_TEXTONLY` date instead
  of an equal `Date`. **If** a live round-trip failure is found, the criterion is: those
  representative partial-date strings parse back to an equal `Date` (right month, year, and
  modifier/quality), demonstrable by C4-verify on a parser round-trip test. **If none
  reproduce** (the likely outcome — see Scope), no production patch ships and the bundle routes
  to §6 NEEDS-HUMAN as a verify-first close. Do MUST NOT manufacture a change to satisfy the
  gate.
- **Invariant to restore:** `DateDisplay → DateParser` round-trips for partial dates: any
  string the displayer produces, the parser parses back to an equal `Date`, and the presence of
  a modifier / quality / dual-year must not regress the month+year (no-day) case to text.
  (Internal Gramps datehandler round-trip contract — the property the DateTest tool exists to
  assert; no external canon.) SELF-TEST: the invariant is over the partial-date *category* under
  all modifier/quality contexts, not one example string.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Scope:** the partial-date (month + year, no day) parse path in the English date parser,
  `gramps/gen/datehandler/_dateparser.py`. **Likely already fixed:** the original report drove
  a developer-only tool; paulfranklin landed `829a8bd01d` "DateParserEN failures under the
  DateTest tool" (2017, in the gramps61 ancestry) for the slash/double-dated cases after
  extensive locale testing in which he could **not** reproduce the reporter's `"before May …"`
  failures, and left the ticket open only "in case others have different results". Subsequent
  round-trip fixes also landed (`dd29d9f29c` "Fix datehandlers for round trip",
  `70520be80c` "Add support for open spans"). So most/all of the reported failures appear
  resolved on gramps61. Do must establish which partial-date strings, if any, *still* fail to
  round-trip before touching parser code, and fix only a confirmed live divergence — ONE logical
  change to partial-date handling, not a sweep of every historical DateTest line. / out of
  scope: non-English parsers (French/Russian inherit the same code but are not this fix's scope
  or success criterion); full-date (with-day) parsing; numeric/ISO formats; the developer
  DateTest tool itself.
- **Repro instruction:** On maintenance/gramps61, parse the displayer's output for partial
  dates under `en_GB.utf-8` — e.g. `DateHandler` parse of `"before May 1900"`, `"about May
  1900"`, `"estimated Jan 1847"`, `"May 1900/01"` — and compare each parsed `Date` to the
  source. (Or run Tools → Debug → "Check the localized date displayer and parser" under
  `en_GB.utf-8` and inspect any partial-date failures.)
- **Test file:** gramps/gen/datehandler/test/dateparser_test.py — IF a live failure is found,
  extend the existing parser test with a partial-date round-trip case set (the representative
  inputs above), driving the **production** `DateParser`/`DateHandler` (no parallel
  re-implementation). Adds no new `.py`. If nothing reproduces, no test/patch ships and the
  bundle routes to §6.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **Prior-art check (triage cycles):** `git log upstream/maintenance/gramps61 --
  gramps/gen/datehandler/_dateparser.py` — `829a8bd01d` (slash-date DateTest failures, 2017) and
  `dd29d9f29c` (round-trip) are both in the gramps61 ancestry; recent commits are black/mypy
  reformat only. Strong signal the reported defect is already largely resolved — closed-PR search
  by this path advised at review.
- **Mantis:** 7084
- **Disposition hint:** POSSIBLY-FIXED → verify first
