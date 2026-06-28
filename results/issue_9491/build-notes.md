# Build notes — issue 9491 / verify-setup-py-replaced-by-pyproject

## Disposition: `not-reproducible` (verify-first close, no patch, no test)

The brief is an explicit verify-first task: *"Verification, not a new fix (no
patch)"* and *"Test file: none"*. The Success criterion is to confirm the
defect's premise no longer holds on the target branch — that the project no
longer ships a directly-executed root `setup.py`, the build is defined by
`pyproject.toml`, and the shebang report is therefore obsolete.

This bundle ships a `close-disposition` (`not-reproducible`) and **no**
`patch.diff` / test / `commit-msg.txt` / `pr-description.md`. An empty
`patch.diff` would break `pdca publish` (a 0-byte patch slips the
`patch.diff.is_file()` guard → `git apply` no-op → `git commit` "nothing to
commit"; pdca-harness #95, observed on bundle 10604), so it is deliberately
absent. The close goes via the disposition fast path; the tracker item is
resolved by hand, not via an upstream PR.

`not-reproducible` is the right token from the configured vocabulary
(`pdca.toml:61`): the original repro — `./setup.py build` on a python2/3 system
— **cannot be run** on the target branch because there is no root `setup.py` to
execute. The bug's premise is gone, so the steps no longer reproduce.

## The original defect

Reported against v5.0.0: the repo-root `setup.py` lacked a
`#!/usr/bin/env python3` shebang, so `./setup.py build` on a system with both
python2 and python3 picked the wrong interpreter. It only worked when invoked
explicitly as `python3 setup.py build`. The fix the report implies is "add a
python3 shebang to the root `setup.py`."

## Evidence on the target branch (gramps-project/gramps @ maintenance/gramps61)

Verified against the pinned upstream worktree `gramps-6.1`, whose HEAD is
exactly `upstream/maintenance/gramps61`:

- `HEAD = cbe5699b2e81192cf11479d82620e1f331ca4b95`
- `upstream/maintenance/gramps61 = cbe5699b2e81192cf11479d82620e1f331ca4b95` — equal.

1. **No root `setup.py`.** `git ls-tree --name-only HEAD` at the repo root lists
   `pyproject.toml` (entry 34) but **no** `setup.py`. The only `*.py` at the root
   is `Gramps.py`. (`git ls-tree --name-only HEAD` → root has `Gramps.py`,
   `pyproject.toml`; `git ls-files '*setup.py'` returns only `aio/setup.py`.)

2. **`pyproject.toml` is the build entry.** `pyproject.toml:23-25` declares
   ```
   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"
   ```
   a PEP-517 build — there is no script for a shell to interpret, so no shebang
   to get wrong.

3. **The migration that removed the file.** Commit
   `6233d44744 "Convert to using a pyproject.toml based build system"` is the
   single commit that **deleted** the root `setup.py` (`--diff-filter=D -- setup.py`)
   **and added** `pyproject.toml` (`--diff-filter=A -- pyproject.toml`). The
   DistUtils path had already been removed earlier
   (`220f4161ba "Removed the Python DistUtils since we have a geps for it now."`).
   So the artifact the defect concerned was removed by the build-system migration,
   not by a shebang fix — making the report moot.

## The one `setup.py` that remains — and why it is not the defect

`aio/setup.py` still exists. It is **not** the artifact the bug is about:

- It is the all-in-one (Windows) cx_Freeze build script, not the project build
  entry — the project build is `pyproject.toml` / hatchling (point 2).
- Its header documents invocation as `python3 setup.py build_exe …` (explicitly
  via `python3`, run from inside `aio/`), not as a directly-executed
  `./setup.py build` from the repo root.
- `git show HEAD:aio/setup.py | head -3` shows it opens with a `"""` docstring,
  not a shebang — and it is not on the `./setup.py build` path the report used,
  so its lack of a shebang does not reproduce the reported failure.

I flag it here only so the reviewer/human is not surprised that the string
`setup.py` still appears in the tree; it does not revive the defect.

## Why no code change

The brief names an `Invariant to restore: n/a` — the artifact the defect
concerned (a directly-executed root `setup.py`) has already been removed by the
PEP-517 migration. There is no shebang to correct and nothing to restore. The
smallest correct action is to record the verification and resolve the item, not
to add code. Adding a shebang to `aio/setup.py` would be out of scope (the brief
excludes "any packaging change") and would not correspond to the reported bug.
