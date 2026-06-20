# Build notes — issue 11589 / pluginmanager-uninstall-destroys-shared-dir

> Withheld from the reviewer. Rationale for the human at sign-off.

## Root cause (confirmed in source)

`__uninstall` (`addons-source` @ `maintenance/gramps60`,
`PluginManager/PluginManager.py:339-358`) deletes the plugin's *directory*
unconditionally — `shutil.rmtree(pdata.fpath)` at `PluginManager.py:349`.
`pdata.fpath` is the directory the plugin's files live in, not a per-plugin
folder. The FilterRules pack ships ~13 rule `*.gpr.py`/`*.py` pairs in one
shared directory (`addons-source/FilterRules/`, confirmed by `ls`), so
uninstalling one rule rmtree's the whole pack plus any unrelated user content in
that directory. `pdata.fpath`/`pdata.fname` semantics confirmed in
`gramps/gen/plug/_pluginreg.py:264-267` (PluginData docstring: fname = the
python file, fpath = the directory).

## Note on the class name (brief imprecision, not a defect to fix)

The brief calls the method `PluginManager.__uninstall` /
`_PluginManager__uninstall`. The method at `PluginManager.py:339` actually lives
in **`class PluginStatus`** (`PluginManager.py:126`), so the real name-mangled
symbol is `_PluginStatus__uninstall`. I followed the source, not the label — the
brief's line citation (339-358) is unambiguous. The test calls
`_PluginStatus__uninstall`.

## The fix

Two private helpers + a branch in `__uninstall`:

- `__plugins_sharing_dir(pdata)` — enumerates registered plugins via
  `self._preg`, returning those (other than `pdata`) whose `fpath` equals
  `pdata.fpath`. It reuses the file's own enumeration idiom — iterate
  `PTYPE_STR` and call `self._preg.type_plugins(ptype)` — which already appears
  at `PluginManager.py:777-778` (`PTYPE_STR` imported at `PluginManager.py:65`;
  `type_plugins` defined in `gramps/gen/plug/_pluginreg.py:1534-1538`). Results
  are de-duplicated by `id` and the selected plugin excluded by `id`.
- `__remove_plugin_files(pdata, siblings)` — removes only the selected plugin's
  own implementation file (`pdata.fname`) and the matching `*.gpr.py` (derived
  from the implementation basename, matching the FilterRules pairing
  convention). Guard: if a sibling is registered from the *same* `.py`
  (`pdata.fname` in the siblings' fnames — e.g. `hasrolerule.gpr.py` registers
  two rules off one `hasrolerule.py`), it removes nothing, so a still-registered
  sibling can't lose its files.
- `__uninstall` now computes `siblings` first; if non-empty it calls
  `__remove_plugin_files` (directory and other contents preserved); otherwise it
  keeps the **unchanged** sole-occupant path (islink→unlink /
  junction→rmdir / else→`shutil.rmtree`). So the only behavioural change is for
  shared directories — sole-occupant uninstall is byte-for-byte the old logic.

`self._pmgr.get_plugin` (line 341) and `self._preg.get_plugin` return the same
PluginData objects — `GuiPluginManager.get_plugin` delegates to the registry
(`gramps/gen/plug/_manager.py:419-423`) — so enumerating via `_preg` and
selecting via `_pmgr` is consistent.

## Alternatives ruled out

- **Repackage FilterRules into one-dir-per-rule** — explicitly out of scope
  (brief): a packaging change to a different addon, not a manager bug.
- **Match siblings by gpr filename rather than fname** — PluginData stores no
  gpr filename; the only robust signal is `fname` + the basename convention.
  Deriving `base + ".gpr.py"` matches every FilterRules pair and the test
  fixture; documented as the intended behaviour per the brief.
- **Normalising `fpath` before comparison** — the existing code compares fpath
  as a plain string (`PluginManager.py:780`); registry values are consistent, so
  I kept plain `==` for parity.

## Test — `PluginManager/tests/test_uninstall_shared_dir.py`

Follows `tests/test_info_empty_requires.py`: `@skipUnless(_HAS_GTK_DISPLAY)` +
`__new__`-bypass (PluginManager.py imports Gtk at module load). Two cases:

1. `test_uninstall_shared_dir_keeps_siblings_and_user_content` — temp dir seeded
   with a selected rule pair, a sibling rule pair, and an unrelated
   sub-folder+file; `_pmgr.get_plugin` returns the selected pdata,
   `_preg.type_plugins` reports both rules as registered in that dir. Asserts the
   dir survives, the sibling pair and user content survive, only the selected
   pair is removed. **Red pre-fix** (rmtree wipes the dir).
2. `test_uninstall_sole_occupant_still_removes_directory` — guards the preserved
   behaviour; passes both pre- and post-fix.

The module is RED pre-fix because case 1 fails (case 2 passing doesn't save it),
and GREEN post-fix.

### Stub bug I had to fix in the prior-cycle draft

An untracked draft of this test was present in the checkout. Its
`_preg.type_plugins` stub used `lambda ptype, _first=[True]: all_plugins if
_first.pop() else []`. Because `__plugins_sharing_dir` calls `type_plugins`
**once per `PTYPE_STR` key** (not once total), the second call hit
`[].pop()` → `IndexError`, which would have made the *post-fix* run error out.
Fixed to `_first and _first.pop()` so subsequent calls short-circuit to `[]`.
Caught by the standalone simulation below; the draft would have failed C4-verify.

## Verification performed

- `git apply --check` of `patch.diff` against the live `addons-source` checkout:
  clean. `py_compile` of both patched files: OK.
- **Standalone algorithm simulation** (`/tmp/sim_11589.py`, no Gtk import):
  replicated `__uninstall`/`__plugins_sharing_dir`/`__remove_plugin_files` and
  the original rmtree logic against the test's exact fixture + stubs. Result:
  PRE-FIX module fails (shared-dir case FAIL, sole-occupant PASS) → RED;
  POST-FIX both PASS → GREEN.
- **C4-verify (Docker) not run here**: the engine runner shells out to
  `docker run`, which requires an approval I can't grant in this session. The
  authoritative red→green gate (`run-verify.sh`, MODE=addon, module
  `PluginManager.tests.test_uninstall_shared_dir`) must be run by Check / the
  human. The standalone sim + clean apply + compile are the evidence I could
  produce; they validate the logic but not the live Gtk-import integration.
