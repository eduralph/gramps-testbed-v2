# Brief — issue 13979 / pluginmanager-info-empty-requires

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** pluginmanager-info-empty-requires
- **Defect:** In the Plugin Manager Enhanced addon, clicking the "PostgreSQL Enhanced" row
  crashes with `IndexError: list index out of range` at `PluginManager.py` `__info`
  (`txt = " ".join(req_lst[0])`): the requirements list `req_lst` is empty for that plugin
  (it declares an empty `requires_exe`), so `req_lst[0]` is out of range. The addon is in
  addons-source (verified — `PluginManager/`), not gramps core's Addon Manager.
- **Success criterion:** `__info` guards the empty-requirements case (skips the row build
  when `req_lst` is empty) so selecting a plugin with no requirements no longer raises
  IndexError. Already merged on the target branch — the brief confirms the guard + test are
  present; there is no patch.diff to carry, so the bundle is discontinued as superseded,
  with the PR referenced.
- **Repo + branch target:** gramps-project/addons-source @ maintenance/gramps60
  (PR 916 merged to both maintenance/gramps60 and maintenance/gramps61)
- **Surfaces:** gui (plugin-list interaction; tree-independent).
- **Scope:** confirm the already-merged empty-requires guard + test are present and close. /
  out of scope: the SEPARATE "installs but doesn't actually install via the core Addon
  Manager" symptom (note 2) — a different defect, not bundled here (one issue per ticket);
  raise it separately if it reproduces.
- **Repro instruction:** With Plugin Manager Enhanced installed and the PostgreSQL Enhanced
  row present, click that row. Pre-fix: IndexError at the `" ".join(req_lst[0])` site.
  Post-fix: the row's info renders with no requirements line.
- **Test file:** addons-source `PluginManager/tests/test_info_empty_requires.py` (already
  shipped with the merged fix; constructs the entry that yields an empty `req_lst` and
  asserts no IndexError) — no new test needed.
- **Citations expected:** n/a (no new patch). Guard present at
  PluginManager/PluginManager.py:653–663 (`req_lst = info[i + 1]; if not req_lst: ...
  continue` before `txt = " ".join(req_lst[0])`).
- **Prior-art check (triage cycles):** searched by file path PluginManager/ on
  maintenance/gramps60 and gramps61 — fixed and merged via PR 916 ("Fix IndexError when an
  addon declares an empty requires_exe", bug 13979), present on both branches with the test.
- **Mantis:** 13979
- **Disposition hint:** likely-close

## STOP discipline

Draft only until Check sign-off. No patch.diff to carry — already merged.
**Recommended sign-off disposition: `discontinue`** (`pdca signoff --discontinue`),
superseded by addons-source PR 916 (merged to gramps60 + gramps61) — per INTEGRATION §7.
No new PR.
