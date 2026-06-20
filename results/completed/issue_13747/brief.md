# Brief — issue 13747 / metadata-set-serialization-order

> CLOSE-disposition brief. The defect is real and still unfixed on the target branch, but a
> complete fix (with its regression test) is already authored, pushed, and submitted as an
> open upstream PR — so re-briefing would duplicate in-flight work. The bundle is carried
> straight to sign-off and discontinued (work is carried by the existing PR). Keep the
> `- **Label:** value` field shape (driver-parsed).

- **Slug:** metadata-set-serialization-order
- **Defect:** Saving/closing an unmodified family tree rewrites the on-disk sqlite file:
  custom-type metadata (e.g. `name_types`) is a Python `set`, and `JSONSerializer.object_to_metadata`
  serializes it with `list(value)` — the set's hash-iteration order, which varies per run —
  so the metadata rows change with no user edit.
- **Success criterion:** N/A (close) — no patch lands in this bundle. The fix's own success
  test (serialize a set-valued metadata twice → byte-stable output) ships with the existing
  upstream PR.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Scope:** none — fix already exists in-flight; do NOT re-author. / out of scope: the
  read-only-vs-read/write export-mode split (separate Mantis 13748); the "always re-saves
  metadata on close" behaviour (Mantis note 3) — only serialization determinism is in scope,
  and it is already addressed by the existing PR.
- **Repro instruction:** import the attached two-person tree with custom name types; close
  gramps; back up sqlite.db; `gramps --format gramps-xml -O <db> -e /tmp/t.gramps`; diff the
  on-disk sqlite (the `name_types` metadata row's order flips).
- **Prior-art check (triage cycles):** searched by file path `gramps/gen/lib/serialize.py`.
  Still unfixed on `upstream/maintenance/gramps61` and `upstream/master` (`object_to_metadata`
  at serialize.py:168-179 still does `list(value)`). However a complete fix is **already
  submitted** as **open upstream PR 2340** ("Sort set metadata so unchanged databases are not
  rewritten", branch fix/bug-13747-metadata-set-order, commit `48b8294aa5`, "Fixes #13747"),
  which sorts the set before serializing and ships the regression test in
  `gramps/gen/lib/test/serialize_test.py`. Re-doing it here would duplicate that PR.
- **Mantis:** 13747
- **Disposition hint:** likely-close — superseded by open upstream PR 2340; the fix and its
  test are carried there, so this bundle has no separate work to land.

## STOP discipline

Draft only until Check sign-off. No patch, no PR — the fix is carried by the existing PR.
