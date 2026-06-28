# Brief — issue 13354 / mediamanager-tooltip-viz-a-viz-typo

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** mediamanager-tooltip-viz-a-viz-typo
- **Defect:** The Media Manager tool's help/tooltip for "Convert paths from absolute to
  relative" contains the misspelling "viz-a-viz". Verified at
  gramps/plugins/tool/mediamanager.py:640 — `"viz-a-viz the base path as given in the
  Preferences, "`. Correct form is "vis-à-vis" (or "vis-a-vis").
- **Success criterion:** the Media Manager "absolute → relative" help text renders the word as
  "vis-à-vis" (or "vis-a-vis") and no longer contains "viz-a-viz". Demonstrable by C4-verify if
  the help string is reachable via the production path; otherwise see Test file.
- **Invariant to restore:** n/a — non-structural behavioural/string fix (principles.md §1.1).
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Difficulty:** low
- **Scope:** the single misspelled word in the help string at mediamanager.py:640. / out of
  scope: rewording the rest of the (long) tooltip; any path-conversion behaviour.
- **Repro instruction:** on maintenance/gramps61 with example.gramps, Tools → Utilities →
  Media Manager, advance to the "Selection" step, hover "Convert paths from absolute to
  relative" — the tooltip contains "viz-a-viz".
- **Test file:** gramps/plugins/tool/test/mediamanager_test.py (NEW dir+file; no
  `plugins/tool/test/` exists today) asserting the corrected help text via the production
  options path. Because this is a one-word translatable-string fix with no behavioural seam,
  expect C4 `PDCA-UNVERIFIABLE` is the likely outcome — if so, state it; do NOT manufacture
  scaffolding just to give run-verify a file to revert (INTEGRATION.md §3).
- **Citations expected:** Do must cite path:line on the target branch for every change.
- **New/removed files:** if a new core test .py (and `test/__init__.py`) is added, register
  the new file(s) in `po/POTFILES.skip`. Editing the existing English source string needs no
  POTFILES change.
- **Prior-art check (triage cycles):** searched by path `gramps/plugins/tool/mediamanager.py`
  on upstream/maintenance/gramps61 — Black reformat, license text, and `Fix media manager bug
  with relative to absolute path conversion` (fe0f70b018); none corrects the spelling. No
  prior/closed PR found.
- **Mantis:** 13354
- **Disposition hint:** likely-fix
