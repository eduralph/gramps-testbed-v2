# Brief — issue 14014 / importxml-compound-date-empty-bound

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** importxml-compound-date-empty-bound
- **Defect:** Importing a Gramps XML (.gramps / .gpkg backup) that contains a daterange
  or datespan with an empty `start` or `stop` attribute raised
  `IndexError: string index out of range` at
  `gramps/plugins/importer/importxml.py` `start_compound_date()` (`if stop[0] == "-":`),
  aborting the whole import. Reported on 6.0.5 (backup made on 6.0.x, restored on 6.0.5).
- **Success criterion:** Importing a Gramps XML containing a date range/span with an
  empty bound completes without `IndexError`; the date imports as the corresponding
  open-ended range. The reported traceback no longer occurs.
- **Invariant to restore:** n/a — non-structural behavioural bug fix (principles.md §1.1).
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** low
- **Scope:** confirm the empty-bound guard is present on the contribution target and the
  reported repro no longer raises. / out of scope: producing a new patch — the fix
  **already landed upstream** (commit 1c411ea3ed "Catch IndexError in importxml", David
  Straub), so this bundle is a verification, not a re-fix.
- **Repro instruction:** Construct a minimal Gramps XML with a `<daterange start=""
  stop="1900"/>` (or empty `stop`) on an event and import it via the XML importer; pre-
  fix raises `IndexError` at start_compound_date, post-(already-)fix imports cleanly.
- **Test file:** gramps/plugins/importer/test/importxml_daterange_test.py (new) — a
  regression test that imports such an XML and asserts no `IndexError` and the expected
  open-ended date. NOTE: because the fix is already in the tree there is no patch to
  revert, so the C4 red→green mechanic cannot run — `run-verify` will emit
  `PDCA-UNVERIFIABLE` and route to §6 NEEDS-HUMAN (expected for a verify-first). The test
  still ships and must pass on the current target.
- **Citations expected:** Do must cite path:line on maintenance/gramps61.
- **New/removed files:** adds gramps/plugins/importer/test/importxml_daterange_test.py
  (no translatable strings) → po/POTFILES.skip. (importer/test/ already exists.)
- **Prior-art check (triage cycles):** searched gramps/plugins/importer/importxml.py
  history on the pinned worktrees — commit **1c411ea3ed** "Catch IndexError in importxml"
  guards `start`, `stop` and `val` (`if start and start[0] == "-"`, etc.) at lines
  ~2553 / 2573 / 2658, present on BOTH upstream/maintenance/gramps60 and
  upstream/maintenance/gramps61. Authored 2025-11-15, after this report (2025-10-13).
  **Fix already merged** — this is verify-first.
- **Mantis:** 14014
- **Disposition hint:** POSSIBLY-FIXED → verify first

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI). The PR MUST NOT be marked ready
before sign-off accepts.
