# Build notes — addon-tests-init-py-gramps60 (addons-source #43)

> Withheld from the reviewer. Rationale, what I verified, what I ruled out.

## What the brief asks for

Restore a **structural-parity invariant** on `addons-source @ maintenance/gramps60`:
every addon `tests/` directory that holds `test_*.py` must also carry a
`tests/__init__.py` package marker (parity with `maintenance/gramps61`, which is
23/23). The brief frames this as an **Invariant to restore** (Tier C internal
invariant), so per `docs/principles.md` §1.2/§2 the target is the *smallest change
that restores the invariant*, not the smallest diff — and the invariant is stated
over the whole category (every gramps60 addon test dir), not one addon.

## Diagnosis — verified, not recalled

Repro against the **upstream** target branch (`upstream/maintenance/gramps60`, the
real contribution target per `docs/INTEGRATION.md` §2, not the fork's tracking copy),
with `LC_ALL=C` so `comm` sees a stable sort:

```
git ls-files '*/tests/test_*.py' | sed -E 's#/tests/.*#/tests/#'   | sort -u   # 22 dirs
git ls-files '*/tests/__init__.py' | sed 's#__init__.py$##'         | sort -u   # 18 markers
comm -23 …                                                                       # the gap
```

gramps60: **22 test dirs / 18 markers** → exactly four missing, matching the brief:

- `CalculateEstimatedDates/tests/`
- `DataEntryGramplet/tests/`
- `Form/tests/`
- `TMGimporter/tests/`

gramps61 reference: **23 test dirs / 23 markers** — full parity, nothing to do there
(and the brief says do NOT touch gramps61). `FRWebConnectPack/tests/` already carries
`__init__.py` on gramps60, so it is correctly *not* in the gap (an earlier non-C-locale
`comm` falsely listed it — a sort-order artefact, ruled out by re-running under
`LC_ALL=C`).

The four gramps61 markers are all **0 bytes** (verified via `git show … | wc -c`), so
the parity change is four empty files.

## The change

`patch.diff` adds four empty `tests/__init__.py` files on `maintenance/gramps60`:

- `CalculateEstimatedDates/tests/__init__.py`
- `DataEntryGramplet/tests/__init__.py`
- `Form/tests/__init__.py`
- `TMGimporter/tests/__init__.py`

Generated with `git diff --cached` from a scratch worktree checked out at
`upstream/maintenance/gramps60` (created/removed via `git worktree`, since the pinned
`addons-source-6.0` validation worktree is outside this session's writable roots).
After the change gramps60 is **22/22** — full parity with the gramps61 reference.

## Red → green proof

This is an **invariant-restoration**, so the red→green gate is the invariant check
itself (the brief's repro), not a new `test_*.py` — the brief is explicit: *"no new
`test_*.py` ships … Verify by discovery, not C4-verify."* I deliberately ship **no
test file** (adding one would also violate the brief's "out of scope: any test-logic
… change").

- **RED (pre-fix, clean worktree):** `comm -23` lists the four dirs; markers 18/22.
- **GREEN (post-fix, patch applied):** `comm -23` is empty; markers 22/22.

Both states captured during the build.

## Why C4-verify / `run-verify.sh` is NOT the gate here (brief confirmed empirically)

`run-verify.sh` (the addon matrix) applies the patch to **both** cores and needs a
shipped `test_*.py`. I confirmed `git apply --check`:

- on `addons-source-6.0` (gramps60): **applies cleanly**;
- on `addons-source-6.1` (gramps61): **fails** — `… already exists in working
  directory` for all four (gramps61 already conforms).

So the 6.1 leg of C4 would fail to apply regardless of the fix. The correct gate is
**T3-addon-unit-60** (gramps60 leg only), exactly as the brief states.

## A finding the human should see (I did not overclaim a discovery-skip)

The brief says the suites are *"red/skipped pre-fix → discovered/green post-fix."* I
tested this directly. Under Python 3 **PEP 420 namespace packages**, the runner's
dotted-path discovery (`<Addon>.tests.<module>`, run with `cwd=addons-source/`)
already imports and runs the suites **without** `__init__.py`: I ran all seven
modules across the four addons and got **244 tests, OK** in *both* the pre-fix
(markers removed) and post-fix (markers present) states. So the "skipped pre-fix"
phrasing does not literally reproduce as a discovery-skip in this harness (dotted
names, one process per addon — no basename-collision path).

What the markers genuinely change:
1. The **structural-parity invariant** (the brief's primary clause + Invariant) — 18→22, which *is* false→true.
2. **Robustness** of that discovery: a namespace package silently re-resolves if any
   like-named dir appears earlier on `sys.path`; a real package (`__init__.py`) pins
   the import. This is the "can silently skip" risk the brief names — now removed.

I have written the rationale around the verifiable invariant rather than asserting a
discovery-skip I could not reproduce. The Success criterion's second clause
("discovered and run, not skipped") holds post-fix (244 tests, OK) — and held
pre-fix too, so the fix does not regress it.

## Alternatives ruled out

- **Ship a structural gate test** (`tests/test_addon_test_packaging.py` asserting the
  invariant): rejected — the brief explicitly ships no new test and de-scopes
  test-logic changes; a `tests/test_*.py` is itself a `test_*.py`. The invariant's
  red→green is the repro command, which is sufficient for an invariant-restoration.
- **Non-empty `__init__.py`** (e.g. moving `gi.require_version` pins in): rejected —
  that is addons-source #38, explicitly out of scope; the gramps61 markers are empty,
  so parity = empty files.
- **Touch gramps61**: rejected — already 23/23; the maintainer's cherry-pick-forward
  would no-op, and `git apply` proves the patch is gramps60-only.

## Formatting / commit-readiness

`black --check` on the four empty files: clean (no change). No `pyproject.toml` /
`.pre-commit-config` / `setup.cfg` in `addons-source` root, so no formatter hook
beyond the trivial. Patch is committable to `maintenance/gramps60`.

## Citations (paths created on `maintenance/gramps60`)

- `CalculateEstimatedDates/tests/__init__.py` (new, empty)
- `DataEntryGramplet/tests/__init__.py` (new, empty)
- `Form/tests/__init__.py` (new, empty)
- `TMGimporter/tests/__init__.py` (new, empty)

Reference (unchanged): `maintenance/gramps61` already carries all four as empty files.
