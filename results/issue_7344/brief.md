# Brief — issue 7344 / addon-setup-locale-path-dead-slice

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** addon-setup-locale-path-dead-slice
- **Defect:** Reported (2013, addons for Gramps 4.0.x): addon translation `.mo` files landed at
  a wrong path for locales whose code is longer than 2 chars (e.g. `pt_BR`, `zh_CN`) because the
  build computed the locale with a fixed-width slice `locale = po[length-11:length-9]`.
  **Likely already fixed:** in the current build tooling
  (../addons-source setup.py, line 787 on maintenance/gramps60) that slice is **dead code** —
  the very next line `(locale_path, locale) = po.rsplit('/', 1)` overwrites `locale`, and the
  locale is then derived as `locale[:-9]` (strip `-local.po`), which is correct for any code
  length. The compile step (setup.py:683–684, 774) already uses `os.path.basename(po[:-3])`.
  This bundle VERIFIES the multi-char-locale path is now correct and, if so, removes the dead
  slice rather than shipping a behavioural change.
- **Success criterion:** building/compiling an addon that has a `pt_BR` (or other >2-char)
  translation produces `<Addon>/locale/pt_BR/LC_MESSAGES/addon.mo` — the correct path; the
  original wrong-path defect does not reproduce. The dead `locale = po[length-11:length-9]` line
  is removed without changing the produced paths.
- **Invariant to restore:** n/a — non-structural build-tooling fix (principles.md §1.1).
  (Correctness requirement: the locale segment of an addon `.mo` path is the full locale code,
  independent of its character length.)
- **Repo + branch target:** gramps-project/addons-source @ maintenance/gramps60
- **Surfaces:** data
- **Difficulty:** low
- **Scope:** the dead fixed-width locale-slice in the addons build/`languages` step (and
  confirming the live `rsplit`-based derivation handles >2-char codes). / out of scope: the
  per-addon compile/listing logic that already derives the locale correctly; any addon's own
  contents.
- **Repro instruction:** on ../addons-source @ maintenance/gramps60, inspect setup.py:786–789;
  confirm `po[length-11:length-9]` is immediately overwritten by `po.rsplit('/', 1)` so the
  produced `languages`/path use `locale[:-9]` (full code). Exercise with a po named
  `<Addon>/po/pt_BR-local.po`.
- **Test file:** none practical — build/packaging tooling. Expect C4 `PDCA-UNVERIFIABLE`
  (no red→green test seam); the change is verified by reading the path derivation and a manual
  build. State the manual repro in build-notes.
- **Citations expected:** Do must cite path:line on the target branch for every change.
- **New/removed files:** none (addons-source build script; not core, no POTFILES).
- **Prior-art check (triage cycles):** searched by path `setup.py` on
  upstream/maintenance/gramps60 — recent commits `Update to current FSF address (#186)`
  (0e8934321) and whitespace (dece286af); the rsplit-based derivation that supersedes the buggy
  slice is already present. No open/closed PR specifically removing the dead slice found.
- **Mantis:** 7344
- **Disposition hint:** POSSIBLY-FIXED → verify first

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: setup.py has been superseded by make.py as the primary addon build tool (README documents all commands via `python3 make.py gramps60 ...`). make.py has the identical dead-slice bug at line 165 (`locale = po[length - 11 : length - 9]`, immediately overwritten by `po.rsplit(os.sep, 1)`). The patch fixes the legacy file and leaves the active one broken. Redirect the 2-line deletion to make.py (and optionally also setup.py for completeness). Note in build-notes whether the Weblate path (active for gramps60+) bypasses this code entirely.
- Failing gate: T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix) (advisory) — T3-baseline [delta]: DELTA: 4 new failure(s) not in baseline: LifeLineChartView.collection::import_or_collection, PDFFor
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
