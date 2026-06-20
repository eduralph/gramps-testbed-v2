# Skip legacy-bsddb import tests when no backend is loadable

> Targets `maintenance/gramps61` (core test-infra fix; forward-merge to `master`).
> Reported upstream in gramps#2314. Links Mantis #13260 ([Linux Mint] "Exception:
> can't load database backend: 'bsddb'") as the underlying backend-unavailability
> issue. This PR fixes the *test-suite* symptom — backend-less installs reporting
> failures that should be skips — not the runtime install error itself, so it uses
> the non-closing `Bug #13260` trailer rather than `Fixes`.

## Root cause
On a default SQLite install where neither `berkeleydb` nor `bsddb3` is importable
(the common Linux case, e.g. Ubuntu 24.04), the five legacy-bsddb import tests fall
through to `make_database("bsddb")` at `gramps/plugins/test/imports_test.py:248`,
which raises `can't load database backend: 'bsddb'`; the catch-all at
`gramps/plugins/test/imports_test.py:266-275` reconverts that into an assertion
failure. The existing skip guard fires only under `win()`
(`gramps/plugins/test/imports_test.py:245-246`, added in
`29a0bedaa03eae52cb2e678f9a1a22121a0a7fc5`), so the backend-less Linux case reports
`FAILED` instead of skipping.

## Fix
Replace the Windows-only guard with a real backend-loadability probe, so the tests
skip whenever the backend is genuinely unavailable on the running platform — exactly
as they already do on Windows — and run unchanged wherever a backend is installed.

- New `gramps/plugins/test/_bsddb_avail.py:38-59` — `bsddb_backend_available()`,
  a test-harness helper whose probe order (try `berkeleydb`, then `bsddb3`,
  anything else → unavailable) mirrors the plugin loader at
  `gramps/plugins/db/bsddb/bsddb.py:32-35`.
- `gramps/plugins/test/imports_test.py:245-246` — the `dbid == "bsddb" and win()`
  guard becomes `dbid == "bsddb" and not bsddb_backend_available()`, with a skip
  message naming the real reason.
- `gramps/plugins/test/imports_test.py:59-65` — the helper is imported defensively
  (a `try/except ImportError` fallback returns `True`, i.e. do not skip), so a
  missing prober never masks a real load failure. No `win()` / OS check is
  reintroduced anywhere.

The `except SkipTest: raise` re-raise (`gramps/plugins/test/imports_test.py:263-265`,
also from `29a0bedaa03eae52cb2e678f9a1a22121a0a7fc5`) is what propagates the skip out
of `db_load`'s catch-all and is left untouched. The `while True` upgrade loop, the
catch-all exception block, the sqlite (`dbid != "bsddb"`) path, and
`gramps/plugins/db/bsddb/` are all unchanged.

## Verified against
- `gramps/plugins/test/imports_test.py:245-246` — confirmed the pre-fix guard was
  `win()`-only, so a non-Windows host with no backend never reached the skip.
- `gramps/plugins/test/imports_test.py:248` — the `make_database(dbid)` the
  "available" branch still falls through to; unchanged, so an installed backend runs
  the real import/compare exactly as before.
- `gramps/plugins/test/imports_test.py:266-275` — the catch-all that turned the
  loader exception into `AssertionError: Cannot open database … can't load database
  backend: 'bsddb'` pre-fix.
- `gramps/plugins/db/bsddb/bsddb.py:32-35` — the loader's `berkeleydb`→`bsddb3` probe
  the new helper mirrors, keeping "available" in lockstep with what
  `make_database("bsddb")` actually finds.

## Test
No new test file — the regression evidence is the existing
`gramps/plugins/test/imports_test.py` tests flipping from failures to skips. On a
backend-less Linux checkout (`GRAMPS_RESOURCES=. python3 -m unittest
gramps.plugins.test.imports_test`):

- representative `test_imp_5_1_2bsd_zip`: pre-fix `FAILED … can't load database
  backend: 'bsddb'` → post-fix `skipped 'bsddb backend not loadable on this platform
  (neither berkeleydb nor bsddb3 is installed)'`;
- whole suite: pre-fix `FAILED (failures=5, …)` → post-fix `OK (skipped=…)`.

The "backend installed" half is non-regressive by construction: the diff changes only
the guard condition and message, and on non-Windows the original `win()` guard was
already `False`, so the run-the-real-import path is byte-identical to today's
behaviour.
