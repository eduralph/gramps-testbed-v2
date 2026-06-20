# Brief — issue 14051 / detailed-descendant-book-report-app-ref

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** detailed-descendant-book-report-app-ref
- **Defect:** Generating the Detailed Descendant Book report crashes in `append_event`
  reading `self.report_app_ref[self.phandle][0]`
  (`AttributeError: ... has no attribute 'report_app_ref'` on the reported version;
  `KeyError` on current code). The pre-pass that fills `report_app_ref` runs only under
  `if self.dubperson:` (omit duplicate ancestors), but `append_event` reads it unguarded
  whenever an index option (Index of Dates / Places / Names) is on — so with
  omit-duplicates OFF and an index ON, the table is never populated and the read fails.
- **Success criterion:** With omit-duplicates off and an index option on, the report
  generates without AttributeError/KeyError, and an index entry pins to the FIRST encounter
  of the person (matching the `[0]` semantic the omit-duplicates path emits), so index
  entries resolve to the same canonical position regardless of the omit-duplicates setting.
  Already merged on the target branch — the brief confirms the fix + test are present;
  there is no patch.diff to carry, so the bundle is discontinued as superseded, with the
  PR referenced.
- **Repo + branch target:** gramps-project/addons-source @ maintenance/gramps60
  (PR 914 merged to both maintenance/gramps60 and maintenance/gramps61)
- **Surfaces:** data (report generation; no GUI assert).
- **Scope:** confirm the already-merged populate-on-first-encounter fix + regression test
  are present and close. / out of scope: the secondary "blank Index of Places page with the
  workaround" symptom (note 12) — did not reproduce on example.gramps; if it persists on
  real data it deserves a separate ticket, not this bundle.
- **Repro instruction:** On a tree with a pedigree collapse (duplicate ancestor), generate
  the Detailed Descendant Book with "omit duplicate ancestors" OFF and an index option
  (Names/Dates/Places) ON. Pre-fix: the crash in `append_event`. Post-fix: clean generation
  with first-encounter index parity.
- **Test file:** addons-source
  `DescendantBooks/tests/test_append_event_index_without_omit_duplicates.py` (already
  shipped with the merged fix; covers the crash and the first-encounter parity) — no new
  test needed.
- **Citations expected:** n/a (no new patch). Fix present in
  DescendantBooks/DetailedDescendantBookReport.py `append_event` (lines ~789–819:
  populate-on-miss branch fills `report_app_ref[self.phandle]` pinned to the first
  encounter when the omit-duplicates pre-pass did not).
- **Prior-art check (triage cycles):** searched by file path DescendantBooks/ on
  maintenance/gramps60 and gramps61 — fixed and merged via PR 914 ("DetailedDescendantBook
  Report", bug 14051: "fix index crash when omit-duplicates is off" + "pin Ref to first
  encounter, not current"), present on both branches with the test. Related prior bug 12857
  (note 4) was an incomplete earlier fix, now superseded.
- **Mantis:** 14051
- **Disposition hint:** likely-close

## STOP discipline

Draft only until Check sign-off. No patch.diff to carry — already merged.
**Recommended sign-off disposition: `discontinue`** (`pdca signoff --discontinue`),
superseded by addons-source PR 914 (merged to gramps60 + gramps61) — per INTEGRATION §7.
No new PR.
