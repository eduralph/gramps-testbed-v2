# Brief — issue glade-setattr / glade-setattr-name-mangling

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** glade-setattr-name-mangling
- **Defect:** `gramps/gui/glade.py` — `Glade(Gtk.Builder).__setattr__` (~L62–69) raises `AttributeError: Ad-hoc attribute _Glade__dirname is not permitted.` whenever a `Glade()` is constructed, blocking GUI startup (reds the `T3-interface` smoke; testbed #1). Two bugs were introduced by `f8c1fc0f50` ("Don't use slots on GObject-derived classes.", on `maintenance/gramps61` and `master`): (1) the guard whitelist lists the **unmangled** names `"__toplevel"/"__filename"/"__dirname"`, but `__init__` assigns `self.__dirname`/`self.__filename`/`self.__toplevel`, which Python name-mangles to `_Glade__dirname` etc. → rejected by the guard; (2) `super().__setattr__(self, name, value)` passes `self` twice — a bound `super()` method already carries it — so once the guard is satisfied it raises `TypeError`. Both confirmed in `git -C ../gramps show maintenance/gramps61:gramps/gui/glade.py` (setattr ~L62–69; mangled assignments at the `self.__dirname, self.__filename = os.path.split(path)` line and the `self.__toplevel = …` lines).
- **Success criterion:** constructing `Glade()` (and loading a real `.glade` file) raises no `AttributeError`/`TypeError`; the `T3-interface` smoke launches the GUI.
- **Repo + branch target**: gramps-project/gramps @ maintenance/gramps61
- **Target note:** core fix per INTEGRATION §2; the maintainer cherry-picks `maintenance/gramps61` forward to `master`.
- **Scope:** the two-line fix to `Glade.__setattr__` — whitelist the **mangled** attribute names and drop the duplicate `self` from the `super().__setattr__` call / out of scope: any other refactor of `glade.py`, touching `__init__`, or reworking how the slots-removal in `f8c1fc0f50` was done elsewhere.
- **Repro instruction:** on `maintenance/gramps61`, headless: `python -c "from gramps.gui.glade import Glade; Glade()"` → raises `AttributeError: Ad-hoc attribute _Glade__dirname is not permitted.` (and a `TypeError` on the `super().__setattr__` path once the whitelist is corrected). The fix makes the construction succeed.
- **Test file:** `gramps/gui/test/glade_test.py` (new; `*_test.py` suffix per repo convention — `gramps/gui/test/` already holds `display_test.py`, `user_test.py`, `utils_test.py`). Headless, GUI-import-light: asserts `Glade()` constructs without raising, so the C4 headless runner can execute it. Red pre-fix, green post-fix.
- **Citations expected:** Do must cite path:line on `maintenance/gramps61` for every change (the two edited lines in `gramps/gui/glade.py` and the new test).
- **Fix spec (Do builder) — both changes, minimal:**
  ```python
  def __setattr__(self, name, value):
      if not hasattr(self, name) and name not in [
          "_Glade__toplevel", "_Glade__filename", "_Glade__dirname",
      ]:
          raise AttributeError(f"Ad-hoc attribute {name} is not permitted.")
      super().__setattr__(name, value)
  ```
- **Prior-art check (triage cycles):** searched by file path. The defect is a regression introduced by `f8c1fc0f50` ("Don't use slots on GObject-derived classes.") on both `maintenance/gramps61` and `master` — verified with `git -C ../gramps log --oneline -1 f8c1fc0f50`. No prior fix on the branch (the buggy guard is still live in `maintenance/gramps61:gramps/gui/glade.py`). Do should confirm no open/closed upstream PR already corrects this guard before opening the draft PR.
- **Verify (Check):** C4-verify proves the new test is **red** with the production change reverted and **green** with the fix. On a green baseline, drop the `_Glade__dirname` signature from `engine/baselines/run-interface.json` and re-promote `T3-interface`.
- **Disposition hint:** likely-fix (regression in `f8c1fc0f50`).

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts. The commit carries `Fixes #0000  (STAND-IN —
replace with the real tracker number before marking the PR ready)`; the PR body
references testbed issue #1 and the `f8c1fc0f50` regression. Swapping `#0000` for
the real number and marking ready are the human's pre-ready steps.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: Rejected: the success criterion — "the T3-interface smoke launches the GUI" — is still red. T3-interface shows a NEW failure `setUpClass (interface.test_smoke.SmokeTest)` not in baseline, so the fix is not demonstrated to restore GUI startup. What to change next: - Address the T3-interface `setUpClass` failure directly: determine whether it is environmental (headless dogtail setUpClass) or a real residual, and get the smoke green for the right reason. The baseline re-promotion can't proceed until it is. - Exercise the real `Glade()` construction path (per brief repro), not only the synthetic `Glade.__new__` + `Gtk.Builder.__init__` bypass, so GUI launch is actually verified end-to-end. Not a concern (do not spend effort here): the missing GPL header on the new test file (T2) — human accepts the test-file convention; that is not blocking.
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
