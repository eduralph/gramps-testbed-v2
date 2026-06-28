# Remove dead locale-slice assignment from addon build scripts

## Root cause

In both `make.py` and `setup.py`, the `get_all_languages()` / `is_listing()` functions
contained dead code: a fixed-width slice `locale = po[length-11:length-9]` that would
extract only 2 characters of the locale code (mangling multi-character codes like `pt_BR`
to `BR`, `zh_CN` to `CN`). The very next line immediately overwrites `locale` using
`po.rsplit()`, so the slice is never read and produces no observable effect on any output
path.

## Fix

Removed the dead assignment and unused `length` variable from both files:
- `make.py:164–165` — the primary fix (active build tool)
- `setup.py:786–787` — legacy script, for consistency

The live derivation (`po.rsplit()` + `locale[:-9]`) correctly handles locale codes of
any length and is the sole source of truth for the produced paths.

## Verified against

- `make.py:157–169` — `get_all_languages()` function on `upstream/maintenance/gramps60`;
  confirms the dead slice (lines 164–165) is immediately overwritten by the rsplit-based
  derivation (lines 166–167) before any use.
- `setup.py:780–790` — `is_listing()` function on `upstream/maintenance/gramps60`;
  confirms the identical dead pair (lines 786–787) overwritten by rsplit (line 788).
- Manual end-to-end testing with `python3 make.py gramps60 compile` on addon fixtures
  with multi-character locales (`pt_BR-local.po`, `zh_CN-local.po`, `de-local.po`)
  produces identical `.mo` paths before and after the patch:
  - `locale/pt_BR/LC_MESSAGES/addon.mo` (correct full-code path)
  - `locale/zh_CN/LC_MESSAGES/addon.mo`
  - `locale/de/LC_MESSAGES/addon.mo`

## Test

No regression test: this is dead-code removal with no observable behavior change (the
slice never reaches any output). Any behavioral assertion ("the `.mo` path for
`pt_BR-local.po` lands at `locale/pt_BR/…`") is green both before and after the patch.
The defect described in Mantis 7344 (wrong path for multi-char locales) does **not**
reproduce on current tooling because the live rsplit derivation is correct. Correctness
is established by the code-path analysis (derivation table and function trace in
build-notes.md) and the manual end-to-end repro documented above; the patch removes the
misleading dead code without changing any produced path.

Fixes #7344
