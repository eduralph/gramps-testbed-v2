# Brief — issue 9491 / verify-setup-py-replaced-by-pyproject

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** verify-setup-py-replaced-by-pyproject
- **Defect:** Reported (v5.0.0): `setup.py` lacked a `#!/usr/bin/env python3` shebang, so
  running `./setup.py build` on a system with python2+python3 picked the wrong interpreter
  (worked only when invoked explicitly as `python3 setup.py build`).
- **Success criterion:** On `maintenance/gramps61`, confirm the premise no longer holds —
  the project no longer ships a `setup.py` to invoke directly; the build is defined by
  `pyproject.toml`. The shebang defect is therefore obsolete and the tracker item can be
  resolved. Verification, not a new fix (no patch).
- **Invariant to restore:** n/a — the artifact the defect concerned (a directly-executed
  `setup.py`) has been removed by the migration to a PEP-517 `pyproject.toml` build; there
  is no shebang to correct.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** low — verification only.
- **Scope:** verify `setup.py` is absent on `maintenance/gramps61` and that
  `pyproject.toml` is the build entry, making the shebang report moot. / out of scope: any
  packaging change, the contents of `pyproject.toml`, build documentation/wiki updates.
- **Repro instruction:** original repro — `./setup.py build` on a python2/3 system. On
  current `maintenance/gramps61` there is no `setup.py` at the repo root to run.
- **Test file:** none — verification of a removed file (no runtime behaviour to regress).
  Evidence is the absence of `setup.py` and presence of `pyproject.toml` at the tree root.
- **Citations expected:** cite the repo root listing of `maintenance/gramps61` (no
  `setup.py`; `pyproject.toml` present) as the evidence the defect is obsolete.
- **New/removed files:** none.
- **Prior-art check (triage cycles):** `git ls-tree maintenance/gramps61` root shows
  `pyproject.toml` and no `setup.py`. → the file the bug targets no longer exists; this
  bundle validates and resolves it as obsolete.
- **Mantis:** 9491
- **Disposition hint:** POSSIBLY-FIXED → verify first

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
