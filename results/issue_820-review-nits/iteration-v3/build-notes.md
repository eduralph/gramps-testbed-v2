# Build notes — 820-review-nits (iteration 3)

Target branch: `origin/feature/ci-cd-pipeline-upstream` (addons-source, tracks
`maintenance/gramps60`). Verified against the `addons-source-6.0-fork` worktree at that
branch. All `path:line` citations below are on that branch (worktree HEAD
`67ed38d39`).

## What changed, per Success-criterion item

### (a) Remove the dead `make_gramps_user()` helper — REMOVED
`git grep make_gramps_user` on the branch finds **only its definition**
(`tests/gramps_test_env.py:116`) — no caller anywhere in the repo. It is dead API, so
removed (the brief allows "wired in or removed"; nothing needs it, so removal is the
minimal resolution). Removed `tests/gramps_test_env.py:116-123` (the `def` + its sole
`from gramps.cli.user import User` local import). `Any` is still used elsewhere in the
file (`:92,:95,:129,:130,:151`), so its import stays.

### (b) Use the public API instead of name-mangled private — `type_plugins()` sweep
`_get_addon_plugins` reached `registry._PluginRegister__plugindata`
(`tests/test_plugin_registration.py:74`). Replaced with a union over the public
`registry.type_plugins(ptype)` for `ptype in (None, *PTYPE)`
(`tests/test_plugin_registration.py:72-78` → new `:167-176`).

**This is the exact point iteration 1 rejected**, so the reasoning is spelled out and
verified against gramps source (`gramps/gen/plug/_pluginreg.py`, both 6.0 and 6.1):
- `type_plugins(ptype)` is `[x for x in __plugindata if x.ptype == ptype]`
  (`_pluginreg.py:1534-1538`).
- `PluginData._ptype` defaults to `None` (`_pluginreg.py:465`); the `ptype` *getter*
  returns `_ptype` verbatim (`:627-628`), and the *setter* raises unless the value is in
  `PTYPE` (`:631-634`). So every record's ptype is in `{None} ∪ PTYPE`, and exactly one
  of those buckets.
- iteration 1's objection was that the naive `for ptype in PTYPE` form (no `None`)
  **silently drops** a half-registered, typeless (`_ptype is None`) addon — making the
  very registration-failure class this smoke test exists to catch invisible. The
  `(None, *PTYPE)` sweep keeps `None` in the cover, so a typeless pdata still surfaces
  and FAILS the test. The union therefore reproduces the old `__plugindata` master list
  **exactly** (complete cover, no record under two types) — equivalence preserved, no
  silent coverage loss.

Rejected alternative: a public "all plugins" accessor. There is none —
`_pluginreg.py:1534-1654` exposes only `type_plugins(ptype)` and per-type wrappers
(`report_plugins`, `tool_plugins`, …), no `all_plugins()`. So the `(None, *PTYPE)` union
is the cheapest public-API equivalent (one extra `PTYPE` import, one nested
comprehension; vs. patching gramps core to add an accessor — out of scope and a
cross-repo change).

### (c) Path-prefix check, not substring — extracted predicate + unit test
The three `ADDONS_ROOT in pdata.fpath` substring tests
(`tests/test_plugin_registration.py:76`, `:253`, `:285`) are replaced with
`is_in_addons_tree(fpath, ADDONS_ROOT)`, a prefix check
(`startswith(addons_root + os.sep)`). A sibling checkout sharing the name prefix
(`/work/addons-source-6.1/...` vs root `/work/addons-source`) is a *substring* match but
a *different directory*; the prefix check rejects it.

The predicate lives in a new **import-light** module `tests/addon_paths.py` (no
`gi`/`gramps` imports) so it is unit-testable headless. Production routes through it —
`test_plugin_registration.py` imports and calls the same function, so the test exercises
the real path, not a copy. The new unit test `tests/test_addon_paths.py` asserts the
prefix-vs-substring contract (`test_sibling_sharing_name_prefix_not_matched`) plus the
direct/nested/empty/None cases.

### (d) Include `.gpr.py` in the compile-check `py_compile` pass
Dropped `! -name '*.gpr.py'` from the `find` in the compile-check job
(`.github/workflows/ci.yml:162` → new `:168`), and updated the step name + comment
(`:141-143`). `py_compile` only checks *syntax* — it does not execute the descriptor —
so the `register()`/injected globals available only at registration time are irrelevant
and cannot cause a false failure. A `.gpr.py` syntax error is now caught at the compile
stage rather than only later at registration.

### (e) Tighten the branch-filter glob
`maintenance/gramps**` also matches `maintenance/gramps-foo`, which then only fails later
in the setup job's `gramps[0-9][0-9]` ref regex (`ci.yml:46-48`). Tightened both filters
to `maintenance/gramps[0-9][0-9]` so the glob matches exactly the series branches the
setup regex accepts: `ci.yml:23,25` and the companion `docker-build.yml:9`. Comments
cross-reference each other and the setup regex.

## Iteration carry-forward addressed

- **iter-2 C4 "patch does not apply"** — root cause was the patch built against a stale
  copy of `ci.yml` (line numbers had drifted). This rebuild regenerates the diff against
  the current `feature/ci-cd-pipeline-upstream` worktree; `git apply --check` is clean
  and `run-verify.sh` ran red→green (below).
- **iter-1 (b) equivalence** — addressed via the `(None, *PTYPE)` cover, with the source
  citations above proving no typeless record is dropped.
- **T5 / one-logical-change** — the harness produces a single `patch.diff` per bundle, so
  the five nits ship together here; they are independent and each is an isolated hunk.
  Splitting into separate PRs is a planner/human decision (brief.md:5-6,37). At minimum
  item (b)'s enumeration change is a self-contained hunk
  (`test_plugin_registration.py:72-78`) the human can lift into its own commit/PR if
  desired.
- **T3-61 Sqlite `test_export_sq` delta** — this patch touches no Sqlite code and nothing
  in core export; the delta is 6.1 baseline noise unrelated to this change (carry-forward
  also flagged it as likely baseline noise). Reproduces without this patch.

## C4 verification (the runner, headless addon mode)

`PDCA_BUNDLE=… ./engine/scripts/ubuntu/run-verify.sh`:
```
→ green check (fix applied):  Ran 5 tests ... OK
→ red check (production change reverted, test kept):
   ModuleNotFoundError: No module named 'tests.addon_paths'  (FAILED)
C4-verify: green-with-fix=PASS / red-without-fix=PASS
```
Note on test selection: the runner picks the *last* `test_*.py` in the patch as the unit
under test. Because the patch both modifies `test_plugin_registration.py` (an
env-dependent integration suite that needs PIL/GTK icon themes — fails in the bare C4
env for reasons unrelated to this change) and adds `test_addon_paths.py`, the patch
file-blocks are ordered so `test_addon_paths.py` is last and is the one C4 drives. The
red leg removes the new `tests/addon_paths.py` production module, so the prefix predicate
the test asserts is genuinely the thing under test.

## Commit-readiness notes

- addons-source has **no** `pyproject.toml` / pre-commit config and its CI lints with
  **ruff** (`ci.yml:83`, codes `E9,F63,F7,F82`), not black. New files import and run
  cleanly under the C4 runner (covers E9 syntax + F undefined-name codes); the
  trailing-whitespace lint (`ci.yml:90`) passes on every touched file.
- One incidental note: `black 26.5.0` wants to collapse an *untouched* line
  (`test_plugin_registration.py:145-148`, the `self.fail(...)` concat). Since the branch
  HEAD is not black-clean there already and the repo does not enforce black, that
  reformat was reverted to keep the diff strictly scoped to the five nits.
