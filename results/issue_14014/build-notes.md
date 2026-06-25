# Build notes — issue 14014 / importxml-compound-date-empty-bound

## Disposition: verify-first (fix already upstream)

The brief is explicit: this is a **verification, not a re-fix**. The crash —
`IndexError: string index out of range` at
`gramps/plugins/importer/importxml.py` `start_compound_date()` — was already
fixed upstream by commit **1c411ea3ed** ("Catch IndexError in importxml"),
which guards each bound before indexing `[0]`.

I confirmed the guard is present on the contribution target
(`maintenance/gramps61`, worktree `../gramps-6.1`):

- `gramps/plugins/importer/importxml.py:2553` — `if start and start[0] == "-":`
- `gramps/plugins/importer/importxml.py:2573` — `if stop and stop[0] == "-":`
- `gramps/plugins/importer/importxml.py:2658` — `if val and val[0] == "-":`

(`start`/`stop` read at `importxml.py:2549-2550`; the `start_daterange` /
`start_datespan` entry points are `importxml.py:2526` / `:2529`.)

The unguarded form is still visible in the system-installed copy used as the
pre-fix oracle below: `/usr/lib/python3/dist-packages/gramps/.../importxml.py:2573`
is `if stop[0] == "-":`.

## What ships

Because the production fix is already in the tree there is no production change
to make — only the regression test the brief names, plus its POTFILES
registration:

1. `gramps/plugins/importer/test/importxml_daterange_test.py` (new) — the
   regression test.
2. `po/POTFILES.skip` — registers the new test (no translatable strings), per
   doc 16 §Adding and removing Python files. Inserted in the existing
   `plugins/importer/test` block in alphabetical order (after
   `importvcard_test.py`).

## Test design — exercises the real production path, import-light

The test drives `gramps.gen.db.utils.import_as_dict` (the same routine the
existing `gramps/plugins/test/imports_test.py` and
`importgedcom_ambiguous_date_test.py` use). `import_as_dict` builds an
in-memory sqlite db and runs the *real* importer, so the test routes through
production `start_compound_date` — it does not re-implement or mirror it.

`importxml.py` imports only `gramps.gen.*` (no `gi` / `gramps.gui`), and
`import_as_dict` uses an in-memory db, so the test is headless-safe: it runs
under plain `python3 -m unittest` with no display / D-Bus / AT-SPI (the C4
headless runner). Confirmed: it loads and runs without a display.

Three cases:

- `test_daterange_empty_stop_imports_as_open_ended_range` — the **reported**
  case `<daterange start="1911-09-01" stop=""/>`. Asserts import completes and
  the date is the corresponding open-ended `MOD_RANGE`: begin bound preserved
  `(1911, 9, 1)`, stop bound open (`get_stop_year() == 0`), not text-only
  (`get_text() == ""`). This is the brief's Success criterion verbatim.
- `test_datespan_empty_stop_imports_as_open_ended_span` — the `<datespan>`
  sibling; same open-ended-span outcome.
- `test_daterange_empty_start_imports_without_indexerror` —
  `<daterange start="" stop="1900"/>` (the brief's "empty start or stop"). The
  pre-fix code raised `IndexError` at `start[0]` here too. Post-fix the import
  completes; Gramps' data model rejects an open *lower* bound (`Date.set`
  raises `DateError`), so the importer's existing `except DateError` path
  degrades it to a text-only date preserving the XML (`MOD_TEXTONLY`, text
  contains `start=""`). That graceful degrade still satisfies "completes
  without IndexError" — I assert the actual observed behaviour rather than
  inventing an open-ended-range outcome the model does not produce.

## Red→green evidence

C4 `run-verify` cannot do its automatic revert mechanic here: the patch is
**test-only** (no production file to revert), so `run-verify.sh` emits
`PDCA-UNVERIFIABLE` (exit 77) → §6 NEEDS-HUMAN. This is the expected and
documented outcome for a verify-first bundle (brief, and `run-verify.sh:162`).

I demonstrated the red→green contract manually instead, using the
system-installed (pre-fix) gramps as the unguarded oracle:

- **GREEN** on the fixed target (`../gramps-6.1` on `maintenance/gramps61`):
  all 3 tests pass (`Ran 3 tests ... OK`).
- **RED** on the unfixed code (`/usr/lib/python3/dist-packages/gramps`, which
  still has `if stop[0] == "-":`): all 3 tests error with
  `IndexError: string index out of range` at `importxml.py:2573` / `:2553` —
  exactly the reported traceback. (`Ran 3 tests ... FAILED (errors=3)`.)

So the test genuinely catches the bug the upstream fix resolves.

## Alternatives considered

- **No new test, accept on the merged commit alone.** Rejected: the brief
  requires the regression test to ship and pass on the current target, and a
  regression test pins the behaviour against future reintroduction (the bug
  was itself introduced by a recent change, 634e5ccc24).
- **Assert an open-ended range for the empty-*start* case.** Rejected: empirically
  the importer stores that as a text-only date (model rejects an open lower
  bound). Asserting a range would be a false expectation that fails on the
  fixed tree. I assert what production actually does.

## Commit-readiness

`black` run over the new test file; `black --check` reports it unchanged.
POTFILES.skip is not Python (no formatter). The worktree carries unrelated
pre-existing leftover edits (`_date_de.py`, `date_de_test.py`) from a prior
lane run; `patch.diff` was generated scoped to only the two files this bundle
changes, so it excludes that noise.
