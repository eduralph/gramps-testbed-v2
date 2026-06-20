# Brief — issue 13966 / prereq-checker-active-page-none

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** prereq-checker-active-page-none
- **Defect:** Closing a family tree with the Prerequisites Checker gramplet on the
  Dashboard prints a traceback to the console: the gramplet's `main()` generator is stepped
  again after tree close, when `self.uistate.viewmanager.active_page` is None, so the
  unguarded `active_page.bottombar` read raises
  `AttributeError: 'NoneType' object has no attribute 'bottombar'`.
- **Success criterion:** `main()` reads `active_page` into a local and returns early when it
  is None, so closing the tree produces a clean close with no console traceback; the
  remaining bottombar / db-open / count short-circuit chain runs unchanged. Already merged
  on the target branch — the brief confirms the guard + test are present; there is no
  patch.diff to carry, so the bundle is discontinued as superseded, with the PR referenced.
- **Repo + branch target:** gramps-project/addons-source @ maintenance/gramps60
  (PR 913 merged to both maintenance/gramps60 and maintenance/gramps61)
- **Surfaces:** data (gramplet lifecycle; the symptom is a console message, no GUI assert).
- **Scope:** confirm the already-merged guard + regression test are present and close. /
  out of scope: any new change; the gramps60-vs-61 branch question is resolved (the fix is
  on both).
- **Repro instruction:** Install Prerequisites Checker, add it to the Dashboard, open then
  close a family tree while on the Dashboard. Pre-fix: the AttributeError traceback prints.
  Post-fix: clean close.
- **Test file:** addons-source
  `PrerequisitesCheckerGramplet/tests/test_main_active_page_none.py` (already shipped with
  the merged fix; reproduces the traceback with a stub uistate whose active_page is None,
  plus the dashboard / non-dashboard short-circuit guard cases) — no new test needed.
- **Citations expected:** n/a (no new patch). Guard present at
  PrerequisitesCheckerGramplet/PrerequisitesCheckerGramplet.py:171–176
  (`active_page = self.uistate.viewmanager.active_page; if active_page is None: ... return`).
- **Prior-art check (triage cycles):** searched by file path
  PrerequisitesCheckerGramplet/ on maintenance/gramps60 and gramps61 — fixed and merged via
  PR 913 ("PrerequisitesCheckerGramplet: guard active_page on tree close (bug 13966)"),
  present on both branches with the test.
- **Mantis:** 13966
- **Disposition hint:** likely-close

## STOP discipline

Draft only until Check sign-off. No patch.diff to carry — already merged.
**Recommended sign-off disposition: `discontinue`** (`pdca signoff --discontinue`),
superseded by addons-source PR 913 (merged to gramps60 + gramps61) — per INTEGRATION §7.
No new PR.
