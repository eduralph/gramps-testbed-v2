# Brief — issue 11589 / pluginmanager-uninstall-destroys-shared-dir

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** pluginmanager-uninstall-destroys-shared-dir
- **Defect:** In the enhanced Plugin Manager addon, uninstalling a single add-on
  filter rule deletes the **entire** shared `FilterRules` plugin directory — all
  the other rules in the pack *and* any unrelated user content (sub-folders, files)
  the user placed there. Root cause: `__uninstall` calls
  `shutil.rmtree(pdata.fpath)` on the plugin's *directory* (`PluginManager.py:349`),
  but `pdata.fpath` is the directory shared by every plugin in a multi-plugin pack
  (the FilterRules pack ships 13 `*.gpr.py`/`*.py` rule pairs in one directory —
  `../addons-source/FilterRules/`), so the whole directory and its contents are
  wiped regardless of which single rule was selected.
- **Success criterion:** Uninstalling one plugin whose directory is shared by other
  registered plugins removes only the files belonging to the selected plugin; the
  sibling plugins' files and any unrelated files/sub-folders in that directory
  survive, and the directory itself is **not** removed while other registered
  plugins still live in it. (Uninstalling a plugin that is the sole occupant of its
  own directory must still remove the directory, preserving today's behaviour.)
- **Repo + branch target:** addons-source @ `maintenance/gramps60` (addons
  production branch per INTEGRATION §2; maintainer cherry-picks forward to gramps61).
- **Scope:** Make `PluginManager.__uninstall` (`../addons-source/PluginManager/PluginManager.py:339-358`)
  non-destructive for shared directories: before `shutil.rmtree`, determine whether
  any *other* registered plugin shares `pdata.fpath` (enumerate via `self._preg`);
  if so, delete only the selected plugin's own file(s) (its `pdata.fname` `.py` and
  the `*.gpr.py` that registers it) and leave the directory and everything else in
  place; only `rmtree`/`rmdir`/`unlink` the directory when the selected plugin is its
  sole registered occupant. /
  **out of scope:** repackaging the FilterRules pack into one-directory-per-rule
  (the alternative the maintainer floated in the Mantis thread — a packaging change
  to FilterRules, not a manager bug); the reporter's secondary observation that all
  rules show as installed/uninstalled together (that is inherent to single-`.addon.tgz`
  distribution and a separate logical change); the core (built-in) plugin manager;
  changing the install path.
- **Repro instruction:** With the FilterRules pack installed (its rules live in one
  shared `FilterRules` directory). Add a sub-folder + a dummy file inside that
  directory. Open Gramps → Help → Plugin Manager (enhanced); filter to `rule`;
  select **one** rule and click **Uninstall**. Observed: the whole `FilterRules`
  directory is deleted — every rule and the user's sub-folder/file are gone. Expected:
  only the selected rule's files are removed; the other rules and the user content
  remain.
- **Test file:** `../addons-source/PluginManager/tests/test_uninstall_shared_dir.py`
  (addon convention per INTEGRATION §3 — `tests/` package, `test_*.py` prefix,
  alongside the existing `tests/test_info_empty_requires.py`). Follow that file's
  display-skip + `__new__`-bypass pattern: build a `PluginManager` instance via
  `__new__`, point `pdata.fpath` at a temp dir seeded with several rule
  `*.gpr.py`/`*.py` pairs plus an unrelated sub-folder/file, stub `self._preg` so it
  reports multiple registered plugins sharing that `fpath`, stub the GUI mutators
  (`__rebuild_reg_list`, dialogs), call the name-mangled `_PluginManager__uninstall`,
  then assert the directory still exists, the sibling rule files and the unrelated
  user content survive, and only the selected rule's files were removed. Must fail
  pre-fix (the temp dir is wiped) and pass post-fix.
- **Citations expected:** Do must cite path:line on the target branch for every change.
- **Prior-art check (triage cycles):** Searched `addons-source` history by file path —
  `git -C ../addons-source log -S "shutil.rmtree" -- PluginManager/PluginManager.py`
  returns only `00794ec32` ("An enhanced addon/plugin manager (#78)"), i.e. the
  `rmtree(pdata.fpath)` uninstall logic is unchanged since the addon was introduced;
  no later fix on any branch. Most recent PluginManager work (`7a0cbdcf1` empty
  `requires_exe`, `e700649d9` linting) does not touch `__uninstall`. No prior fix or
  open PR found for this defect.
- **Disposition hint:** likely-fix (Mantis status `confirmed`; root cause confirmed
  in source and corroborated by maintainer prculley in the thread).

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
